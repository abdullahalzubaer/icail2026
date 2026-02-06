# main.py
import argparse
import gc
import hashlib
import json
import math
import os
import random
import re
import shutil
import sys
import time
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml
from dotenv import load_dotenv
from huggingface_hub import login
from tenacity import RetryCallState, retry, stop_after_attempt, wait_random_exponential

# >>> Load HF token from .env >>>
load_dotenv(dotenv_path='/root/work/configs/.env') 
hf_token = os.getenv("HUGGINGNFACE_TOKEN")
if hf_token:
    login(token=hf_token)
    print("[hf-login] Successfully logged in to Hugging Face Hub.")
else:
    raise EnvironmentError("[Error] HF_TOKEN environment variable is not set.")
# <<< Load HF token from .env <<<


# for excel export: remove illegal control chars
from openpyxl.utils.exceptions import IllegalCharacterError
ILLEGAL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
def clean_cell(x):
    return ILLEGAL.sub("", x) if isinstance(x, str) else x

ERROR_TOKEN = "ERROR_COULD_NOT_EXTRACT"


def clear_huggingface_cache():
    """
    Clears the HuggingFace cache directory (~/.cache/huggingface).
    Equivalent to: rm -rf ~/.cache/huggingface/*
    """
    cache_dir = Path.home() / ".cache" / "huggingface"
    if cache_dir.exists():
        try:
            for item in cache_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            print(f"[cache] Successfully cleared HuggingFace cache: {cache_dir}")
        except Exception as e:
            print(f"[cache] Warning: Failed to clear HuggingFace cache: {e}")
    else:
        print(f"[cache] HuggingFace cache directory does not exist: {cache_dir}")


# --- add near other helpers ---
def _hp_vllm(cfg: dict) -> dict:
    """Return the vLLM hyperparameter dict."""
    return (cfg.get("model_hyperparameters_vllm") or {})


def exp_wait_seconds(attempt: int, *, min_s: float = 1.0, max_s: float = 180.0, base: float = 2.0) -> float:
    """
    attempt: 1-based retry number (1,2,3,...)
    Returns a sleep time using 'full jitter':
      sleep ∈ [min_s, min(max_s, base**attempt)].
    """
    upper = min(max_s, base ** attempt)
    lower = min_s
    if upper < lower:
        return lower
    return random.uniform(lower, upper)


# ---------------------------
# Config loading
# ---------------------------
def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_global_max_tokens(cfg):
    # default 8192, allow top-level override
    return int(cfg.get("max_tokens", 8192))

def get_model_max_tokens(cfg, model):
    hp = _hp_vllm(cfg).get(model, {}) or {}           # CHANGED
    # hp = cfg.get("model_hyperparameters", {}).get(model, {}) or {}
    if "max_tokens" in hp and hp["max_tokens"] is not None:
        return int(hp["max_tokens"])
    return None

def get_effective_max_tokens(cfg, model):
    per_model = get_model_max_tokens(cfg, model)
    return per_model if per_model is not None else get_global_max_tokens(cfg)

def get_system_message_for_prompt(cfg, prompt_col):
    # Behavior per your spec:
    # - If provide_system_message: true -> prefer per-prompt; fallback to global; else none
    # - If provide_system_message: false -> no system message at all
    if not cfg.get("provide_system_message", False):
        return ""
    sys_msgs = cfg.get("system_messages", {}) or {}
    if prompt_col in sys_msgs and sys_msgs[prompt_col]:
        return sys_msgs[prompt_col]
    return cfg.get("system_message", "") or ""

def top_level_seed(cfg):
    return cfg.get("seed")

def set_global_seed(seed):
    if seed is None:
        return
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except Exception:
        pass

# ---------------------------
# Column naming / hashing
# ---------------------------
def sanitize(s):
    import re
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", s).strip("-").lower()

def short_hash_from_kwargs(kwargs, length=8):
    # Only hash actual kwargs sent to SamplingParams (exclude max_tokens)
    payload = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]

