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