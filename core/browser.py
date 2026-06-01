"""Browser Automation - Playwright powered web scraping"""
import os
import asyncio
from typing import Optional, Dict

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class BrowserOperator:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self._initialized = False
    
    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE
    
    async def _ensure_browser(self):
        """Initialize browser if not already done"""
        if not self._initialized and PLAYWRIGHT_AVAILABLE:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=True)
                self._initialized = True
            except Exception as e:
                print(f"Browser launch failed: {e}")
                self._initialized = True  # Don't retry
    
    async def extract(self, url: str, instructions: str = "") -> Dict:
        """Extract content from a URL"""
        if not PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright not installed", "content": ""}
        
        await self._ensure_browser()
        if not self.browser:
            return {"error": "Browser not available", "content": ""}
        
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if instructions:
                # Find elements matching instructions
                content = await page.inner_text("body")
            else:
                content = await page.inner_text("body")
            
            await page.close()
            
            return {
                "url": url,
                "content": content[:5000],  # Limit content size
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "content": "", "success": False}
    
    async def interact(self, url: str, actions: str) -> Dict:
        """Interact with a webpage (click, type, etc.)"""
        if not PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright not installed"}
        
        await self._ensure_browser()
        if not self.browser:
            return {"error": "Browser not available"}
        
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            
            # Parse actions (simple implementation)
            action_lines = actions.split("\n")
            for line in action_lines:
                if "click" in line.lower():
                    selector = line.replace("click", "").strip()
                    await page.click(selector)
                elif "type" in line.lower():
                    parts = line.replace("type", "").split("->")
                    if len(parts) == 2:
                        await page.fill(parts[0].strip(), parts[1].strip())
            
            # Get final page state
            content = await page.inner_text("body")
            await page.close()
            
            return {"success": True, "content": content[:5000]}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def close(self):
        """Close browser resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
