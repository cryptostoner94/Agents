#!/usr/bin/env python3
"""
NEXUS OMEGA - Smoke Test Suite
Tests that all core functionality is working.
"""

import sys
import json
import subprocess
import time
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30

def log(msg, status="INFO"):
    symbols = {"INFO": "ℹ", "PASS": "✓", "FAIL": "✗", "WARN": "⚠"}
    print(f"  [{symbols.get(status, '•')}] {msg}")

def test_imports():
    """Test that all Python modules can be imported."""
    log("Testing Python module imports...")
    try:
        from core.agent_loop import run_agent
        from core.browser_operator import extract_page, extract_urls, PLAYWRIGHT
        from core.code_sandbox import run_python
        from core.shell_runner import run_shell
        from core.memory import log_event, recent
        from core.policy import check_text, shell_allowed
        log(f"All modules imported. Playwright available: {PLAYWRIGHT}", "PASS")
        return True
    except ImportError as e:
        log(f"Import error: {e}", "FAIL")
        return False

def test_api_health():
    """Test the /health endpoint."""
    log("Testing /health endpoint...")
    try:
        import urllib.request
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data.get("ok"):
                log(f"Health OK - Uptime: {data.get('uptime')}s, Playwright: {data.get('playwright')}", "PASS")
                return True
        log("Health endpoint returned non-ok response", "FAIL")
        return False
    except Exception as e:
        log(f"Health check failed: {e}", "FAIL")
        return False

def test_api_data():
    """Test the /api/data endpoint."""
    log("Testing /api/data endpoint...")
    try:
        import urllib.request
        req = urllib.request.Request(f"{BASE_URL}/api/data")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data.get("ok"):
                log(f"Routes available: {len(data.get('routes', []))}", "PASS")
                return True
        log("Data endpoint returned non-ok response", "FAIL")
        return False
    except Exception as e:
        log(f"Data check failed: {e}", "FAIL")
        return False

def test_api_browser():
    """Test the /api/browser endpoint with a simple URL."""
    log("Testing /api/browser endpoint...")
    try:
        import urllib.request
        payload = json.dumps({"command": "extract https://httpbin.org/html"}).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/browser", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            if data.get("ok") or "error" in data:
                log(f"Browser API responded: {data.get('ok', False)} - {data.get('error', data.get('results', [{}])[0].get('title', 'OK'))}", "PASS" if data.get("ok") else "WARN")
                return True
        log("Browser endpoint failed", "FAIL")
        return False
    except Exception as e:
        log(f"Browser API failed (may need playwright): {e}", "WARN")
        return False

def test_api_chat():
    """Test the /api/chat endpoint with a simple message."""
    log("Testing /api/chat endpoint...")
    try:
        import urllib.request
        payload = json.dumps({"message": "hello"}).encode()
        req = urllib.request.Request(f"{BASE_URL}/api/chat", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            if data.get("ok"):
                log(f"Chat API OK - Mode: {data.get('mode', 'unknown')}", "PASS")
                return True
        log(f"Chat returned: {data}", "FAIL")
        return False
    except Exception as e:
        log(f"Chat API failed: {e}", "FAIL")
        return False

def test_api_artifacts():
    """Test the /api/artifacts endpoint."""
    log("Testing /api/artifacts endpoint...")
    try:
        import urllib.request
        req = urllib.request.Request(f"{BASE_URL}/api/artifacts")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data.get("ok"):
                log(f"Artifacts API OK - {data.get('count', 0)} files", "PASS")
                return True
        log("Artifacts endpoint returned non-ok response", "FAIL")
        return False
    except Exception as e:
        log(f"Artifacts check failed: {e}", "FAIL")
        return False

def test_html_pages():
    """Test that HTML pages are served correctly."""
    log("Testing HTML page serving...")
    pages = ["/", "/app", "/chat"]
    all_ok = True
    for page in pages:
        try:
            import urllib.request
            req = urllib.request.Request(f"{BASE_URL}{page}")
            with urllib.request.urlopen(req, timeout=10) as r:
                content = r.read().decode()
                if "NEXUS" in content or "nexus" in content.lower():
                    log(f"{page} OK", "PASS")
                else:
                    log(f"{page} - content check failed", "WARN")
        except Exception as e:
            log(f"{page} - {e}", "FAIL")
            all_ok = False
    return all_ok

def test_code_sandbox():
    """Test the code sandbox."""
    log("Testing code sandbox...")
    try:
        from core.code_sandbox import run_python
        result = run_python("print('sandbox_test_ok')")
        if result.get("ok") and "sandbox_test_ok" in result.get("stdout", ""):
            log("Code sandbox OK", "PASS")
            return True
        log(f"Code sandbox unexpected result: {result}", "FAIL")
        return False
    except Exception as e:
        log(f"Code sandbox failed: {e}", "FAIL")
        return False

def test_policy():
    """Test the policy module."""
    log("Testing policy module...")
    try:
        from core.policy import check_text, shell_allowed
        
        # Test blocked terms
        allowed, _ = check_text("hello world")
        if not allowed:
            log("Policy check failed for valid text", "FAIL")
            return False
        
        allowed, reason = check_text("wallet seed phrase private key")
        if allowed:
            log("Policy check failed - blocked text allowed", "FAIL")
            return False
        else:
            log(f"Blocked text correctly rejected: {reason}", "PASS")
        
        # Test shell allowlist
        if shell_allowed("pwd"):
            log("Shell allowlist OK", "PASS")
        else:
            log("Shell allowlist broken", "FAIL")
            return False
        
        return True
    except Exception as e:
        log(f"Policy test failed: {e}", "FAIL")
        return False

def main():
    print("")
    print("=" * 50)
    print("  NEXUS OMEGA - Smoke Test Suite")
    print("=" * 50)
    print("")
    
    # Check if server is running
    log("Checking if server is running...")
    try:
        import urllib.request
        req = urllib.request.Request(f"{BASE_URL}/health")
        urllib.request.urlopen(req, timeout=5)
        log("Server is running", "PASS")
    except Exception:
        log(f"Server not running at {BASE_URL}", "FAIL")
        log("Start server with: bash install.sh (or python3 -m uvicorn api_main:app --port 8000)", "WARN")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Module Imports", test_imports()))
    results.append(("Health Endpoint", test_api_health()))
    results.append(("Data Endpoint", test_api_data()))
    results.append(("Browser API", test_api_browser()))
    results.append(("Chat API", test_api_chat()))
    results.append(("Artifacts API", test_api_artifacts()))
    results.append(("HTML Pages", test_html_pages()))
    results.append(("Code Sandbox", test_code_sandbox()))
    results.append(("Policy Module", test_policy()))
    
    # Summary
    print("")
    print("=" * 50)
    print("  Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {name}")
    
    print("")
    print(f"  Total: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed > 0:
        log(f"{failed} test(s) failed", "FAIL")
        sys.exit(1)
    else:
        log("All tests passed!", "PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()