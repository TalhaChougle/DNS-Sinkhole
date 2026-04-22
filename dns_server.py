"""
DNS Sinkhole Server
Intercepts DNS queries and blocks malicious/unwanted domains.
"""

import socket
import threading
import struct
import logging
import os
from datetime import datetime
from database import db_log_query, db_is_blocked

# Config
DNS_HOST = "0.0.0.0"
DNS_PORT = 53
UPSTREAM_DNS = "8.8.8.8"   # Google DNS (fallback for allowed domains)
SINKHOLE_IP = "0.0.0.0"    # Returned for blocked domains

logging.basicConfig(level=logging.INFO, format="%(asctime)s [DNS] %(message)s")
logger = logging.getLogger(__name__)


def parse_domain_from_query(data):
    """Extract domain name from raw DNS query bytes."""
    try:
        domain_parts = []
        idx = 12  # DNS header is 12 bytes
        while idx < len(data):
            length = data[idx]
            if length == 0:
                break
            domain_parts.append(data[idx + 1: idx + 1 + length].decode("utf-8", errors="ignore"))
            idx += length + 1
        return ".".join(domain_parts)
    except Exception:
        return ""


def build_blocked_response(query_data, sinkhole_ip=SINKHOLE_IP):
    """Build a DNS response pointing to the sinkhole IP."""
    try:
        transaction_id = query_data[:2]
        flags = b"\x81\x80"  # Standard response, no error
        questions = query_data[4:6]
        answer_count = b"\x00\x01"
        auth_rr = b"\x00\x00"
        add_rr = b"\x00\x00"

        header = transaction_id + flags + questions + answer_count + auth_rr + add_rr
        question = query_data[12:]  # Include the question section

        # Answer: pointer to question name, type A, class IN, TTL 60, data 0.0.0.0
        answer = (
            b"\xc0\x0c"          # Pointer to domain name in question
            + b"\x00\x01"        # Type A
            + b"\x00\x01"        # Class IN
            + b"\x00\x00\x00\x3c"  # TTL 60 seconds
            + b"\x00\x04"        # Data length 4 bytes
            + socket.inet_aton(sinkhole_ip)
        )

        return header + question + answer
    except Exception as e:
        logger.error(f"Error building blocked response: {e}")
        return None


def forward_to_upstream(data, upstream=UPSTREAM_DNS, timeout=3):
    """Forward DNS query to upstream resolver and return response."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(data, (upstream, 53))
        response, _ = sock.recvfrom(4096)
        sock.close()
        return response
    except Exception as e:
        logger.error(f"Upstream DNS error: {e}")
        return None


def handle_query(data, addr, server_socket):
    """Handle a single DNS query — block or forward."""
    domain = parse_domain_from_query(data)
    if not domain:
        return

    blocked = db_is_blocked(domain)
    action = "BLOCKED" if blocked else "ALLOWED"

    # Log to database
    client_ip = addr[0]
    db_log_query(domain, client_ip, action)

    if blocked:
        logger.info(f"🚫 BLOCKED  {domain} from {client_ip}")
        response = build_blocked_response(data)
        if response:
            server_socket.sendto(response, addr)
    else:
        logger.info(f"✅ ALLOWED  {domain} from {client_ip}")
        response = forward_to_upstream(data)
        if response:
            server_socket.sendto(response, addr)


def start_dns_server():
    """Start the UDP DNS server."""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((DNS_HOST, DNS_PORT))
        logger.info(f"🌐 DNS Sinkhole listening on {DNS_HOST}:{DNS_PORT}")

        while True:
            try:
                data, addr = server_socket.recvfrom(4096)
                thread = threading.Thread(
                    target=handle_query,
                    args=(data, addr, server_socket),
                    daemon=True
                )
                thread.start()
            except Exception as e:
                logger.error(f"Error handling query: {e}")

    except PermissionError:
        logger.error("❌ Port 53 requires root/admin privileges. Run with sudo or use port 5353.")
        raise
    except Exception as e:
        logger.error(f"Fatal DNS server error: {e}")
        raise


if __name__ == "__main__":
    start_dns_server()
