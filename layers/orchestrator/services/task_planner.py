"""
Task Planner - Decomposition and Parallelization Detection

Expands batch operations into individual steps and detects
opportunities for parallel execution.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
import glob
import uuid

from schemas.models import Step, WorkspaceContext


logger = logging.getLogger("orchestrator.planner")


class TaskPlanner:
    """
    Task decomposition and parallelization detection.
    
    Expands high-level batch operations into concrete parallel steps.
    """
    
    async def expand_batch(
        self,
        batch_step: Step,
        workspace_context: Optional[WorkspaceContext] = None,
    ) -> List[Step]:
        """
        Expand a batch step into individual parallelizable steps.
        
        Args:
            batch_step: Step with tool="batch" and pattern/operation params
            workspace_context: Current workspace for path resolution
            
        Returns:
            List of individual Step objects ready for parallel execution
        """
        params = batch_step.params
        pattern = params.get("pattern", "*")
        operation = params.get("operation", "read_file")
        batch_id = batch_step.batch_id or f"batch_{uuid.uuid4().hex[:8]}"
        
        # Resolve workspace root
        workspace_root = "."
        if workspace_context:
            workspace_root = workspace_context.cwd
        
        # Find matching files
        search_pattern = os.path.join(workspace_root, "**", pattern)
        matching_files = glob.glob(search_pattern, recursive=True)
        
        # Limit batch size for safety
        # DEV MODE: Higher limit for testing
        max_batch_size = 100
        if workspace_context:
            max_batch_size = min(
                workspace_context.max_parallel_tasks * 10,
                500  # DEV MODE: Higher hard limit
            )
        
        if len(matching_files) > max_batch_size:
            logger.warning(
                f"Batch size {len(matching_files)} exceeds limit {max_batch_size}, "
                f"truncating to first {max_batch_size} files"
            )
            matching_files = matching_files[:max_batch_size]
        
        # Generate individual steps
        steps = []
        for i, file_path in enumerate(matching_files):
            step = Step(
                step_id=f"{batch_id}_{i}",
                tool=operation,
                params={"path": file_path},
                batch_id=batch_id,
                reasoning=f"Part of batch operation: {operation} on {pattern}",
            )
            steps.append(step)
        
        logger.info(f"Expanded batch to {len(steps)} steps")
        return steps
    
    def detect_parallelization(
        self,
        task: str,
        workspace_context: Optional[WorkspaceContext] = None,
    ) -> bool:
        """
        Detect if a task can be parallelized.
        
        Looks for patterns like:
        - "all files", "every file", "each file"
        - "multiple", "batch", "parallel"
        - File glob patterns (*.py, *.ts, etc.)
        
        Args:
            task: User's task description
            workspace_context: For checking if parallel is enabled
            
        Returns:
            True if task appears parallelizable
        """
        # Check if parallel execution is allowed
        if workspace_context and not workspace_context.parallel_enabled:
            return False
        
        # Parallelization decision delegated to LLM (reasoning engine)
        # NO hardcoded keyword shortcuts - let the model analyze task semantics
        # The orchestrator will decide based on actual task analysis, not word matching
        # For now: default to sequential execution (safest)
        return False
    
    def estimate_task_complexity(self, task: str) -> int:
        """
        Estimate task complexity (number of steps).
        
        DEPRECATED: This should not use keyword heuristics.
        
        Complexity estimation is now delegated to:
        1. LLM reasoning (generate_task_plan returns actual steps)
        2. Token counting on the task description
        3. Never hardcoded keyword analysis
        
        Returns:
            Estimated number of steps (1-10)
        """
        # Safe default: estimate based on character length only (no keywords)
        # Actual complexity determined by reasoning engine's task plan
        char_count = len(task)
        if char_count < 50:
            return 1
        elif char_count < 200:
            return 2
        elif char_count < 500:
            return 3
        else:
            return min(4 + (char_count // 500), 10)
