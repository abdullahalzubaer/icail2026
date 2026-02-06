#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import gc
import hashlib
import json
import math
import os
import random
import re
import sys
import time
from importlib import import_module
from typing import Any, Dict, List, Optional, Tuple

import litellm
import pandas as pd
import yaml
from dotenv import load_dotenv
from tqdm.auto import tqdm

litellm.suppress_debug_info = True
from litellm import completion, completion_cost, stream_chunk_builder
from tenacity import RetryCallState, retry, stop_after_attempt, wait_random_exponential

from openpyxl.utils.exceptions import IllegalCharacterError
# for excel export: remove illegal control chars
ILLEGAL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
def clean_cell(x):
    return ILLEGAL.sub("", x) if isinstance(x, str) else x

# =========================
# Defaults / ENV wiring
# =========================

load_dotenv("/root/work/configs/.env")


# Per your requirement (read-only mappings for defaults)
os.environ["OPENAI_API_KEY"]     = os.getenv("YOUR_OPENAI_API_KEY", "")
os.environ["OPENROUTER_API_KEY"] = os.getenv("YOUR_OPENROUTER_API_KEY", "")

# Column prefix for this script (set to "litellm_" to distinguish from vLLM).
COL_PREFIX = os.getenv("LITELLM_COL_PREFIX", "litellm_")
ERROR_TOKEN = "ERROR_COULD_NOT_EXTRACT" # special token to indicate extraction failure

# --- add near other helpers ---
def _hp_litellm(cfg):
    """Return the LiteLLM hyperparameter dict."""
    return (cfg.get("model_hyperparameters_litellm") or {})

# =========================
# Helpers
# =========================


def _before_retry(retry_state):
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    print(
        f"[tenacity] retrying LiteLLM call: attempt={retry_state.attempt_number}, error={exc}"
    )


def _on_final_failure(retry_state):
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    print(
        f"[tenacity] giving up on LiteLLM call after {retry_state.attempt_number} attempts. last error={exc}"
    )
    # You can return a sentinel object here instead of raising if you want.
    # With reraise=True (see decorator below), Tenacity will re-raise the last exception.
    return None



@retry(
    wait=wait_random_exponential(min=1, max=180),
    stop=stop_after_attempt(10),
    before_sleep=_before_retry,
    retry_error_callback=_on_final_failure,
    reraise=True,  # re-raise the final exception to outer code
)
def _tenacious_completion_collect(
    *,
    routed_model,
    route_params,
    common_kwargs,
    messages):
    
    if route_params is not None:
        resp = completion(
            custom_llm_provider=route_params["provider"],
            model=routed_model,
            api_base=route_params["api_base"],
            api_key=route_params["api_key"],
            **common_kwargs,
        )
    else:
        # No routing → standard LiteLLM call
        resp = completion(model=routed_model, **common_kwargs)

    if common_kwargs.get("stream"):
        chunks = []
        for c in resp:
            chunks.append(c)
        return stream_chunk_builder(chunks, messages=messages)

    return resp


@retry(
    wait=wait_random_exponential(min=1, max=180),
    stop=stop_after_attempt(10),
    before_sleep=_before_retry,
    retry_error_callback=_on_final_failure,
    reraise=True,  # re-raise the final exception to outer code
)
def  _tenacious_completion(
    *,
    routed_model,
    route_params,
    common_kwargs,
):
    """
    Tenacity-wrapped LiteLLM call.
    Retries on exceptions with exponential backoff.
    """
    if route_params is not None:
        return completion(
            custom_llm_provider=route_params["provider"],
            model=routed_model,
            api_base=route_params["api_base"],
            api_key=route_params["api_key"],
            **common_kwargs,
        )
    else:
        # No routing → standard LiteLLM call
        return completion(model=routed_model, **common_kwargs)



def exp_wait_seconds(attempt, *, min_s = 1.0, max_s = 180.0, base = 2.0):
    upper = min(max_s, base ** attempt)
    lower = min_s
    if upper < lower:
        return lower
    return random.uniform(lower, upper)

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def get_global_max_tokens(cfg):
    return int(cfg.get("max_tokens", 8192))

