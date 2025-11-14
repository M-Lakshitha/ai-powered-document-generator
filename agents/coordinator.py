"""
Agent Coordinator - Orchestrates all agents with parallel execution
"""
from typing import Dict, List
from backend.services.task_scheduler import TaskScheduler, AgentTask, AgentStage
from agents.code_analyst import CodeAnalystAgent
from agents.api_documenter import APIDocumenterAgent
from agents.readme_creator import READMECreatorAgent

class AgentCoordinator:
    """
    Coordinates all agents with optimal parallel execution
    
    Execution flow:
    1. CodeAnalyst runs first (dependency for others)
    2. APIDocumenter and READMECreator run in parallel
    3. Results are collected and saved
    """
    
    def __init__(self):
        self.analyst = CodeAnalystAgent()
        self.api_documenter = APIDocumenterAgent()
        self.readme_creator = READMECreatorAgent()
        self.scheduler = TaskScheduler(max_parallel=3)
    
    async def coordinate(self, input_data: Dict) -> Dict:
        """
        Coordinate all agents to generate documentation
        
        Args:
            input_data: {
                "chunks": List of file chunks,
                "project_name": Project name,
                "session_id": Session ID
            }
        
        Returns:
            Combined results from all agents
        """
        
        print("🤖 Starting agent coordination...")
        print(f"📊 Processing {len(input_data.get('chunks', []))} chunk(s)")
        
        # Define tasks with dependencies
        tasks = [
            # Task 1: Code Analysis (no dependencies - runs first)
            AgentTask(
                stage=AgentStage.ANALYSIS,
                agent_func=self._wrap_agent(self.analyst),
                dependencies=[],
                input_data=input_data,
                priority=10
            ),
            
            # Task 2: API Documentation (depends on analysis)
            AgentTask(
                stage=AgentStage.API_DOCS,
                agent_func=self._wrap_agent(self.api_documenter),
                dependencies=[AgentStage.ANALYSIS],
                input_data=input_data,
                priority=5
            ),
            
            # Task 3: README Creation (depends on analysis, runs parallel with API docs)
            AgentTask(
                stage=AgentStage.README,
                agent_func=self._wrap_agent(self.readme_creator),
                dependencies=[AgentStage.ANALYSIS],
                input_data=input_data,
                priority=5
            )
        ]
        
        # Execute all tasks with optimal scheduling
        results = await self.scheduler.schedule_and_execute(tasks)
        
        print("✅ All agents completed successfully!")
        
        return results
    
    def _wrap_agent(self, agent):
        """Wrap agent execute method for scheduler"""
        async def wrapped(input_data: Dict, context: Dict):
            return await agent.execute(input_data, context)
        return wrapped
