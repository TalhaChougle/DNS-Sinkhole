# 🛡️ DNS Sinkhole

> A Python-based DNS sinkhole that intercepts real network traffic, blocks malicious domains before any connection is made, and provides a real-time admin dashboard for monitoring and management.

**🔴 [Live Demo](https://dns-sinkhole.netlify.app)** &nbsp;|&nbsp; **⭐ Star this repo if you find it useful**

![DNS Sinkhole Dashboard](https://github.com/user-attachments/assets/24562426-47f0-4e2d-8954-e8cb1cfc09fa)
---

## 🧠 What is a DNS Sinkhole?

Every time you visit a website, your device first asks a DNS server *"what's the IP address for this site?"* — this is called a **DNS query**.

A DNS Sinkhole sits in the middle of that process. It intercepts every DNS query and checks it against a blocklist of known malicious, ad, and tracking domains. If the domain is on the blocklist, it returns a **fake IP (0.0.0.0)** so your device never connects. If it's safe, it forwards the query to Google DNS and returns the real IP normally.

```
Your Device
    │
    │  "What's the IP for doubleclick.net?"
    ▼
DNS Sinkhole (port 53)
    │
    ├── In blocklist? ──YES──► Return 0.0.0.0 ──► Connection blocked ✅
    │                          Log as BLOCKED
    │
    └── Not in blocklist? ───► Forward to 8.8.8.8 ──► Return real IP ──► Site loads
                               Log as ALLOWED
```

Think of it as a **network-level ad blocker** that works on every device on your network — phones, laptops, smart TVs — without installing anything on them. Similar to how **Pi-hole** works.

---

## ✨ Features

- 🌐 **Real UDP DNS Server** — intercepts actual DNS queries on port 53
- 🚫 **Blocklist Management** — block domains by category (ads, malware, phishing, trackers)
- 🔗 **Parent Domain Matching** — blocking `example.com` auto-blocks `ads.example.com`
- 📋 **Real-time Query Logging** — every DNS query logged with exact date and time
- 📊 **Live Dashboard** — charts, stats, top blocked domains, query activity
- 🧪 **DNS Test Tool** — test any domain without a DNS client
- 🔄 **Enable/Disable Without Restart** — toggle protection on/off from the dashboard
- 🎮 **Demo Mode** — interactive demo with simulated data for portfolio use
- 🐳 **Docker Support** — one-command deployment with Docker Compose
- 🔌 **REST API** — full API for all operations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### 1. Clone the repo
```bash
git clone https://github.com/TalhaChougle/DNS-Sinkhole.git
cd DNS-Sinkhole
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the app

**Windows** (run VS Code or terminal as Administrator):
```bash
python main.py
```

**Mac/Linux:**
```bash
sudo python3 main.py
```

### 4. Open the dashboard
```
http://127.0.0.1:5000
```

> **Note:** On Windows without admin privileges the DNS server runs on port **5353**. For system-wide DNS filtering on port 53, run as Administrator.

---

## 🖥️ System-Wide DNS Filtering (Windows)

To make the sinkhole filter all DNS traffic on your machine automatically:

1. Run VS Code as Administrator and start the app
2. Go to **Network Settings → WiFi → IPv4 Properties**
3. Set **Preferred DNS** to `127.0.0.1` and **Alternate DNS** to `8.8.8.8`
4. Click OK

Every website you visit now goes through your sinkhole. The dashboard logs every domain in real time with exact timestamps.

**To revert:** Switch IPv4 DNS back to "Obtain automatically"

---

## 🤖 Auto-Start on Boot (Windows)

To make the sinkhole start automatically when Windows boots:

1. Create `start_sinkhole.bat`:
```bat
@echo off
cd "C:\path\to\DNS-Sinkhole"
python main.py
```

2. Press **Win + R** → type `shell:startup` → paste the bat file there

The sinkhole now starts silently in the background every time you turn on your laptop.

---

## 🧪 Live Demo

Try the interactive demo at **[dns-sinkhole.netlify.app](https://dns-sinkhole.netlify.app)**

- Test any domain to see if it would be blocked or allowed
- Add and remove domains from the blocklist live
- View simulated query logs and real-looking charts
- No installation needed — runs entirely in the browser

---

## 📁 Project Structure

```
DNS-Sinkhole/
├── main.py               ← Entry point — starts DNS server + dashboard together
├── dns_server.py         ← Core DNS engine — intercepts and filters queries
├── database.py           ← SQLite layer — logs, blocklist, settings
├── app.py                ← Flask REST API + dashboard backend
├── simulate_traffic.py   ← Demo traffic generator for testing
├── requirements.txt      ← Python dependencies
├── Dockerfile
├── docker-compose.yml
└── templates/
    └── dashboard.html    ← Admin dashboard (live + demo mode)
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | Aggregate statistics |
| `GET` | `/api/logs` | Query logs (`?action=BLOCKED&search=domain`) |
| `POST` | `/api/logs/clear` | Clear all logs |
| `GET` | `/api/blocklist` | All blocked domains |
| `POST` | `/api/blocklist/add` | Add domain `{"domain":"...","category":"...","reason":"..."}` |
| `DELETE` | `/api/blocklist/remove/<id>` | Remove domain by ID |
| `GET` | `/api/test?domain=x` | Simulate a DNS query check |
| `GET/POST` | `/api/settings` | Get or update settings |

**Example:**
```bash
curl "http://127.0.0.1:5000/api/test?domain=doubleclick.net"
# {"domain": "doubleclick.net", "action": "BLOCKED", "blocked": true}
```

---

## 🐳 Deploy with Docker

```bash
docker-compose up --build
```

Dashboard → `http://localhost:5000` &nbsp;|&nbsp; DNS → `127.0.0.1:53`

---

## 🔒 Default Blocklist

| Category | Examples |
|----------|---------|
| **Ads** | `doubleclick.net`, `googlesyndication.com`, `amazon-adsystem.com` |
| **Trackers** | `scorecardresearch.com`, `quantserve.com`, `analytics.facebook.com` |
| **Malware** | `malware-test.com`, `c2server-demo.ru` |
| **Phishing** | `phishing-site.net` |

---

## 💡 Tech Stack

| Component | Technology |
|-----------|-----------|
| DNS Server | Python `socket` (raw UDP) |
| Web API | Flask + Flask-CORS |
| Database | SQLite |
| Dashboard | HTML/CSS/JS + Chart.js |
| Deployment | Docker + Netlify |

---

## ⚠️ Limitations & Notes

- **DNS over HTTPS (DoH)** — Chrome and Firefox use encrypted DNS by default which bypasses system DNS. Disable "Secure DNS" in browser settings to route traffic through the sinkhole.
- **Port 53** — requires Administrator/root privileges on most operating systems.
- **Network-wide filtering** — for filtering all devices on a network, deploy on a router or VPS with a static IP and point all devices' DNS to that IP.

---

## 📄 License

MIT — free to use, modify and distribute.

---

*Built as a cybersecurity portfolio project demonstrating DNS-level network filtering, Python socket programming, REST API design, SQLite data management, and real-time web dashboards.*
