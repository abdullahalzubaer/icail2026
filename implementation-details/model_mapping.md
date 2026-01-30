# Model Name Mapping (Paper ↔ Experiment IDs)


This README maps **model names referenced in the paper** (left) to the **exact model identifiers used in our experiments** (right), grouped by access method (OpenRouter, OpenAI API, or local vLLM via Hugging Face).

---

## Models via OpenRouter

| Paper name | Experiment ID (OpenRouter) |
|---|---|
| Gemini-2.5-Pro | `openrouter/google/gemini-2.5-pro` |
| DeepSeeek-685B-V3.1 | `openrouter/deepseek/deepseek-v3.1-terminus` |
| Qwen3-Next-80B-Th. | `openrouter/qwen/qwen3-next-80b-a3b-thinking` |
| Qwen3-Next-80B-it. | `openrouter/qwen/qwen3-next-80b-a3b-instruct` |
| Qwen3-235B | `openrouter/qwen/qwen3-235b-a22b-2507` |
| Qwen3-235B-Th. | `openrouter/qwen/qwen3-235b-a22b-thinking-2507` |
| GPT-OSS-120B | `openrouter/openai/gpt-oss-120b` |
| GPT-OSS-20B | `openrouter/openai/gpt-oss-20b` |
| Llama-3.3-70B-it | `openrouter/meta-llama/llama-3.3-70b-instruct` |
| Mistral-Large | `openrouter/mistralai/mistral-large-2512` |

---

## Models via OpenAI API

| Paper name | Experiment ID (OpenAI) |
|---|---|
| GPT-5 | `gpt-5-2025-08-07` |
| GPT-5.1 | `gpt-5.1-2025-11-13` |
| GPT-5.2 | `gpt-5.2-2025-12-11` |
| GPT-5-mini | `gpt-5-mini-2025-08-07` |
| GPT-4o-mini | `gpt-4o-mini-2024-07-18` |
| GPT-4o | `gpt-4o-2024-11-20` |
| GPT-4.1 | `gpt-4.1-2025-04-14` |
| GPT-4.1-mini | `gpt-4.1-mini-2025-04-14` |

---

## Models run locally (vLLM via Hugging Face)

| Paper name | Experiment ID (HF repo) |
|---|---|
| QwQ-32B | `Qwen/QwQ-32B` |
| Qwen3-32B | `Qwen/Qwen3-32B` |
| Qwen3-30B-Th. | `Qwen/Qwen3-30B-A3B-Thinking-2507` |
| Qwen3-30B-it | `Qwen/Qwen3-30B-A3B-Instruct-2507` |
| Ministral-3-14B-it | `mistralai/Ministral-3-14B-Instruct-2512` |
| Ministral-3-14B-Rea. | `mistralai/Ministral-3-14B-Reasoning-2512` |
| Gemma-3-27B-it | `google/gemma-3-27b-it` |
| EuroLLM-22B-it | `utter-project/EuroLLM-22B-Instruct-2512` |
| Apertus-70B-it | `swiss-ai/Apertus-70B-Instruct-2509` |

---

## Notes

- **Paper name** = shorthand label used in the manuscript and plots/tables.
- **Experiment ID** = exact model identifier used in code/configs.
- Suffix conventions:
  - `-it` / `-instruct` = instruction-tuned/chat variant
  - `-Th.` / `-thinking` / `-Reasoning` = reasoning/thinking variant (as provided by the respective provider)


