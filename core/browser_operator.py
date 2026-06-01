import re, time, uuid, os
from pathlib import Path
 
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT = True
except Exception:
    PLAYWRIGHT = False

BASE = Path(os.getenv("NEXUS_BASE", "./data"))
SCR = BASE / "browser_screens"
SCR.mkdir(parents=True, exist_ok=True)
 
def extract_urls(text):
    return re.findall(r'''https?://[^\s"'<>]+''', text or "")
 
async def extract_page(url: str):
    job = f"browser_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    shot = SCR / f"{job}.png"
    if not PLAYWRIGHT:
        return {"ok": False, "error": "playwright unavailable"}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
            page = await browser.new_page(viewport={"width":1365,"height":900})
            response = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            await page.wait_for_timeout(800)
            title = await page.title()
            try:
                text = await page.locator("body").inner_text(timeout=8000)
            except Exception:
                text = ""
            try:
                links = await page.evaluate("""() => Array.from(document.querySelectorAll('a')).slice(0,40).map(a => ({text:(a.innerText||'').trim().slice(0,120),href:a.href}))""")
            except Exception:
                links = []
            await page.screenshot(path=str(shot), full_page=True)
            final_url = page.url
            await browser.close()
            return {"ok": True, "id": job, "url": final_url, "requested_url": url, "status_code": response.status if response else None, "title": title, "text_preview": re.sub(r"\s+"," ",text).strip()[:12000], "links": links, "screenshot": str(shot)}
    except Exception as e:
        return {"ok": False, "url": url, "error": str(e)}
 
async def click_by_text(url: str, text: str):
    return await extract_page(url)