def make_col_base(prompt_col, model_name, iter_n, hp_hash):
    p = sanitize(prompt_col)
    m = sanitize(model_name.split("/")[-1])
    return f"vllm_{p}__{m}__i{iter_n}__h{hp_hash}"

def make_col_names(prompt_col, model_name, iter_n, hp_hash):
    base = make_col_base(prompt_col, model_name, iter_n, hp_hash)
    return {
        "out":    f"{base}__output",
        "resp":   f"{base}__complete_response",
        "extracted_element":  f"{base}__extracted_element",
        "meta":   f"{base}__metadata",
        "prompt": f"{base}__prompt_sent",  # only for first iteration
    }

# ---------------------------
# Decoding policy → SamplingParams kwargs
# ---------------------------
def build_sampling_kwargs(cfg, model):
    
    """
    Returns (sampling_kwargs_for_SamplingParams, effective_knobs_for_hash)
    - Excludes max_tokens from the hash basis.
    - Honors decoding_policy: default | greedy | custom_sampling
    - 'default': pass nothing except max_tokens
    - 'greedy': pass only temperature=0.0 (+ max_tokens)
    - 'custom_sampling': pass only provided sampling keys (others remain defaults) (+ max_tokens)
    - Includes reasoning_effort in hash if set (for consistency with LiteLLM, affects output on API models).
    """

    hp = _hp_vllm(cfg).get(model, {}) or {}
    policy = (hp.get("decoding_policy", "default") or "default").lower()

    # Resolve max_tokens separately (global default 8192, per-model override)
    max_tokens = get_effective_max_tokens(cfg, model)

    sampling_kwargs = {"max_tokens": max_tokens}
    hash_basis = {}  # only keys that actually affect decoding beyond max_tokens

    # Include reasoning_effort in hash if set (for consistency with LiteLLM script)
    reasoning_effort = hp.get("reasoning_effort", None)
    if reasoning_effort is not None:
        hash_basis["reasoning_effort"] = reasoning_effort

    if policy == "default":
        return sampling_kwargs, hash_basis # Return only max_tokens

    elif policy == "greedy":
        sampling_kwargs["temperature"] = 0.0
        hash_basis["temperature"] = 0.0

        return sampling_kwargs, hash_basis # Return max_tokens + temperature=0.0

    elif policy == "custom_sampling":
        for k in ["temperature", "top_p", "top_k", "min_p"]: # these are just examples, it does not stop you from adding in extra_sampliing as we have extra_sampling below to pass through any other keys.
            if k in hp and hp[k] is not None:
                sampling_kwargs[k] = hp[k]
                hash_basis[k] = hp[k]
                
        # Optional pass-through for any extra sampling kwargs
        extra = hp.get("extra_sampling", {})
        if isinstance(extra, dict):
            for k, v in extra.items():
                sampling_kwargs[k] = v
                hash_basis[k] = v
                
        return sampling_kwargs, hash_basis # Return max_tokens + provided sampling keys
    
    else:
        raise ValueError(f"Unknown decoding_policy '{policy}' for model '{model}'")



    

# ---------------------------
# LLM init (per model)
# ---------------------------
def init_llm_for_model(model_name, cfg):
    
    from vllm import LLM
    
    hp = _hp_vllm(cfg).get(model_name, {}) or {}
    llm_init = hp.get("llm_init", {}) or {}

    llm_kwargs = {"model": model_name}

    # Optional: gpu_memory_utilization
    if "gpu_memory_utilization" in llm_init and llm_init["gpu_memory_utilization"] is not None:
        llm_kwargs["gpu_memory_utilization"] = float(llm_init["gpu_memory_utilization"])

    # Optional: tensor_parallel_size (pass through only if provided)
    if "tensor_parallel_size" in llm_init and llm_init["tensor_parallel_size"] is not None:
        llm_kwargs["tensor_parallel_size"] = int(llm_init["tensor_parallel_size"])

    # Optional extra LLM init kwargs
    extra_llm = hp.get("extra_llm", {})
    if isinstance(extra_llm, dict):
        llm_kwargs.update(extra_llm)

    return LLM(**llm_kwargs)

