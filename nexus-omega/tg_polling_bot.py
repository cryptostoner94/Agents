import os, time, requests
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API = "http://127.0.0.1:8000/api/agent"
def main():
    if not TOKEN:
        print("missing TELEGRAM_BOT_TOKEN"); return
    offset = 0
    while True:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", params={"offset":offset,"timeout":30}).json()
        for u in r.get("result",[]):
            offset = u["update_id"] + 1
            msg = u.get("message",{}); chat = msg.get("chat",{}).get("id"); text = msg.get("text","")
            if not chat or not text: continue
            if text.startswith("/status"):
                out = requests.get("http://127.0.0.1:8000/health").text
            elif text.startswith("/agent"):
                q = text.replace("/agent","",1).strip(); out = requests.post(API,json={"message":q}).text[:3500]
            else:
                out = "Commands: /status, /agent <objective>"
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id":chat,"text":out[:3900]})
        time.sleep(1)
if __name__ == "__main__": main()
