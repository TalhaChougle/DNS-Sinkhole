"""
Demo Traffic Simulator
Sends fake DNS-like test queries via the API to populate logs for demo purposes.
Run this in a separate terminal: python simulate_traffic.py
"""

import requests
import time
import random

BASE = "http://127.0.0.1:5000"

DOMAINS = [
    # Should be BLOCKED
    "doubleclick.net",
    "ads.google.com",
    "googlesyndication.com",
    "amazon-adsystem.com",
    "malware-test.com",
    "c2server-demo.ru",
    "phishing-site.net",
    "tracking.example.com",
    "scorecardresearch.com",
    # Should be ALLOWED
    "google.com",
    "github.com",
    "stackoverflow.com",
    "python.org",
    "youtube.com",
    "wikipedia.org",
    "cloudflare.com",
    "reddit.com",
    "openai.com",
    "anthropic.com",
]

def simulate():
    print("🔄 Simulating DNS traffic... (Ctrl+C to stop)")
    count = 0
    while True:
        domain = random.choice(DOMAINS)
        try:
            r = requests.get(f"{BASE}/api/test?domain={domain}", timeout=3)
            data = r.json()
            icon = "🚫" if data["blocked"] else "✅"
            print(f"  {icon} {data['action']:7} → {domain}")
            count += 1
            if count % 10 == 0:
                print(f"\n  [{count} queries simulated]\n")
        except Exception as e:
            print(f"  ⚠️  Error: {e} — Is the Flask app running?")
        time.sleep(random.uniform(0.3, 1.2))

if __name__ == "__main__":
    simulate()