# ---------------------------
# Build conversations (exact payload we send)
# ---------------------------
def build_conversations(rows,
                        prompt_col,
                        system_msg):
    
    convs = []
    
    for _, r in rows.iterrows():
        u = "" if pd.isna(r[prompt_col]) else str(r[prompt_col])
        convo = []
        if system_msg:
            convo.append({"role": "system", "content": system_msg})
        convo.append({"role": "user", "content": u})
        convs.append(convo)
    return convs

def first_text(vllm_output) -> str:
    try:
        return vllm_output.outputs[0].text if getattr(vllm_output, "outputs", None) else ""
    except Exception:
        return ""

def serialize_vllm_output(o):
    """
    JSON-friendly snapshot of a single vLLM request output.
    Includes a robust 'repr' fallback so "whatever the model replied with" is retained.
    """
    result = {}
    try:
        result["request_id"] = getattr(o, "request_id", None)
        outs = []
        for j, ch in enumerate(getattr(o, "outputs", []) or []):
            outs.append({
                "index": j,
                "text": getattr(ch, "text", None),
                "finish_reason": getattr(ch, "finish_reason", None),
            })
        result["outputs"] = outs
        # Light-weight extras (lengths only to stay CSV-friendly)
        pti = getattr(o, "prompt_token_ids", None)
        result["prompt_token_ids_len"] = len(pti) if isinstance(pti, (list, tuple)) else None
        result["output_token_ids_len"] = [
            len(getattr(ch, "token_ids", []) or []) for ch in (getattr(o, "outputs", []) or [])
        ]
        # Fallback full repr (string) to preserve any additional info
        result["repr"] = repr(o)
    except Exception as e:
        result = {"repr": repr(o), "error_serializing": str(e)}
    return result

# ---------------------------
# Tenacity hooks
# ---------------------------
def _before_retry(rs: RetryCallState):
    print(f"[retry] attempt #{rs.attempt_number} after error: {rs.outcome.exception() if rs.outcome else 'unknown'}")

def _on_final_failure(rs: RetryCallState):
    print(f"[retry] final failure after {rs.attempt_number} attempts.")
    return None

# A single batched chat call with retry (used for the *subset of failing rows*)
@retry(
    wait=wait_random_exponential(min=1, max=180),
    stop=stop_after_attempt(10),
    before_sleep=_before_retry,
    retry_error_callback=_on_final_failure,
    reraise=True,
)
def chat_batch(llm, conversations, sampling_params, chat_template=None):
    
    chat_kwargs = {
        "sampling_params": sampling_params,
        "use_tqdm": True,
        "add_generation_prompt": True,
    }
    
    if chat_template is not None:
        chat_kwargs["chat_template"] = chat_template
    
    return llm.chat(conversations, **chat_kwargs)
    # "add_generation_prompt": Read here: https://github.com/vllm-project/vllm/blob/e5ef4dfc11abfc44494963b85ced1c79d1d5efea/vllm/entrypoints/llm.py#L925, this is the same as here in huggingface: https://huggingface.co/docs/transformers/v4.57.1/en/chat_templating#addgenerationprompt
    
    
