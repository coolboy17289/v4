"""
Inference Engine for running model inference
"""

import logging
import time
import torch
from typing import Dict, Any, List, Union, Optional
from transformers import PreTrainedModel, PreTrainedTokenizer

logger = logging.getLogger(__name__)


class InferenceEngine:
    """Handles inference operations with various optimization techniques"""

    def __init__(self, model_loader: 'ModelLoader'):
        self.model_loader = model_loader
        self.device = self._get_device()

    def _get_device(self) -> int:
        """Determine the best available device"""
        if torch.cuda.is_available():
            return 0  # Use first GPU
        return -1  # Use CPU

    def generate_text(self, model_name: str, prompt: str,
                     max_length: int = 100,
                     temperature: float = 0.7,
                     top_p: float = 0.9,
                     do_sample: bool = True,
                     **kwargs) -> Dict[str, Any]:
        """
        Generate text using a language model

        Args:
            model_name: Name of the model to use
            prompt: Input text to generate from
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            do_sample: Whether to use sampling
            **kwargs: Additional generation parameters

        Returns:
            Dictionary with generated text and metadata
        """
        start_time = time.time()

        try:
            logger.info(f"Generating text with model {model_name}")

            # Get or create text generation pipeline
            generator = self.model_loader.create_pipeline(
                model_name,
                "text-generation",
                device=self.device
            )

            # Generate text
            outputs = generator(
                prompt,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                **kwargs
            )

            # Extract generated text (remove the prompt)
            generated_text = outputs[0]['generated_text']
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):]

            end_time = time.time()
            processing_time = end_time - start_time

            result = {
                "generated_text": generated_text.strip(),
                "prompt": prompt,
                "model_used": model_name,
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": do_sample
                },
                "processing_time": processing_time,
                "timestamp": time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error during text generation: {str(e)}")
            raise

    def embed_text(self, model_name: str, texts: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Generate embeddings for text

        Args:
            model_name: Name of the embedding model
            texts: Single text or list of texts to embed

        Returns:
            Dictionary with embeddings and metadata
        """
        start_time = time.time()

        try:
            logger.info(f"Generating embeddings with model {model_name}")

            # Ensure tokens are list
            if isinstance(texts, str):
                texts = [texts]

            # Get or create feature extraction pipeline
            feature_extractor = self.model_loader.create_pipeline(
                model_name,
                "feature-extraction",
                device=self.device
            )

            # Generate embeddings
            embeddings = feature_extractor(texts)

            # For sentence transformers, we usually take the mean of the last hidden state
            # But for simplicity, we'll return the raw output
            # In a real implementation, you'd process this appropriately

            end_time = time.time()
            processing_time = end_time - start_time

            result = {
                "embeddings": embeddings,
                "input_texts": texts,
                "model_used": model_name,
                "num_texts": len(texts),
                "processing_time": processing_time,
                "timestamp": time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error during embedding generation: {str(e)}")
            raise

    def answer_question(self, model_name: str, question: str,
                       context: str = "") -> Dict[str, Any]:
        """
        Answer a question using a QA model

        Args:
            model_name: Name of the QA model
            question: Question to answer
            context: Context in which to find the answer (optional)

        Returns:
            Dictionary with answer and metadata
        """
        start_time = time.time()

        try:
            logger.info(f"Answering question with model {model_name}")

            # Get or create question-answering pipeline
            qa_pipeline = self.model_loader.create_pipeline(
                model_name,
                "question-answering",
                device=self.device
            )

            # Prepare input
            if context:
                inputs = {
                    "question": question,
                    "context": context
                }
            else:
                # For models that don't require separate context
                inputs = question

            # Get answer
            result = qa_pipeline(inputs)

            end_time = time.time()
            processing_time = end_time - start_time

            # Format result
            answer_result = {
                "answer": result.get('answer', ''),
                "score": result.get('score', 0.0),
                "start": result.get('start', 0),
                "end": result.get('end', 0),
                "question": question,
                "context": context if context else "Not provided",
                "model_used": model_name,
                "processing_time": processing_time,
                "timestamp": time.time()
            }

            return answer_result

        except Exception as e:
            logger.error(f"Error during question answering: {str(e)}")
            raise

    def summarize_text(self, model_name: str, text: str,
                      max_length: int = 130,
                      min_length: int = 30,
                      do_sample: bool = False) -> Dict[str, Any]:
        """
        Summarize text using a summarization model

        Args:
            model_name: Name of the summarization model
            text: Text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            do_sample: Whether to use sampling

        Returns:
            Dictionary with summary and metadata
        """
        start_time = time.time()

        try:
            logger.info(f"Summarizing text with model {model_name}")

            # Get or create summarization pipeline
            summarizer = self.model_loader.create_pipeline(
                model_name,
                "summarization",
                device=self.device
            )

            # Generate summary
            summary_result = summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=do_sample
            )

            summary_text = summary_result[0]['summary_text']

            end_time = time.time()
            processing_time = end_time - start_time

            result = {
                "summary": summary_text,
                "original_text": text,
                "model_used": model_name,
                "parameters": {
                    "max_length": max_length,
                    "min_length": min_length,
                    "do_sample": do_sample
                },
                "processing_time": processing_time,
                "timestamp": time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error during text summarization: {str(e)}")
            raise

    def translate_text(self, model_name: str, text: str,
                      src_lang: str = "en",
                      tgt_lang: str = "de",
                      **kwargs) -> Dict[str, Any]:
        """
        Translate text using a translation model

        Args:
            model_name: Name of the translation model
            text: Text to translate
            src_lang: Source language code
            tgt_lang: Target language code
            **kwargs: Additional translation parameters

        Returns:
            Dictionary with translation and metadata
        """
        start_time = time.time()

        try:
            logger.info(f"Translating text with model {model_name} from {src_lang} to {tgt_lang}")

            # Get or create translation pipeline
            translator = self.model_loader.create_pipeline(
                model_name,
                "translation",
                device=self.device
            )

            # Translate
            translation_result = translator(
                text,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                **kwargs
            )

            translated_text = translation_result[0]['translation_text']

            end_time = time.time()
            processing_time = end_time - start_time

            result = {
                "translation": translated_text,
                "original_text": text,
                "source_language": src_lang,
                "target_language": tgt_lang,
                "model_used": model_name,
                "processing_time": processing_time,
                "timestamp": time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error during translation: {str(e)}")
            raise

    def get_available_models(self) -> Dict[str, List[str]]:
        """
        Get information about available models for different tasks

        Returns:
            Dictionary mapping task types to lists of model names
        """
        # In a real implementation, this might query a model registry
        # For now, return some common model examples
        return {
            "text-generation": [
                "gpt2",
                "EleutherAI/gpt-neo-125M",
                "microsoft/DialoGPT-medium"
            ],
            "text-classification": [
                "distilbert-base-uncased-finetuned-sst-2-english",
                "nlptown/bert-base-multilingual-uncased-sentiment"
            ],
            "question-answering": [
                "distilbert-base-cased-distilled-squad",
                "bert-large-uncased-whole-word-masking-finetuned-squad"
            ],
            "summarization": [
                "facebook/bart-large-cnn",
                "google/pegasus-xsum"
            ],
            "translation": [
                "Helsinki-NLP/opus-mt-en-de",
                "Helsinki-NLP/opus-mt-en-fr"
            ],
            "feature-extraction": [
                "sentence-transformers/all-MiniLM-L6-v2",
                "bert-base-uncased"
            ]
        }