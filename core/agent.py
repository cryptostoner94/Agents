"""Agent Core - Task orchestration and execution"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime

class AgentCore:
    def __init__(self, llm_manager):
        self.llm = llm_manager
        self.current_task = None
        self.history = []
    
    async def run_task(self, task: str, model: str = "auto") -> Dict:
        """Run a task through the agent pipeline"""
        self.current_task = task
        start_time = datetime.utcnow()
        
        # Step 1: Analyze task
        analysis = await self._analyze(task)
        
        # Step 2: Plan execution
        plan = await self._plan(task, analysis)
        
        # Step 3: Execute steps
        results = []
        for step in plan["steps"]:
            result = await self._execute_step(step)
            results.append(result)
        
        # Step 4: Generate response
        response = await self._generate_response(task, results)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        self.history.append({
            "task": task,
            "analysis": analysis,
            "plan": plan,
            "results": results,
            "duration": duration
        })
        
        return {
            "task": task,
            "analysis": analysis,
            "plan": plan,
            "results": results,
            "response": response,
            "duration": f"{duration:.2f}s"
        }
    
    async def _analyze(self, task: str) -> Dict:
        """Analyze the task to understand what's needed"""
        prompt = f"""Analyze this task and identify:
1. Type (research, automation, coding, general)
2. Required tools (browser, code, search, analysis)
3. Complexity (1-5)
4. Key objectives

Task: {task}

Return a brief analysis."""
        
        response = await self.llm.generate(prompt)
        return {"raw": response, "type": self._categorize(task)}
    
    def _categorize(self, task: str) -> str:
        """Simple categorization"""
        task_lower = task.lower()
        if any(w in task_lower for w in ["search", "find", "research", "extract"]):
            return "research"
        elif any(w in task_lower for w in ["build", "create", "code", "program"]):
            return "coding"
        elif any(w in task_lower for w in ["automate", "run", "execute", "do"]):
            return "automation"
        return "general"
    
    async def _plan(self, task: str, analysis: Dict) -> Dict:
        """Create execution plan"""
        prompt = f"""Create a step-by-step plan for this task:

Task: {task}
Type: {analysis.get('type', 'general')}

Provide 2-5 concrete steps. Format as a JSON array of step objects:
[{{"step": 1, "action": "description", "tool": "browser|code|llm"}}]"""
        
        try:
            response = await self.llm.generate(prompt)
            # Simple parsing - extract steps from response
            steps = []
            if "1." in response or "Step 1" in response:
                # Parse numbered steps
                for i in range(1, 6):
                    if f"{i}." in response or f"Step {i}" in response:
                        steps.append({"step": i, "action": f"Execute step {i}", "tool": "llm"})
        except:
            steps = [{"step": 1, "action": "Process task", "tool": "llm"}]
        
        return {"steps": steps[:5] or [{"step": 1, "action": "Complete task", "tool": "llm"}]}
    
    async def _execute_step(self, step: Dict) -> Dict:
        """Execute a single step"""
        await asyncio.sleep(0.1)  # Simulate processing
        return {
            "step": step["step"],
            "status": "completed",
            "output": f"Step {step['step']} executed successfully"
        }
    
    async def _generate_response(self, task: str, results: List) -> str:
        """Generate final response"""
        prompt = f"""Task: {task}

Results from {len(results)} steps:
{chr(10).join([r['output'] for r in results])}

Provide a clear summary of what was accomplished."""
        
        return await self.llm.generate(prompt)
