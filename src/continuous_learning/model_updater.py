"""
Model Updater for updating models based on learned patterns
"""

import logging
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ModelUpdater:
    """Updates models based on learned patterns and feedback"""

    def __init__(self, model_registry_path: str = "./models"):
        self.model_registry_path = model_registry_path
        self.update_queue: List[Dict[str, Any]] = []
        self.last_update_time: Dict[str, datetime] = {}

        # Ensure registry directory exists
        os.makedirs(self.model_registry_path, exist_ok=True)

    def queue_model_update(self, model_name: str, update_type: str,
                          update_data: Dict[str, Any],
                          priority: str = "normal") -> bool:
        """
        Queue a model update for processing

        Args:
            model_name: Name of the model to update
            update_type: Type of update (e.g., 'fine_tune', 'prompt_adjustment', 'parameter_tweak')
            update_data: Data needed for the update
            priority: Priority of the update ('low', 'normal', 'high')

        Returns:
            bool: True if successfully queued
        """
        try:
            update_request = {
                "model_name": model_name,
                "update_type": update_type,
                "update_data": update_data,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat(),
                "id": self._generate_update_id()
            }

            self.update_queue.append(update_request)
            # Sort by priority (high first)
            priority_order = {"high": 0, "normal": 1, "low": 2}
            self.update_queue.sort(
                key=lambda x: priority_order.get(x["priority"], 3)
            )

            logger.info(f"Queued {update_type} update for model {model_name} with priority {priority}")
            return True
        except Exception as e:
            logger.error(f"Error queuing model update: {e}")
            return False

    def process_update_queue(self, max_updates: int = 5) -> List[Dict[str, Any]]:
        """
        Process queued model updates

        Args:
            max_updates: Maximum number of updates to process in this batch

        Returns:
            List of update results
        """
        results = []
        processed_count = 0

        while self.update_queue and processed_count < max_updates:
            update_request = self.update_queue.pop(0)  # Take highest priority
            result = self._process_update_request(update_request)
            results.append(result)
            processed_count += 1

        return results

    def _process_update_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single model update request

        Args:
            request: The update request dictionary

        Returns:
            Result of the update attempt
        """
        model_name = request["model_name"]
        update_type = request["update_type"]
        update_data = request["update_data"]

        try:
            logger.info(f"Processing {update_type} update for {model_name}")

            # Check if we should throttle updates for this model
            if self._should_throttle_update(model_name):
                return {
                    "success": False,
                    "model_name": model_name,
                    "update_type": update_type,
                    "reason": "throttled",
                    "message": f"Update throttled for {model_name}"
                }

            # Process based on update type
            if update_type == "fine_tune":
                result = self._perform_fine_tuning(model_name, update_data)
            elif update_type == "prompt_adjustment":
                result = self._adjust_prompt(model_name, update_data)
            elif update_type == "parameter_tweak":
                result = self._tweak_parameters(model_name, update_data)
            elif update_type == "update_training_data":
                result = self._update_training_data(model_name, update_data)
            else:
                result = {
                    "success": False,
                    "model_name": model_name,
                    "update_type": update_type,
                    "error": f"Unknown update type: {update_type}"
                }

            # Update last update time if successful
            if result.get("success", False):
                self.last_update_time[model_name] = datetime.utcnow()

            return result

        except Exception as e:
            logger.error(f"Error processing update for {model_name}: {e}")
            return {
                "success": False,
                "model_name": model_name,
                "update_type": request["update_type"],
                "error": str(e)
            }

    def _should_throttle_update(self, model_name: str) -> bool:
        """Check if we should throttle updates for a model"""
        if model_name not in self.last_update_time:
            return False

        last_update = self.last_update_time[model_name]
        time_since_last = datetime.utcnow() - last_update

        # Don't update more than once per hour for the same model
        return time_since_last < timedelta(hours=1)

    def _perform_fine_tuning(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform fine-tuning on a model"""
        # In a real implementation, this would trigger a training job
        # For now, we'll simulate it
        epochs = data.get("epochs", 3)
        learning_rate = data.get("learning_rate", 1e-5)

        logger.info(f"Simulating fine-tuning of {model_name} for {epochs} epochs with LR {learning_rate}")

        # Simulate success
        return {
            "success": True,
            "model_name": model_name,
            "update_type": "fine_tune",
            "details": {
                "epochs": epochs,
                "learning_rate": learning_rate,
                "status": "completed_simulation"
            }
        }

    def _adjust_prompt(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust the prompt template for a model"""
        template = data.get("template", "")
        variables = data.get("variables", {})

        if not template:
            return {
                "success": False,
                "model_name": model_name,
                "update_type": "prompt_adjustment",
                "error": "No template provided"
            }

        # Save the new template
        template_path = f"{self.model_registry_path}/{model_name}_prompt_template.txt"
        try:
            with open(template_path, 'w') as f:
                f.write(template)
            # Also save variables if provided
            if variables:
                vars_path = f"{self.model_registry_path}/{model_name}_prompt_variables.json"
                with open(vars_path, 'w') as f:
                    json.dump(variables, f, indent=2)

            return {
                "success": True,
                "model_name": model_name,
                "update_type": "prompt_adjustment",
                "details": {
                    "template_saved": template_path,
                    "variables_saved": bool(variables)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "model_name": model_name,
                "update_type": "prompt_adjustment",
                "error": f"Failed to save template: {e}"
            }

    def _tweak_parameters(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Tweak model parameters"""
        parameters = data.get("parameters", {})

        if not parameters:
            return {
                "success": False,
                "model_name": model_name,
                "update_type": "parameter_tweak",
                "error": "No parameters provided"
            }

        # Save the parameters
        params_path = f"{self.model_registry_path}/{model_name}_parameters.json"
        try:
            # Load existing parameters if any
            existing_params = {}
            if os.path.exists(params_path):
                with open(params_path, 'r') as f:
                    existing_params = json.load(f)

            # Update with new values
            existing_params.update(parameters)

            with open(params_path, 'w') as f:
                json.dump(existing_params, f, indent=2)

            return {
                "success": True,
                "model_name": model_name,
                "update_type": "parameter_tweak",
                "details": {
                    "parameters_updated": list(parameters.keys()),
                    "total_parameters": len(existing_params)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "model_name": model_name,
                "update_type": "parameter_tweak",
                "error": f"Failed to update parameters: {e}"
            }

    def _update_training_data(self, model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update training data for a model"""
        new_examples = data.get("examples", [])

        if not isinstance(new_examples, list):
            return {
                "success": False,
                "model_name": model_name,
                "update_type": "update_training_data",
                "error": "Training data must be a list of examples"
            }

        # Save the new examples
        data_path = f"{self.model_registry_path}/{model_name}_training_data.jsonl"
        try:
            with open(data_path, 'a') as f:
                for example in new_examples:
                    f.write(json.dumps(example) + '\n')

            return {
                "success": True,
                "model_name": model_name,
                "update_type": "update_training_data",
                "details": {
                    "examples_added": len(new_examples),
                    "data_file": data_path
                }
            }
        except Exception as e:
            return {
                "success": False,
                "model_name": model_name,
                "update_type": "update_training_data",
                "error": f"Failed to update training data: {e}"
            }

    def get_update_history(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get history of model updates

        Args:
            model_name: If provided, only return updates for this model

        Returns:
            List of update records
        """
        # In a real implementation, this would query a database
        # For now, return an empty list
        return []

    def get_pending_updates(self) -> List[Dict[str, Any]]:
        """Get list of pending updates"""
        return self.update_queue.copy()

    def _generate_update_id(self) -> str:
        """Generate a unique ID for an update"""
        import hashlib
        import time
        data_string = f"{time.time()}:{len(self.update_queue)}"
        return hashlib.md5(data_string.encode()).hexdigest()[:8]


# Global model updater instance
model_updater = ModelUpdater()