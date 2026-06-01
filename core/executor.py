"""Task Executor - Orchestrates complex multi-step tasks"""
import asyncio
from typing import Dict
from datetime import datetime

class TaskExecutor:
    def __init__(self, agent, browser, memory):
        self.agent = agent
        self.browser = browser
        self.memory = memory
    
    async def execute(self, task: str) -> Dict:
        """Execute a complex task with full orchestration"""
        start = datetime.utcnow()
        
        # Run through agent pipeline
        result = await self.agent.run_task(task)
        
        # Log execution
        await self.memory.log_event("execution", {
            "task": task,
            "result": result,
            "start": start.isoformat(),
            "end": datetime.utcnow().isoformat()
        })
        
        return {
            "task": task,
            "result": result,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