# ---------------------------
# Core per-model runner (child mode)
# ---------------------------
def run_single_model(cfg_path, model_name):
    print(f"[start] vLLM inference for model: {model_name}")
    cfg = load_yaml(cfg_path)

    # seed (top-level)
    seed = top_level_seed(cfg)
    set_global_seed(seed)

    # load df
    df = pd.read_csv(cfg["primary_file"])
    
    print(f"\n{'='*60}")
    print(f"[info] CSV file: {cfg['primary_file']}")
    print(f"[info] Total rows: {len(df)}")
    print(f"[info] Model to run: {model_name}")
    print(f"[info] Prompts to process: {cfg['prompt_to_score_list']}")
    print(f"{'='*60}\n")

    # test subset
    if cfg.get("for_testing_purpose", False):
        pct = max(1, min(100, int(cfg.get("working_with_n_percentage_of_data", 10))))
        n = math.ceil(len(df) * (pct / 100.0))
        df = df.sample(n=n, random_state=42).reset_index(drop=True)
        print(f"[info] Testing mode: using {pct}% -> {n} rows.")

    

    upfront_check = bool(cfg.get("upfront_check_extraction", False))

    def _load_extraction_callable(cfg: Dict[str, Any]):
        ex_cfg = (cfg.get("extraction") or {})
        if not ex_cfg.get("enabled", False):
            return None, None
        dotted = ex_cfg.get("function")
        if not dotted:
            raise RuntimeError("extraction.enabled=true but no extraction.function set in config.")
        mod_name, func_name = dotted.rsplit(".", 1)
        fn = getattr(import_module(mod_name), func_name)
        if not callable(fn):
            raise TypeError(f"extraction.function '{dotted}' is not callable")
        return fn, dotted

    extraction_fn, extraction_fn_path = _load_extraction_callable(cfg)

    def _is_valid_and_value(text: str):
        if not extraction_fn:
            return True, None  # validation off
        try:
            val = extraction_fn(text or "")
        except Exception:
            return False, None
        if val is None or val == ERROR_TOKEN:
            return False, None
        return True, val



    # vLLM objects (init inside child)
    from vllm import SamplingParams
    llm = init_llm_for_model(model_name, cfg)

    # sampling kwargs & hash (exclude max_tokens from hash_basis)
    sampling_kwargs, hash_basis = build_sampling_kwargs(cfg, model_name)
    hp_hash = short_hash_from_kwargs(hash_basis)

    # Get optional chat_template from config
    hp = _hp_vllm(cfg).get(model_name, {}) or {}
    chat_template = hp.get("chat_template", None)

    # iterations
    iters = int(cfg["iteration"]["iterations"])
    start_it = int(cfg["iteration"]["start_iteration"])
    iter_values = list(range(start_it, start_it + iters))

    # prompts list
    prompt_cols = cfg["prompt_to_score_list"]

    # overwrite behavior
    overwrite = bool(cfg["overwrite_existing_output_columns"])

    # prepare sampling params factory (max_tokens can differ per model already resolved)
    def make_sampling() -> SamplingParams:
        return SamplingParams(**sampling_kwargs)


    # process each prompt column
    for prompt_col in prompt_cols:
        if prompt_col not in df.columns:
            raise KeyError(f"Prompt column missing: {prompt_col}")

        # rows with non-null prompt
        idx_all = df.index[df[prompt_col].notna()].tolist()
        if not idx_all:
            print(f"[warn] No rows to process for {prompt_col}")
            continue

        # per-prompt system message (per your spec)
        # If provide_system_message: true -> prefer per-prompt; fallback to global; else none!
        sys_msg = get_system_message_for_prompt(cfg, prompt_col)
        # Until now we have the prompt column and system message (if available) ready for this prompt_col.
        for iter_n in iter_values:
            # column names for this combo
            cols = make_col_names(prompt_col, model_name, iter_n, hp_hash)
            targets = [cols["out"], cols["resp"], cols["meta"]]
            if upfront_check and extraction_fn is not None:
                targets.append(cols["extracted_element"])
            if iter_n == 1:
                targets.append(cols["prompt"])
                
            # overwrite checks
            existing = [c for c in targets if c in df.columns]
            if existing and not overwrite:
                raise RuntimeError(f"Columns already exist (overwrite=False): {existing}")

            # Make a working view for this iteration
            work_idx = idx_all[:]  # all candidate rows for this iteration

            # First pass on all
            rows = df.loc[work_idx, [prompt_col]].copy()
            convs = build_conversations(rows, prompt_col, sys_msg)
            outs = chat_batch(llm, convs, make_sampling(), chat_template=chat_template) # Complete response from vLLM
            texts = [first_text(o) for o in outs] # Only output string from the model.

            # Attach first results (out=text; resp=JSON serialized vLLM output)
            for row_i, o, text, convo in zip(work_idx, outs, texts, convs):
                df.at[row_i, cols["out"]] = text
                df.at[row_i, cols["resp"]] = json.dumps(serialize_vllm_output(o), ensure_ascii=False)

            # Validation & row-level retries ONLY if upfront_check and extraction_fn is set.
            retry_round = 0
            max_retries = 20
            if upfront_check and extraction_fn is not None:
                valid_mask = [_is_valid_and_value(t)[0] for t in texts]
                while True:
                    failing_idx = [row_i for row_i, ok in zip(work_idx, valid_mask) if not ok]
                    if not failing_idx or retry_round >= max_retries:
                        break
                    retry_round += 1
                    
                    # --- Exponential backoff with jitter ---
                    # Manual pause before each retry batch.
                    # Reason of manual pause:  with llm.chat(conversations, …) the whole batch is one synchronous call. I can’t intervene “mid-batch” (e.g., pause, cancel, change params, validate row-by-row) until the call returns. I used to this before when I was doing per-row calls. But now, with batch calls, I can only do it between calls.
                    
                    # sleep_s = exp_wait_seconds(retry_round, min_s=1.0, max_s=180.0, base=2.0)
                    sleep_s = 2
                    print(f"[retry] round={retry_round} sleeping {sleep_s:.1f}s before retrying {len(failing_idx)} rows")
                    time.sleep(sleep_s)

                    rows_retry = df.loc[failing_idx, [prompt_col]].copy()
                    convs_retry = build_conversations(rows_retry, prompt_col, sys_msg)
                    retry_outs = chat_batch(llm, convs_retry, make_sampling(), chat_template=chat_template)
                    retry_texts = [first_text(o) for o in retry_outs]

                    for row_i, o_new, t_new in zip(failing_idx, retry_outs, retry_texts):
                        df.at[row_i, cols["out"]] = t_new
                        df.at[row_i, cols["resp"]] = json.dumps(serialize_vllm_output(o_new), ensure_ascii=False)

                    valid_mask = [_is_valid_and_value(df.at[row_i, cols["out"]])[0] for row_i in work_idx]

                # Log if max retries exhausted with still-failing rows
                final_failing_idx = [row_i for row_i, ok in zip(work_idx, valid_mask) if not ok]
                if final_failing_idx:
                    print(f"\n[WARNING] Max retries ({max_retries}) exhausted for model={model_name} prompt={prompt_col} iter={iter_n}")
                    print(f"[WARNING] {len(final_failing_idx)} rows still have invalid/non-extractable output:")
                    for row_i in final_failing_idx:
                        raw_out = df.at[row_i, cols["out"]]
                        preview = raw_out
                        # preview = (raw_out[:100] + "...") if len(str(raw_out)) > 100 else raw_out
                        print(f"  - Row index {row_i}: {preview!r}")
                    print(f"[WARNING] These rows will have None in '{cols['extracted_element']}' column.\n")

            if upfront_check and extraction_fn is not None:
                for row_i in work_idx:
                    ok, val = _is_valid_and_value(df.at[row_i, cols["out"]])
                    df.at[row_i, cols["extracted_element"]] = (val if ok else None)


            # meta + prompt (for prompt its only first iteration)
            meta_payload = {
                "model": model_name,
                "prompt_col": prompt_col,
                "iteration": iter_n,
                "dataset": cfg["primary_file"],
                "decoding_policy": (_hp_vllm(cfg).get(model_name, {}) or {}).get("decoding_policy", "default"),
                "sampling_kwargs_effective": hash_basis,  # only knobs actually passed (excl. max_tokens)
                "max_tokens": sampling_kwargs.get("max_tokens"),
                "gpu_memory_utilization": (_hp_vllm(cfg).get(model_name, {}).get("llm_init", {}) or {}).get("gpu_memory_utilization"),
                "tensor_parallel_size": (_hp_vllm(cfg).get(model_name, {}).get("llm_init", {}) or {}).get("tensor_parallel_size"),
                "seed": seed,
                "num_retries": 30,
                "extraction_enabled": bool(cfg.get("extraction", {}).get("enabled", False)),
                "extraction_function": extraction_fn_path,
                "upfront_check_extraction": upfront_check,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            meta_json = json.dumps(meta_payload, ensure_ascii=False)
            df.loc[work_idx, cols["meta"]] = meta_json

            if iter_n == 1:
                # Save the exact prompt payload we sent for first iteration only.
                # Save the exact chat payload (JSON list of {role, content})
                # Store per-row conversations as JSON strings
                payloads = [json.dumps(c, ensure_ascii=False) for c in convs]
                df.loc[work_idx, cols["prompt"]] = payloads

            print(f"[done] model={model_name} prompt={prompt_col} iter={iter_n} rows={len(work_idx)}")

    # save back to the same CSV
    df.to_csv(cfg["primary_file"], index=False)
    
    # sanitize *only* for Excel export
    df_excel = df.map(clean_cell)
    df_excel.to_excel(cfg["primary_file"].replace(".csv", ".xlsx"), index=False, engine="xlsxwriter")

    print(f"\n[saved] {cfg['primary_file']}")
    print(f"[saved] {cfg['primary_file'].replace('.csv', '.xlsx')}\n")
    

    # explicit cleanup
    try:
        del llm
    except Exception:
        pass
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass

# ---------------------------
# Parent orchestrator (spawns per-model subprocesses)
# ---------------------------
def run_parent(cfg_path: str):
    # Load config ONCE at parent startup
    cfg = load_yaml(cfg_path)
    models = cfg["model_list_vllm"]
    
    # Check if cache clearing is enabled (default: True)
    clear_cache = cfg.get("clear_hf_cache_after_each_model", True)

    # Print run summary
    print(f"\n{'='*60}")
    print(f"[vLLM Inference Script]")
    print(f"{'='*60}")
    print(f"[info] Config file: {cfg_path}")
    print(f"[info] CSV file: {cfg['primary_file']}")
    print(f"[info] Prompts to process: {cfg['prompt_to_score_list']}")
    print(f"[info] Models to run: {models}")
    print(f"[info] Clear HF cache after each model: {clear_cache}")
    print(f"{'='*60}\n")

    # Parent does *not* import vllm; spawns per model
    # Note: Subprocesses must read config from path (can't share memory)
    for m in models:
        print(f"[spawn] running model: {m}")
        # Inherit current env (so CUDA_VISIBLE_DEVICES applies)
        cmd = [sys.executable, os.path.abspath(__file__), "--config", cfg_path, "--only_model", m]
        rc = os.spawnve(os.P_WAIT, sys.executable, cmd, os.environ.copy())
        if rc != 0:
            print(f"[warn] Child for model '{m}' failed with exit code {rc}; continuing...")
        
        # Clear HuggingFace cache after each model (if enabled)
        if clear_cache:
            print(f"[cache] Clearing HuggingFace cache after model: {m}")
            clear_huggingface_cache()


# ---------------------------
# CLI
# ---------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--only_model", default=None, help="If set, run only this model (child mode)")
    args = parser.parse_args()

    if args.only_model:
        # Child mode: must read config from path (subprocess can't share memory)
        run_single_model(args.config, args.only_model)
    else:
        # Parent mode: reads config once, spawns children
        run_parent(args.config)

if __name__ == "__main__":
    main()