def get_model_max_tokens(cfg, model):
    hp = _hp_litellm(cfg).get(model, {}) or {}        # CHANGED
    if "max_tokens" in hp and hp["max_tokens"] is not None:
        return int(hp["max_tokens"])
    return None

def get_effective_max_tokens(cfg, model):
    per_model = get_model_max_tokens(cfg, model)
    return per_model if per_model is not None else get_global_max_tokens(cfg)

def get_system_message_for_prompt(cfg, prompt_col):
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

def sanitize(s):
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", s).strip("-").lower()

def short_hash_from_kwargs(kwargs, length=8):
    payload = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]

def make_col_base(prompt_col, model_name, iter_n, hp_hash):
    p = sanitize(prompt_col)
    m = sanitize(model_name.split("/")[-1])
    return f"{COL_PREFIX}{p}__{m}__i{iter_n}__h{hp_hash}"

def make_col_names(prompt_col, model_name, iter_n, hp_hash):
    base = make_col_base(prompt_col, model_name, iter_n, hp_hash)
    return {
        "out":    f"{base}__output",
        "resp":   f"{base}__complete_response",
        "extracted_element":  f"{base}__extracted_element",
        "meta":   f"{base}__metadata",
        "prompt": f"{base}__prompt_sent",
    }


# ============================================
# Decoding policy → LiteLLM sampling kwargs
# ============================================

_SAMPLING_KEYS = ["temperature", "top_p", "top_k", "min_p",
                  "presence_penalty", "frequency_penalty"]

def build_sampling_kwargs(cfg, model):
    """
    Returns (sampling_kwargs_for_completion, effective_knobs_for_hash)
    - Excludes max_tokens from the hash basis.
    - Honors decoding_policy: default | greedy | custom_sampling
    - max_tokens is NOT included by default (LiteLLM defaults to infinity).
    - Includes reasoning_effort in hash if set (affects output).
    """
    hp = _hp_litellm(cfg).get(model, {}) or {}        # CHANGED
    policy = (hp.get("decoding_policy", "default") or "default").lower()

    # >>> max_tokens handling >>>
    # Uncomment to include max_tokens in sampling kwargs
    # max_tokens = get_effective_max_tokens(cfg, model)
    # sampling_kwargs: Dict[str, Any] = {"max_tokens": max_tokens}

    # max_tokens is intentionally NOT included - LiteLLM defaults to infinity
    # Comment out this line and uncomment sampling_kwargs and max_tokens above to include it.
    sampling_kwargs: Dict[str, Any] = {}
    # <<<< max_tokens handling <<<
    
    hash_basis: Dict[str, Any] = {}

    # Include reasoning_effort in hash if set (it affects model output)
    reasoning_effort = hp.get("reasoning_effort", None)
    if reasoning_effort is not None:
        hash_basis["reasoning_effort"] = reasoning_effort

    if policy == "default":
        return sampling_kwargs, hash_basis

    elif policy == "greedy":
        sampling_kwargs["temperature"] = 0.0
        hash_basis["temperature"] = 0.0
        return sampling_kwargs, hash_basis

    elif policy == "custom_sampling":
        for k in _SAMPLING_KEYS:
            if k in hp and hp[k] is not None:
                sampling_kwargs[k] = hp[k]
                hash_basis[k] = hp[k]
        extra = hp.get("extra_sampling", {})
        if isinstance(extra, dict):
            for k, v in extra.items():
                sampling_kwargs[k] = v
                hash_basis[k] = v
        return sampling_kwargs, hash_basis

    else:
        raise ValueError(f"Unknown decoding_policy '{policy}' for model '{model}'")


# =========================
# ROUTING (from config)
# =========================

def _require(value, name):
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def _resolve_route_env(route_cfg):
    base_env = route_cfg["api_base_env"]
    key_env  = route_cfg["api_key_env"]
    api_base = os.getenv(base_env) or (route_cfg.get("defaults") or {}).get("api_base")
    api_key  = os.getenv(key_env)
    return {"api_base": _require(api_base, base_env), "api_key": _require(api_key, key_env)}

