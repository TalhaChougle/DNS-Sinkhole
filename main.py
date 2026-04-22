"""
Main entry point.
Starts the DNS sinkhole server (port 5353 for local dev) and Flask dashboard together.
"""

import threading
import sys
import os

# ── Patch DNS port for local dev (no sudo needed) ──────────────────────────
# Port 53 requires root. For local dev we use 5353.
# In Docker / production, we run as root on port 53.
IS_DOCKER = os.path.exists("/.dockerenv")
DNS_PORT_OVERRIDE = 53

import dns_server
dns_server.DNS_PORT = DNS_PORT_OVERRIDE


def run_dns():
    try:
        dns_server.start_dns_server()
    except PermissionError:
        print("\n❌ Cannot bind to DNS port. On Linux/Mac run with: sudo python main.py")
        print("   Or just use the dashboard + test tool without the live DNS server.\n")


def run_flask():
    from app import app
    from database import init_db
    init_db()
    print("🌐 Dashboard → http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    print("=" * 55)
    print("  🛡️  DNS Sinkhole — Starting up")
    print("=" * 55)
    print(f"  DNS Server  → 127.0.0.1:{DNS_PORT_OVERRIDE}")
    print(f"  Dashboard   → http://127.0.0.1:5000")
    print("=" * 55)

    # Start DNS server in background thread
    dns_thread = threading.Thread(target=run_dns, daemon=True, name="DNSServer")
    dns_thread.start()

    # Flask in main thread
    run_flask()
