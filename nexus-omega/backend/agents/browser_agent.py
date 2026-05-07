import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA = Path('/home/cryptostoner94/nexus-singularity')
STATE = DATA / 'browser_agent_state.json'
SCREENS = DATA / 'browser_screens'

BLOCK = ['seed phrase', 'private key', 'kyc', 'passport', 'ssn',
         'payment', 'credit card', 'bank', 'wallet', 'captcha']


def ensure_dirs():
    DATA.mkdir(parents=True, exist_ok=True)
    SCREENS.mkdir(parents=True, exist_ok=True)


def save(d):
    ensure_dirs()
    STATE.write_text(json.dumps(d, indent=2))


def run_natural(text):
    low = text.lower()
    if any(x in low for x in BLOCK):
        return {'status': 'BLOCKED', 'reason': 'sensitive/risky task detected'}
    url = None
    for part in text.split():
        if part.startswith('http://') or part.startswith('https://'):
            url = part
            break
    if not url:
        return {'status': 'NEEDS_URL', 'example': 'extract https://example.com'}
    ensure_dirs()
    run_id = 'browser_' + str(int(time.time()))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        title = page.title()
        body = page.locator('body').inner_text(timeout=60000)[:5000]
        shot = SCREENS / f'{run_id}.png'
        page.screenshot(path=str(shot), full_page=True)
        browser.close()
    out = {
        'id': run_id,
        'status': 'DONE',
        'url': url,
        'title': title,
        'text_preview': body,
        'screenshot': str(shot)
    }
    save(out)
    return out


def run_status():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            pass
    return {'status': 'READY', 'last_run': None}


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'status'
    task = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
    if mode == 'natural':
        if not task:
            print(json.dumps({'status': 'NEEDS_TASK'}, indent=2))
        else:
            print(json.dumps(run_natural(task), indent=2))
    else:
        print(json.dumps(run_status(), indent=2))
