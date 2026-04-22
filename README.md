# 🛡️ DNS Sinkhole

A Python-based DNS sinkhole with a real-time admin dashboard.
Intercepts DNS queries, blocks malicious/unwanted domains, logs all traffic, and provides a web UI for management.

---

## 📁 Project Structure

```
dns_sinkhole/
├── main.py               ← Entry point (runs DNS + dashboard together)
├── dns_server.py         ← Core DNS server (intercepts queries)
├── database.py           ← SQLite layer (logs, blocklist, settings)
├── app.py                ← Flask web API + dashboard backend
├── simulate_traffic.py   ← Demo traffic generator
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── templates/
    └── dashboard.html    ← Admin dashboard UI
```

---

## 🚀 Run Locally (VS Code)

### 1. Install dependencies
```bash
cd dns_sinkhole
pip install -r requirements.txt
```

### 2. Start the app
```bash
python main.py
```

> **Note:** The DNS server uses port **5353** locally (no sudo needed).  
> Port 53 requires root. For a full DNS test, run `sudo python main.py`.

### 3. Open the dashboard
```
http://127.0.0.1:5000
```

### 4. Simulate traffic (optional — fill dashboard with demo data)
Open a **second terminal**:
```bash
python simulate_traffic.py
```

---

## 🧪 Test a DNS Query (no DNS client needed)

Use the built-in **Test Tool** tab in the dashboard, or via API:
```bash
curl "http://127.0.0.1:5000/api/test?domain=doubleclick.net"
curl "http://127.0.0.1:5000/api/test?domain=google.com"
```

---

## 🔌 Use as an Actual DNS Server (Linux/Mac)

```bash
sudo python main.py
```

Then point your system DNS to `127.0.0.1`:
- **Mac:** System Settings → Network → DNS → add 127.0.0.1
- **Linux:** Edit `/etc/resolv.conf` → `nameserver 127.0.0.1`

---

## 🐳 Deploy with Docker

```bash
docker-compose up --build
```

Dashboard → `http://localhost:5000`  
DNS → `127.0.0.1:53`

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Aggregate statistics |
| GET | `/api/logs` | Query logs (supports `?action=BLOCKED&search=domain`) |
| POST | `/api/logs/clear` | Clear all logs |
| GET | `/api/blocklist` | All blocked domains |
| POST | `/api/blocklist/add` | Add domain `{"domain":"...", "category":"...", "reason":"..."}` |
| DELETE | `/api/blocklist/remove/<id>` | Remove domain |
| GET | `/api/test?domain=x` | Simulate a DNS query |
| GET/POST | `/api/settings` | Get/update settings |

---

## ⚙️ How It Works

```
Client DNS Query
      │
      ▼
  DNS Sinkhole (port 53 / 5353)
      │
      ├─── Domain in blocklist? ──YES──► Return 0.0.0.0 (sinkhole)
      │                                  Log as BLOCKED
      │
      └─── No ──► Forward to upstream DNS (8.8.8.8)
                  Return real IP
                  Log as ALLOWED
```

---

## 🎯 Features

- ✅ Real UDP DNS server
- ✅ Blocklist with category tagging (ads, malware, phishing, tracker)
- ✅ Parent-domain matching (block `example.com` → also blocks `sub.example.com`)
- ✅ SQLite logging with filtering and search
- ✅ Real-time dashboard with charts
- ✅ Enable/disable sinkhole without restart
- ✅ DNS Test Tool (no DNS client needed)
- ✅ Docker + Docker Compose deployment
- ✅ REST API for all operations
