#!/usr/bin/env python3
"""
NEXUS OMEGA - GitHub Webhook Receiver
Listens for push events and triggers auto-deployment.

Setup:
1. Add this to your GitHub repo webhook: https://your-ec2-ip:8443/webhook
2. Set secret: your-webhook-secret
3. Events: Push

Environment variables:
- AGENTS_DEPLOY_SCRIPT: Path to deploy script (default: /home/ubuntu/Agents/deploy/github-auto-deploy.sh)
- AGENTS_WEBHOOK_SECRET: Secret to verify webhook signature
- NEXUS_DEPLOY_KEY: GitHub PAT for private repos
"""

import os
import json
import hashlib
import hmac
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Configuration
DEPLOY_SCRIPT = os.getenv("AGENTS_DEPLOY_SCRIPT", "/home/ubuntu/Agents/deploy/github-auto-deploy.sh")
WEBHOOK_SECRET = os.getenv("AGENTS_WEBHOOK_SECRET", "")
WEBHOOK_PORT = int(os.getenv("AGENTS_WEBHOOK_PORT", "8443"))
LOG_FILE = "/var/log/nexus-webhook.log"

def log(msg):
    """Log to file and stdout."""
    timestamp = subprocess.getoutput("date '+%Y-%m-%d %H:%M:%S'").strip()
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def verify_signature(payload, signature):
    """Verify GitHub webhook signature."""
    if not WEBHOOK_SECRET:
        return True  # Skip verification if no secret set
    if not signature:
        return False
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def trigger_deployment(event_type="push"):
    """Trigger deployment in background thread."""
    def run():
        log(f"Triggering deployment (event: {event_type})...")
        try:
            # Set environment for deployment
            env = os.environ.copy()
            # Get GitHub event info
            env["NEXUS_DEPLOY_EVENT"] = event_type
            env["NEXUS_DEPLOY_TIMESTAMP"] = subprocess.getoutput("date -u '+%Y-%m-%dT%H:%M:%SZ'").strip()
            
            # Run deployment script
            result = subprocess.run(
                ["/bin/bash", DEPLOY_SCRIPT],
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                log("Deployment completed successfully")
            else:
                log(f"Deployment failed: {result.stderr[:500]}")
        except subprocess.TimeoutExpired:
            log("Deployment timed out (5 minute limit)")
        except Exception as e:
            log(f"Deployment error: {e}")
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    log("Deployment triggered in background")

def handle_push_event(payload):
    """Handle GitHub push event."""
    ref = payload.get("ref", "")
    repository = payload.get("repository", {}).get("full_name", "unknown")
    commits = payload.get("commits", [])
    
    log(f"Push to {ref} in {repository}")
    if commits:
        for commit in commits[:3]:
            log(f"  - {commit.get('id', '')[:8]}: {commit.get('message', '')[:80]}")
    
    trigger_deployment("push")

class WebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming webhook requests."""
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        pass  # We handle logging ourselves
    
    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"NEXUS Webhook Server OK\n")
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
<html><head><title>NEXUS Webhook</title></head>
<body>
<h1>NEXUS OMEGA Webhook Receiver</h1>
<p>Status: Active</p>
<p>Waiting for GitHub push events...</p>
</body></html>
""")
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests (webhook events)."""
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return
        
        # Read payload
        content_length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(content_length)
        
        # Get signature
        signature = self.headers.get("X-Hub-Signature-256", "")
        
        # Verify signature
        if not verify_signature(payload, signature):
            log("Invalid webhook signature - rejecting")
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid signature"}')
            return
        
        # Parse event
        event = self.headers.get("X-GitHub-Event", "push")
        log(f"Received GitHub event: {event}")
        
        try:
            data = json.loads(payload.decode())
        except json.JSONDecodeError:
            log("Invalid JSON payload")
            self.send_response(400)
            self.end_headers()
            return
        
        # Handle different events
        if event == "push":
            handle_push_event(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "deployment triggered"}')
        elif event == "ping":
            # GitHub sends ping on webhook setup
            log("Ping received - webhook configured correctly")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"message": "Webhook configured"}')
        else:
            log(f"Ignoring event type: {event}")
            self.send_response(200)
            self.end_headers()
    
    def do_HEAD(self):
        """Handle HEAD requests."""
        self.send_response(200)
        self.end_headers()

def main():
    """Start webhook server."""
    log(f"NEXUS Webhook Server starting on port {WEBHOOK_PORT}")
    
    server = HTTPServer(("0.0.0.0", WEBHOOK_PORT), WebhookHandler)
    log(f"Listening for GitHub webhooks on :{WEBHOOK_PORT}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Shutting down...")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()