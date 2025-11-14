

"""
Parallel task scheduler for agent coordination
"""
import asyncio
from typing import List, Dict, Callable
from dataclasses import dataclass
from enum import Enum

class AgentStage(Enum):
    """Agent processing stages"""
    ANALYSIS = "analysis"
    API_DOCS = "api_documentation"
    README = "readme_creation"
    ARCHITECTURE = "architecture_docs"

@dataclass
class AgentTask:
    """Represents a task for an agent"""
    stage: AgentStage
    agent_func: Callable
    dependencies: List[AgentStage]
    input_data: Dict
    priority: int = 0

class TaskScheduler:
    """
    Schedules and executes agent tasks in parallel
    Respects dependencies and maximizes LLM utilization
    """
    
    def __init__(self, max_parallel: int = 3):
        self.max_parallel = max_parallel
        self.completed_stages = set()
        self.failed_stages = set()  # ✅ NEW: Track failed stages to prevent infinite loops
        self.results = {}
        self.semaphore = asyncio.Semaphore(max_parallel)
    
    async def execute_task(self, task: AgentTask) -> Dict:
        """Execute a single agent task"""
        async with self.semaphore:
            print(f"🔄 Starting: {task.stage.value}")
            try:
                # ✅ FIXED: Check dependencies with timeout
                await self._wait_for_dependencies(task.dependencies)
                
                # Execute agent function
                result = await task.agent_func(task.input_data, self.results)
                
                # Store result
                self.results[task.stage] = result
                self.completed_stages.add(task.stage)
                print(f"✅ Completed: {task.stage.value}")
                return result
                
            except Exception as e:
                print(f"❌ Failed: {task.stage.value} - {str(e)}")
                self.failed_stages.add(task.stage)  # ✅ NEW: Mark as failed
                raise
    
    async def _wait_for_dependencies(self, dependencies: List[AgentStage]):
        """
        Wait for dependent tasks to complete
        ✅ FIXED: Added timeout and failure detection to prevent infinite loops
        """
        if not dependencies:
            return  # No dependencies, proceed immediately
        
        # ✅ NEW: 5 minute timeout to prevent infinite waiting
        start_time = asyncio.get_event_loop().time()
        timeout = 300  # 5 minutes
        
        while not all(dep in self.completed_stages for dep in dependencies):
            # ✅ NEW: Check if any dependency failed
            failed_deps = [dep for dep in dependencies if dep in self.failed_stages]
            if failed_deps:
                raise Exception(f"Dependencies failed: {[d.value for d in failed_deps]}")
            
            # ✅ NEW: Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                missing = [dep.value for dep in dependencies if dep not in self.completed_stages]
                raise asyncio.TimeoutError(
                    f"Timeout ({timeout}s) waiting for dependencies: {missing}"
                )
            
            await asyncio.sleep(0.1)
        
        print(f"✅ All dependencies satisfied for current task")
    
    async def schedule_and_execute(self, tasks: List[AgentTask]) -> Dict:
        """
        Schedule and execute tasks with optimal parallelization
        """
        print(f"📋 Scheduling {len(tasks)} tasks...")
        
        # Sort by priority and dependencies
        sorted_tasks = sorted(tasks, key=lambda t: (len(t.dependencies), -t.priority))
        
        print("📊 Execution order:")
        for i, task in enumerate(sorted_tasks, 1):
            deps = [d.value for d in task.dependencies] if task.dependencies else ["None"]
            print(f"  {i}. {task.stage.value} (depends on: {deps})")
        
        # Create task coroutines
        task_coros = [self.execute_task(task) for task in sorted_tasks]
        
        # Execute all tasks (asyncio.gather handles parallelization)
        results = await asyncio.gather(*task_coros, return_exceptions=True)
        
        # Check for failures
        failures = [r for r in results if isinstance(r, Exception)]
        if failures:
            error_msgs = "\n".join([f"  - {type(f).__name__}: {str(f)}" for f in failures])
            print(f"❌ Task execution failed:\n{error_msgs}")
            raise Exception(f"Task execution failed: {failures[0]}")
        
        print(f"✅ All {len(tasks)} tasks completed successfully!")
        return self.results