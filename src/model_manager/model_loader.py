"""
Model Loader for loading and managing AI models
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM, pipeline

logger = logging.getLogger(__name__)


class ModelLoader:
    """Handles loading and caching of AI models"""

    def __init__(self, cache_dir: str = "./model_cache"):
        self.cache_dir = cache_dir
        self.loaded_models: Dict[str, Any] = {}
        self.loaded_tokenizers: Dict[str, Any] = {}
        self.pipelines: Dict[str, Any] = {}

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

    def load_model(self, model_name: str, model_type: str = "auto",
                   use_auth_token: Optional[str] = None,
                   **kwargs) -> Any:
        """
        Load a model from Hugging Face or local cache

        Args:
            model_name: Name or path of the model
            model_type: Type of model ('auto', 'causal_lm', 'seq2seq', etc.)
            use_auth_token: Hugging Face auth token if needed
            **kwargs: Additional arguments for model loading

        Returns:
            Loaded model object
        """
        cache_key = f"{model_name}_{model_type}"

        if cache_key in self.loaded_models:
            logger.info(f"Returning cached model: {cache_key}")
            return self.loaded_models[cache_key]

        try:
            logger.info(f"Loading model: {model_name} (type: {model_type})")

            if model_type == "causal_lm" or (model_type == "auto" and "gpt" in model_name.lower()):
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    cache_dir=self.cache_dir,
                    token=use_auth_token,
                    **kwargs
                )
            elif model_type == "seq2seq":
                from transformers import AutoModelForSeq2SeqLM
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name,
                    cache_dir=self.cache_dir,
                    token=use_auth_token,
                    **kwargs
                )
            else:
                model = AutoModel.from_pretrained(
                    model_name,
                    cache_dir=self.cache_dir,
                    token=use_auth_token,
                    **kwargs
                )

            self.loaded_models[cache_key] = model
            return model

        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise

    def load_tokenizer(self, model_name: str,
                      use_auth_token: Optional[str] = None,
                      **kwargs) -> Any:
        """
        Load a tokenizer for a model

        Args:
            model_name: Name or path of the model
            use_auth_token: Hugging Face auth token if needed
            **kwargs: Additional arguments for tokenizer loading

        Returns:
            Loaded tokenizer object
        """
        if model_name in self.loaded_tokenizers:
            logger.info(f"Returning cached tokenizer: {model_name}")
            return self.loaded_tokenizers[model_name]

        try:
            logger.info(f"Loading tokenizer: {model_name}")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                token=use_auth_token,
                **kwargs
            )
            self.loaded_tokenizers[model_name] = tokenizer
            return tokenizer

        except Exception as e:
            logger.error(f"Failed to load tokenizer {model_name}: {str(e)}")
            raise

    def create_pipeline(self, model_name: str, task: str,
                       model: Optional[Any] = None,
                       tokenizer: Optional[Any] = None,
                       device: int = -1,
                       **kwargs) -> Any:
        """
        create a pipeline for a specific task

        Args:
            model_name: Name or path of the model
            task: Task for the pipeline (e.g., 'text-generation', 'translation')
            model: Pre-loaded model (optional)
            tokenizer: Pre-loaded tokenizer (optional)
            device: Device to run on (-1 for CPU, 0+ for GPU)
            **kwargs: Additional arguments for the pipeline

        Returns:
            Pipeline object
        """
        pipeline_key = f"{model_name}_{task}_{device}"

        if pipeline_key in self.pipelines:
            logger.info(f"Returning cached pipeline: {pipeline_key}")
            return self.pipelines[pipeline_key]

        try:
            logger.info(f"Creating pipeline: {task} with model {model_name}")

            if model is None:
                model = self.load_model(model_name)
            if tokenizer is None:
                tokenizer = self.load_tokenizer(model_name)

            pipe = pipeline(
                task,
                model=model,
                tokenizer=tokenizer,
                device=device,
                **kwargs
            )

            self.pipelines[pipeline_key] = pipe
            return pipe

        except Exception as e:
            logger.error(f"Failed to create pipeline for {model_name} task {task}: {str(e)}")
            raise

    def unload_model(self, model_name: str, model_type: str = "auto"):
        """
        Unload a model from memory

        Args:
            model_name: Name of the model to unload
            model_type: Type of the model
        """
        cache_key = f"{model_name}_{model_type}"
        if cache_key in self.loaded_models:
            del self.loaded_models[cache_key]
            logger.info(f"Unloaded model: {cache_key}")

        # Also remove associated tokenizers and pipelines
        if model_name in self.loaded_tokenizers:
            del self.loaded_tokenizers[model_name]
            logger.info(f"Unloaded tokenizer: {model_name}")

        # Remove pipelines that use this model
        keys_to_remove = [k for k in self.pipelines.keys() if k.startswith(model_name)]
        for key in keys_to_remove:
            del self.pipelines[key]
            logger.info(f"Removed pipeline: {key}")

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a loaded model

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model information
        """
        # In a real implementation, this would return detailed info
        return {
            "model_name": model_name,
            "is_loaded": any(model_name in key for key in self.loaded_models.keys()),
            "cache_dir": self.cache_dir
        }