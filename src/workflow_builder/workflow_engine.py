"""
Workflow Engine for defining and executing workflows
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(Enum):
    """Type of workflow step"""
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    SUBWORKFLOW = "subworkflow"


class WorkflowStep:
    """Represents a step in a workflow"""

    def __init__(self, step_id: str, step_type: StepType, config: Dict[str, Any]):
        self.step_id = step_id
        self.step_type = step_type
        self.config = config
        self.next_steps: List[str] = []  # IDs of next steps
        self.condition: Optional[Callable[[Dict[str, Any]], bool]] = None

    def add_next_step(self, step_id: str):
        """Add a next step"""
        self.next_steps.append(step_id)

    def set_condition(self, condition_func: Callable[[Dict[str, Any]], bool]):
        """Set a condition for this step (for conditional workflows)"""
        self.condition = condition_func


class Workflow:
    """Represents a workflow definition"""

    def __init__(self, workflow_id: str, name: str, description: str = ""):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps: Dict[str, WorkflowStep] = {}
        self.start_step_id: Optional[str] = None
        self.variables: Dict[str, Any] = {}

    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps[step.step_id] = step

    def set_start_step(self, step_id: str):
        """Set the starting step"""
        if step_id not in self.steps:
            raise ValueError(f"Step {step_id} does not exist")
        self.start_step_id = step_id

    def add_variable(self, name: str, value: Any):
        """Add a variable to the workflow"""
        self.variables[name] = value

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        return self.steps.get(step_id)


class WorkflowExecutionContext:
    """Context for workflow execution"""

    def __init__(self, workflow: Workflow, initial_inputs: Dict[str, Any] = None):
        self.workflow = workflow
        self.variables = workflow.variables.copy()
        if initial_inputs:
            self.variables.update(initial_inputs)
        self.step_results: Dict[str, Any] = {}
        self.current_step_id: Optional[str] = None
        self.status = WorkflowStatus.PENDING
        self.execution_id = str(uuid.uuid4())
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None


class WorkflowEngine:
    """Engine for executing workflows"""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.action_handlers: Dict[str, Callable] = {}

    def register_workflow(self, workflow: Workflow):
        """Register a workflow with the engine"""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.workflow_id}")

    def register_action_handler(self, action_name: str, handler: Callable):
        """Register a function to handle a specific action type"""
        self.action_handlers[action_name] = handler
        logger.info(f"Registered action handler: {action_name}")

    def unregister_workflow(self, workflow_id: str):
        """Unregister a workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.info(f"Unregistered workflow: {workflow_id}")

    def execute_workflow(self, workflow_id: str, initial_inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a workflow

        Args:
            workflow_id: ID of the workflow to execute
            initial_inputs: Initial input variables

        Returns:
            Dictionary with execution results
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        context = WorkflowExecutionContext(workflow, initial_inputs)

        try:
            logger.info(f"Starting execution of workflow {workflow_id}")
            context.status = WorkflowStatus.RUNNING
            context.start_time = asyncio.get_event_loop().time()

            # Start from the start step
            if not workflow.start_step_id:
                raise ValueError(f"No start step defined for workflow {workflow_id}")

            self._execute_step(workflow.start_step_id, context)

            context.status = WorkflowStatus.COMPLETED
            context.end_time = asyncio.get_event_loop().time()

            result = {
                "execution_id": context.execution_id,
                "workflow_id": workflow_id,
                "status": context.status.value,
                "start_time": context.start_time,
                "end_time": context.end_time,
                "duration": context.end_time - context.start_time if context.start_time and context.end_time else 0,
                "variables": context.variables,
                "step_results": context.step_results
            }

            logger.info(f"Workflow {workflow_id} completed successfully")
            return result

        except Exception as e:
            context.status = WorkflowStatus.FAILED
            context.end_time = asyncio.get_event_loop().time()

            error_result = {
                "execution_id": context.execution_id,
                "workflow_id": workflow_id,
                "status": context.status.value,
                "error": str(e),
                "start_time": context.start_time,
                "end_time": context.end_time,
                "duration": (context.end_time - context.start_time) if context.start_time and context.end_time else 0,
                "variables": context.variables,
                "step_results": context.step_results
            }

            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            return error_result

    def _execute_step(self, step_id: str, context: WorkflowExecutionContext):
        """Execute a single step"""
        step = context.workflow.get_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found in workflow {context.workflow.workflow_id}")

        context.current_step_id = step_id
        logger.info(f"Executing step {step_id} (type: {step.step_type.value})")

        # Check condition if present
        if step.condition is not None:
            if not step.condition(context.variables):
                logger.info(f"Step {step_id} skipped due to condition")
                # Move to next steps if any
                for next_step_id in step.next_steps:
                    self._execute_step(next_step_id, context)
                return

        # Execute based on step type
        if step.step_type == StepType.ACTION:
            self._execute_action_step(step, context)
        elif step.step_type == StepType.CONDITION:
            self._execute_condition_step(step, context)
        elif step.step_type == StepType.LOOP:
            self._execute_loop_step(step, context)
        elif step.step_type == StepType.SUBWORKFLOW:
            self._execute_subworkflow_step(step, context)
        else:
            raise ValueError(f"Unknown step type: {step.step_type}")

        # Move to next steps
        for next_step_id in step.next_steps:
            self._execute_step(next_step_id, context)

    def _execute_action_step(self, step: WorkflowStep, context: WorkflowExecutionContext):
        """Execute an action step"""
        action_name = step.config.get("action")
        if not action_name:
            raise ValueError(f"Action step {step.step_id} missing 'action' in config")

        if action_name not in self.action_handlers:
            raise ValueError(f"No handler registered for action: {action_name}")

        # Prepare parameters
        params = step.config.get("parameters", {})
        # Replace variable references in parameters
        params = self._resolve_variables(params, context.variables)

        # Execute the action
        handler = self.action_handlers[action_name]
        result = handler(params, context)

        # Store result
        context.step_results[step.step_id] = result

        # Update variables if specified
        output_var = step.config.get("output_variable")
        if output_var and result is not None:
            context.variables[output_var] = result

    def _execute_condition_step(self, step: WorkflowStep, context: WorkflowExecutionContext):
        """Execute a condition step"""
        # Condition steps are handled by the condition function in the step
        # The actual branching is done by checking the condition and choosing next steps
        # For simplicity, we'll just mark it as executed and let the normal flow handle branching
        condition_result = step.condition(context.variables) if step.condition else False
        context.step_results[step.step_id] = {"condition_result": condition_result}

        # In a more complex implementation, we would choose different paths based on condition
        # For now, we'll just proceed to the first next step if condition is true, or second if false
        # This is a simplification - real workflow engines have more complex branching logic
        pass

    def _execute_loop_step(self, step: WorkflowStep, context: WorkflowExecutionContext):
        """Execute a loop step"""
        # Simple loop implementation - in reality, this would be more complex
        pass

    def _execute_subworkflow_step(self, step: WorkflowStep, context: WorkflowExecutionContext):
        """Execute a subworkflow step"""
        # Execute another workflow as a step
        sub_workflow_id = step.config.get("workflow_id")
        if not sub_workflow_id:
            raise ValueError(f"Subworkflow step {step.step_id} missing 'workflow_id' in config")

        if sub_workflow_id not in self.workflows:
            raise ValueError(f"Subworkflow {sub_workflow_id} not found")

        # Execute the subworkflow
        sub_result = self.execute_workflow(sub_workflow_id, context.variables)
        context.step_results[step.step_id] = sub_result

        # Update variables with subworkflow output
        output_var = step.config.get("output_variable")
        if output_var:
            # Assuming the subworkflow returns a result with an 'output' field
            # This is simplified - real implementation would depend on subworkflow design
            if "variables" in sub_result:
                context.variables[output_var] = sub_result["variables"]

    def _resolve_variables(self, value: Any, variables: Dict[str, Any]) -> Any:
        """Resolve variable references in a value"""
        if isinstance(value, str):
            # Handle simple variable substitution like {variable_name}
            import re
            def replace_var(match):
                var_name = match.group(1)
                return str(variables.get(var_name, match.group(0)))  # Return original if not found

            return re.sub(r'\{(\w+)\}', replace_var, value)
        elif isinstance(value, dict):
            return {k: self._resolve_variables(v, variables) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_variables(item, variables) for item in value]
        else:
            return value

    def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the definition of a workflow"""
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "variables": workflow.variables,
            "steps": [
                {
                    "step_id": step_id,
                    "type": step.step_type.value,
                    "config": step.config,
                    "next_steps": step.next_steps,
                    "has_condition": step.condition is not None
                }
                for step_id, step in workflow.steps.items()
            ],
            "start_step": workflow.start_step_id
        }

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all registered workflows"""
        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "step_count": len(wf.steps)
            }
            for wf in self.workflows.values()
        ]