def _route_model(model, routes):
    for prefix, cfg in (routes or {}).items():
        if model.startswith(prefix):
            stripped = model[len(prefix):]
            params = {
                "provider": cfg["provider"],
                **_resolve_route_env(cfg),
            }
            return stripped, params, prefix
    return model, None, None


# =========================
# Message building
# =========================

def build_conversation_for_row(user_text, system_msg):
    convo: List[Dict[str, str]] = []
    if system_msg:
        convo.append({"role": "system", "content": system_msg})
    convo.append({"role": "user", "content": user_text or ""})
    return convo

def dump_litellm_json(obj):
    # Prefer .model_dump_json() if provided by LiteLLM’s Pydantic object
    try:
        if hasattr(obj, "model_dump_json"):
            return obj.model_dump_json()
    except Exception:
        pass
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return json.dumps(str(obj), ensure_ascii=False)

def get_text_from_response(resp):
    """
    Try to extract "only_output" text from either a dict-like or LiteLLM ModelResponse.
    """
    try:
        # dict-like path (e.g., built from stream chunks)
        if isinstance(resp, dict):
            return (((resp or {}).get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        # ModelResponse path
        if hasattr(resp, "choices"):
            # pydantic model with attributes
            ch0 = resp.choices[0]
            msg = getattr(ch0, "message", None) or {}
            content = getattr(msg, "content", None)
            if content is None and isinstance(ch0, dict):
                content = ch0.get("message", {}).get("content")
            return content or ""
    except Exception:
        pass
    return ""


# =========================
# Core per-model runner
# =========================

def run_single_model(cfg, model_name):
    """
    Run inference for a single model.
    
    Args:
        cfg: Already-loaded config dictionary (not a path)
        model_name: Name of the model to run
    """
    routes = cfg.get("routes", {}) or {}

    seed = top_level_seed(cfg)
    set_global_seed(seed)

    df = pd.read_csv(cfg["primary_file"])
    
    print(f"\n{'='*60}")
    print(f"[info] CSV file: {cfg['primary_file']}")
    print(f"[info] Total rows: {len(df)}")
    print(f"[info] Model to run: {model_name}")
    print(f"[info] Prompts to process: {cfg['prompt_to_score_list']}")
    print(f"{'='*60}\n")

    # Testing subset (same as vLLM)
    if cfg.get("for_testing_purpose", False):
        pct = max(1, min(100, int(cfg.get("working_with_n_percentage_of_data", 10))))
        n = math.ceil(len(df) * (pct / 100.0))
        df = df.sample(n=n, random_state=42).reset_index(drop=True)
        print(f"[info] Testing mode: using {pct}% -> {n} rows.")

    
    # --- ADD ---
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

    def _is_valid_and_value(text):
        if not extraction_fn:
            return True, None
        try:
            val = extraction_fn(text or "")
        except Exception:
            return False, None
        if val is None or val == ERROR_TOKEN:
            return False, None
        return True, val
    # --- /ADD ---


    # sampling kwargs + hash (exclude max_tokens from hash)
    sampling_kwargs, hash_basis = build_sampling_kwargs(cfg, model_name)
    hp_hash = short_hash_from_kwargs(hash_basis)

    # pull litellm-specific runtime knobs from model_hyperparameters
    hp = _hp_litellm(cfg).get(model_name, {}) or {}       
    stream            = bool(hp.get("stream", True))
    num_retries       = int(hp.get("num_retries", 20))   
    reasoning_effort  = hp.get("reasoning_effort", None) # can be None; still forwarded if present
    # Optional: per-call request_timeout
    request_timeout   = hp.get("request_timeout", None)

    # iterations
    iters = int(cfg["iteration"]["iterations"])
    start_it = int(cfg["iteration"]["start_iteration"])
    iter_values = list(range(start_it, start_it + iters))

    prompt_cols: List[str] = cfg["prompt_to_score_list"]
    overwrite = bool(cfg["overwrite_existing_output_columns"])


    for prompt_col in prompt_cols:
        if prompt_col not in df.columns:
            raise KeyError(f"Prompt column missing: {prompt_col}")

        idx_all = df.index[df[prompt_col].notna()].tolist()
        if not idx_all:
            print(f"[warn] No rows to process for {prompt_col}")
            continue

        system_msg = get_system_message_for_prompt(cfg, prompt_col)

        for iter_n in iter_values:
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

            work_idx = idx_all[:]

            # Process rows one-by-one (LiteLLM has no batched chat)
            row_iter = tqdm(work_idx, desc=f"{model_name} | {prompt_col} | iter {iter_n}")
            for row_i in row_iter:
            # for row_i in work_idx:
                
                user_msg = "" if pd.isna(df.at[row_i, prompt_col]) else str(df.at[row_i, prompt_col])
                messages = build_conversation_for_row(user_msg, system_msg)

                # Route model if it has a known prefix
                routed_model, route_params, route_id = _route_model(model_name, routes)

                # Prepare common kwargs for LiteLLM call
                common_kwargs = dict(
                    messages=messages,
                    stream=stream,
                    # num_retries=num_retries,
                    **sampling_kwargs,
                )
                # Optionals
                if reasoning_effort is not None:
                    common_kwargs["reasoning_effort"] = reasoning_effort
                if request_timeout is not None:
                    common_kwargs["request_timeout"] = request_timeout

                # Forward seed too if set (many providers ignore; included per request)
                if seed is not None:
                    common_kwargs["seed"] = seed

                # ---- Single-call + optional validation retry loop ----
                attempt = 0
                max_validate_retries = num_retries if upfront_check and extraction_fn is not None else 1
                final_only_output = ""
                final_complete_resp = None
                final_cost = None

                while attempt < max_validate_retries:
                    attempt += 1
                    try:
                        # resp = _tenacious_completion(
                        #     routed_model=routed_model,
                        #     route_params=route_params,
                        #     common_kwargs=common_kwargs,
                        # )

                        # # Assemble complete response & text
                        # if stream:
                        #     chunks = [c for c in resp]
                        #     complete_resp = stream_chunk_builder(chunks, messages=messages)
                        # else:
                        #     complete_resp = resp

                        # only_output = get_text_from_response(complete_resp)
                        
                        complete_resp = _tenacious_completion_collect(
                            routed_model=routed_model,
                            route_params=route_params,
                            common_kwargs=common_kwargs,
                            messages=messages,
                        )
                        only_output = get_text_from_response(complete_resp)

                        # Compute cost (best-effort)
                        cost_value = None
                        try:
                            # If custom route has custom_pricing metadata, attach it;
                            # also try LiteLLM cost when possible.
                            if route_id is not None:
                                # Try built-in cost first
                                try:
                                    cost_value = float(completion_cost(completion_response=complete_resp, model=routed_model))
                                except Exception:
                                    cost_value = None
                                # Attach pricing_info from config if present
                                pricing_info = (routes.get(route_id, {}).get("custom_pricing") or {}).get(routed_model)
                            else:
                                cost_value = float(completion_cost(completion_response=complete_resp, model=routed_model))
                                pricing_info = None
                        except Exception:
                            pricing_info = (routes.get(route_id, {}).get("custom_pricing") or {}).get(routed_model) if route_id else None
                            cost_value = None

                        final_only_output = only_output
                        final_complete_resp = complete_resp
                        final_cost = cost_value
                        final_pricing_info = pricing_info
                        
                        # --- validation / retry decision ---
                        if upfront_check and extraction_fn is not None:
                            is_ok, _ = _is_valid_and_value(only_output)   # extractor runs only when needed
                            if is_ok:
                                break # success, stop retrying
                            
                            #  invalid extraction
                            if attempt < max_validate_retries:
                                sleep_s = exp_wait_seconds(attempt, min_s=1.0, max_s=180.0, base=2.0)
                                print(
                                    f"[retry-row] prompt={prompt_col} row={row_i} attempt={attempt} "
                                    f"sleeping {sleep_s:.1f}s (invalid extraction)"
                                )
                                time.sleep(sleep_s)
                            else:
                                # last attempt AND still invalid → mark as failed
                                print(
                                    f"[fail-row] prompt={prompt_col} row={row_i} "
                                    f"reason=invalid_extraction output={only_output[:200]!r}"
                                )
                        else:
                            break  # no upfront check => no validation calls, no retries
                        

                    except Exception as e:
                        # Tenacity already exhausted its retries inside _tenacious_completion
                        err = f"[litellm-error] {e}"
                        final_only_output = ""
                        final_complete_resp = {"error": str(e)}
                        final_cost = None
                        final_pricing_info = None
                        # Just log once and give up on this row
                        print(f"[fail-row] prompt={prompt_col} row={row_i} error={err}")
                        break  # exit the while loop for this row

                # Save outputs
                df.at[row_i, cols["out"]]  = final_only_output
                df.at[row_i, cols["resp"]] = dump_litellm_json(final_complete_resp)
                    

                if upfront_check and extraction_fn is not None:
                    ok, val = _is_valid_and_value(final_only_output)
                    df.at[row_i, cols["extracted_element"]] = (val if ok else None)



                # Build meta (align with vLLM + add LiteLLM specifics)
                meta_payload = {
                    "model": model_name,
                    "routed_model": routed_model,
                    "route_id": route_id,
                    "prompt_col": prompt_col,
                    "iteration": iter_n,
                    "dataset": cfg["primary_file"],
                    "decoding_policy": hp.get("decoding_policy", "default"),
                    "sampling_kwargs_effective": hash_basis,
                    "max_tokens": "infinity (default)",  # Not set - LiteLLM defaults to infinity
                    # "max_tokens": 8192, # Uncomment if max_tokens is included above
                    "seed": seed,
                    "stream": stream,
                    "num_retries": 20,
                    "reasoning_effort": reasoning_effort,
                    "extraction_enabled": bool(cfg.get("extraction", {}).get("enabled", False)),
                    "extraction_function": extraction_fn_path,
                    "upfront_check_extraction": upfront_check,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "cost": final_cost,                         # exact call cost if available
                }
                # Attach any custom pricing metadata without leaking secrets
                if route_id is not None:
                    meta_payload["pricing_info"] = final_pricing_info

                df.at[row_i, cols["meta"]] = json.dumps(meta_payload, ensure_ascii=False)

                # Save exact prompt payload on first iteration
                if iter_n == 1:
                    df.at[row_i, cols["prompt"]] = json.dumps(messages, ensure_ascii=False)

            print(f"[done] (litellm) model={model_name} prompt={prompt_col} iter={iter_n} rows={len(work_idx)}")

    # Save CSV and Excel
    df.to_csv(cfg["primary_file"], index=False)

    # sanitize *only* for Excel export
    df_excel = df.map(clean_cell)
    df_excel.to_excel(cfg["primary_file"].replace(".csv", ".xlsx"), index=False, engine="xlsxwriter")

    print(f"[saved] {cfg['primary_file']}")
    print(f"[saved] {cfg['primary_file'].replace('.csv', '.xlsx')}")

    # Cleanup
    gc.collect()



# =========================
# CLI
# =========================

# --- simplify CLI main(): run sequentially in-process ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--only_model", default=None, help="If set, run only this model")
    args = parser.parse_args()

    # Load config ONCE at startup
    cfg = load_yaml(args.config)

    # Print run summary
    print(f"\n{'='*60}")
    print(f"[LiteLLM Inference Script]")
    print(f"{'='*60}")
    print(f"[info] Config file: {args.config}")
    print(f"[info] CSV file: {cfg['primary_file']}")
    print(f"[info] Prompts to process: {cfg['prompt_to_score_list']}")
    
    if args.only_model:
        print(f"[info] Models to run: [{args.only_model}] (--only_model)")
    else:
        models = cfg.get("model_list_litellm", [])
        print(f"[info] Models to run: {models}")
    print(f"{'='*60}\n")

    if args.only_model:
        run_single_model(cfg, args.only_model)                         # pass cfg dict directly
    else:
        models = cfg.get("model_list_litellm", [])                     
        if not models:
            raise RuntimeError("No models under 'model_list_litellm' in config.")
        for m in models:
            print(f"[run] (litellm) model: {m}")
            run_single_model(cfg, m)                                   # pass cfg dict directly

if __name__ == "__main__":
    main()