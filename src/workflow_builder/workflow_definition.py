"""
Workflow Definition Utilities
"""

import json
from typing import Dict, Any, List, Optional
from .workflow_engine import Workflow, WorkflowStep, StepType


class WorkflowDefinition:
    """Utility class for creating and parsing workflow definitions"""

    @staticmethod
    def from_dict(definition: Dict[str, Any]) -> Workflow:
        """
        Create a workflow from a dictionary definition

        Args:
            definition: Dictionary containing workflow definition

        Returns:
            Workflow object
        """
        workflow_id = definition.get("workflow_id", str(uuid.uuid4()))
        name = definition.get("name", "Unnamed Workflow")
        description = definition.get("description", "")

        workflow = Workflow(workflow_id, name, description)

        # Add variables
        variables = definition.get("variables", {})
        for var_name, var_value in variables.items():
            workflow.add_variable(var_name, var_value)

        # Add steps
        steps_def = definition.get("steps", [])
        for step_def in steps_def:
            step_id = step_def.get("step_id", str(uuid.uuid4()))
            step_type_str = step_def.get("type", "action")
            config = step_def.get("config", {})

            try:
                step_type = StepType(step_type_str)
            except ValueError:
                # Default to action if invalid type
                step_type = StepType.ACTION

            step = WorkflowStep(step_id, step_type, config)

            # Add next steps
            next_steps = step_def.get("next_steps", [])
            for next_step_id in next_steps:
                step.add_next_step(next_step_id)

            # Add condition if present
            condition_str = step_def.get("condition")
            if condition_str:
                # In a real implementation, we would parse this into a function
                # For now, we'll just note that it has a condition
                # The actual condition function would need to be provided separately
                pass

            workflow.add_step(step)

        # Set start step
        start_step = definition.get("start_step")
        if start_step:
            workflow.set_start_step(start_step)
        elif steps_def:
            # Default to first step if not specified
            first_step_id = steps_def[0].get("step_id")
            if first_step_id:
                workflow.set_start_step(first_step_id)

        return workflow

    @staticmethod
    def from_json(json_str: str) -> Workflow:
        """
        Create a workflow from a JSON string

        Args:
            json_str: JSON string containing workflow definition

        Returns:
            Workflow object
        """
        definition = json.loads(json_str)
        return WorkflowDefinition.from_dict(definition)

    @staticmethod
    def to_dict(workflow: Workflow) -> Dict[str, Any]:
        """
        Convert a workflow to a dictionary representation

        Args:
            workflow: Workflow object

        Returns:
            Dictionary representation of the workflow
        """
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "variables": workflow.variables,
            "steps": [
                {
                    "step_id": step.step_id,
                    "type": step.step_type.value,
                    "config": step.config,
                    "next_steps": step.next_steps
                }
                for step_id, step in workflow.steps.items()
            ],
            "start_step": workflow.start_step_id
        }

    @staticmethod
    def to_json(workflow: Workflow) -> str:
        """
        Convert a workflow to a JSON string

        Args:
            workflow: Workflow object

        Returns:
            JSON string representation of the workflow
        """
        return json.dumps(WorkflowDefinition.to_dict(workflow), indent=2)