FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Port 53 UDP for DNS, 5000 TCP for dashboard
EXPOSE 53/udp
EXPOSE 5000/tcp

CMD ["python", "main.py"]
