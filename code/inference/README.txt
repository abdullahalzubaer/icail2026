Code Execution Guide

    LiteLLM Models
    --------------
    Run inference for all models in litellm_vllm_config.yaml:
        python litellm_inf.py --config litellm_vllm_config.yaml

    Run inference for a single model:
        python litellm_inf.py --config litellm_vllm_config.yaml --only_model <model_name>

    vLLM Models
    -----------
    Run with one GPU:
        CUDA_VISIBLE_DEVICES=1 python vllm_inf.py --config litellm_vllm_config.yaml

    Run with two GPUs:
        CUDA_VISIBLE_DEVICES=1,4 python vllm_inf.py --config litellm_vllm_config.yaml

    (Optional) Run a single model:
        CUDA_VISIBLE_DEVICES=0 python vllm_inf.py --config litellm_vllm_config.yaml --only_model google/gemma-3-27b-it

    Note:
    Ensure your config file (litellm_vllm_config.yaml) lists all desired models and their parameters.


Hyperparameters:
    We used provider-default hyperparameters for all models, as in prior benchmarking work [2] 


Note: 

    - We allowed up to 20 retries for invalid outputs and 10 for temporary execution failures. 
    -  Using OpenRouter pricing, the total inference cost for successful generations was approx $280 (criminal law: $247; public law: $33) (excluding OpenAI-direct usage, which is only available as account-level aggregates, and excluding unlogged failed retries).

[2] Odysseas S. Chlapanis, Dimitrios Galanis, Nikolaos Aletras, and Ion Androutsopoulos. 2025. GreekBarBench: A Challenging Benchmark for Free-Text Legal Reasoning and Citations. In Findings of the Association for Computational Linguistics: EMNLP 2025, pages 25099–25119, Suzhou, China. Association for Computational Linguistics.
