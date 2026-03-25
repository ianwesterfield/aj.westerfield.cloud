"""
Parallel Executor - Batch Execution with Partial Failure Handling

Executes multiple steps concurrently using asyncio.gather.
Individual failures do not cascade - sibling tasks continue.

Uses the shared tool_dispatcher module for consistent tool execution
across both the orchestrator API and batch operations.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from schemas.models import (
    Step,
    StepResult,
    StepStatus,
    BatchResult,
    ErrorMetadata,
    ErrorType,
    WorkspaceContext,
)

from services.bash_dispatcher import dispatch_tool  # "All You Need is Bash" - simplified tool dispatch


logger = logging.getLogger("orchestrator.executor")


class ParallelExecutor:
    """
    Parallel batch executor with partial failure handling.
    
    Uses asyncio.gather to execute steps concurrently.
    Failures are captured but don't stop sibling executions.
    
    Delegates tool execution to the shared tool_dispatcher module.
    """
    
    def __init__(self):
        # No local handlers needed - uses shared tool_dispatcher
        pass
    
    async def execute_batch(
        self,
        steps: List[Step],
        batch_id: str,
        workspace_context: Optional[WorkspaceContext] = None,
    ) -> BatchResult:
        """
        Execute a batch of steps in parallel.
        
        Args:
            steps: List of steps to execute
            batch_id: Batch identifier for logging
            workspace_context: Execution context (limits, permissions)
            
        Returns:
            BatchResult with successful and failed step lists
        """
        start_time = time.time()
        
        # Determine concurrency limit
        max_concurrent = 4
        if workspace_context:
            max_concurrent = workspace_context.max_parallel_tasks
        
        logger.info(f"Executing batch {batch_id}: {len(steps)} steps, max {max_concurrent} concurrent")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(step: Step) -> tuple[Step, StepResult | Exception]:
            async with semaphore:
                try:
                    result = await self._execute_single_step(step, workspace_context)
                    return (step, result)
                except Exception as e:
                    return (step, e)
        
        # Execute all steps concurrently
        tasks = [execute_with_semaphore(step) for step in steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        successful = []
        failed = []
        
        for item in results:
            if isinstance(item, Exception):
                # asyncio.gather caught an exception
                logger.error(f"Batch task exception: {item}")
                continue
            
            step, result = item
            
            if isinstance(result, Exception):
                # Step execution raised an exception
                error_meta = self._classify_error(step, result)
                failed.append(error_meta)
            elif isinstance(result, StepResult):
                if result.status == StepStatus.SUCCESS:
                    successful.append(result)
                else:
                    error_meta = ErrorMetadata(
                        step_id=result.step_id,
                        error=result.error or "Unknown error",
                        error_type=ErrorType.EXECUTION_ERROR,
                        recoverable=True,
                    )
                    failed.append(error_meta)
        
        duration = time.time() - start_time
        
        return BatchResult(
            batch_id=batch_id,
            successful=successful,
            failed=failed,
            duration=duration,
        )
    
    async def _execute_single_step(
        self,
        step: Step,
        workspace_context: Optional[WorkspaceContext] = None,
    ) -> StepResult:
        """
        Execute a single step DIRECTLY via local handlers.
        
        No HTTP overhead - handlers are instantiated locally.
        
        Args:
            step: Step to execute
            workspace_context: Execution context
            
        Returns:
            StepResult with status and output
        """
        start_time = time.time()
        tool = step.tool
        params = step.params
        
        try:
            # Route to appropriate handler based on tool name
            result = await self._dispatch_tool(tool, params, workspace_context)
            execution_time = time.time() - start_time
            
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.SUCCESS if result.get("success") else StepStatus.FAILED,
                output=result.get("output") or result.get("stdout") or result.get("data"),
                error=result.get("error") or result.get("stderr"),
                execution_time=execution_time,
            )
            
        except asyncio.TimeoutError:
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                error="Execution timeout",
                execution_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"Step execution error: {e}")
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time,
            )
    
    async def _dispatch_tool(
        self,
        tool: str,
        params: Dict[str, Any],
        workspace_context: Optional[WorkspaceContext] = None,
    ) -> Dict[str, Any]:
        """Delegate to shared tool dispatcher."""
        return await dispatch_tool(tool, params, workspace_context)
    
    def _classify_error(self, step: Step, error: Exception) -> ErrorMetadata:
        """Classify an exception into an ErrorMetadata object."""
        error_str = str(error)
        
        # Classify error type
        if "timeout" in error_str.lower():
            error_type = ErrorType.TIMEOUT
            recoverable = True
        elif "permission" in error_str.lower():
            error_type = ErrorType.PERMISSION_DENIED
            recoverable = False
        elif "sandbox" in error_str.lower():
            error_type = ErrorType.SANDBOX_VIOLATION
            recoverable = False
        elif "resource" in error_str.lower() or "memory" in error_str.lower():
            error_type = ErrorType.RESOURCE_LIMIT
            recoverable = True
        else:
            error_type = ErrorType.EXECUTION_ERROR
            recoverable = True
        
        return ErrorMetadata(
            step_id=step.step_id,
            error=error_str[:200],  # Truncate long errors
            error_type=error_type,
            recoverable=recoverable,
        )
    
    async def close(self):
        """Cleanup (no-op, no HTTP client to close)."""
        pass
