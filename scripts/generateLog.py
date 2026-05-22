#!/usr/bin/env python3
"""
Generate a messy server log file with various anomalies for testing.
Run: python scripts/generate_messy_log.py [output_file] [num_lines]
"""

import random
import time
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path


def random_ip():
    """Generate random IPv4 address."""
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def random_method():
    """Pick random HTTP method with realistic distribution."""
    return random.choices(
        ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        weights=[0.6, 0.2, 0.08, 0.05, 0.04, 0.02, 0.01]
    )[0]

def random_path():
    """Generate random API endpoint path."""
    endpoints = [
        "/api/users", "/api/users/123", "/api/users/me", "/api/login",
        "/api/logout", "/api/products", "/api/products/456", "/api/orders",
        "/api/orders/789", "/api/search", "/api/health", "/api/metrics",
        "/static/index.html", "/static/app.js", "/static/style.css",
        "/admin/dashboard", "/admin/config", "/webhook/stripe", "/graphql"
    ]
    return random.choice(endpoints)

def random_status():
    """Return HTTP status codes with realistic distribution."""
    return random.choices(
        [200, 201, 204, 301, 302, 400, 401, 403, 404, 500, 502, 503],
        weights=[0.7, 0.05, 0.03, 0.04, 0.03, 0.04, 0.03, 0.02, 0.03, 0.02, 0.005, 0.005]
    )[0]

def random_response_time():
    """Generate random response time with various units."""
    ms_time = random.uniform(1, 5000)
    format_choice = random.random()
    
    if format_choice < 0.7:  # 70% ms
        return f"{int(ms_time)}ms"
    elif format_choice < 0.85:  # 15% seconds (with s)
        return f"{round(ms_time / 1000, 3)}s"
    else:  # 15% just number (assume ms by convention)
        return f"{int(ms_time)}"

def timestamp_variants(base_time):
    """Generate different timestamp formats."""
    style = random.random()
    
    if style < 0.6:  # 60% ISO format
        return base_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif style < 0.75:  # 15% with slashes
        return base_time.strftime("%Y/%m/%d %H:%M:%S")
    elif style < 0.85:  # 10% Unix epoch
        return str(int(base_time.timestamp()))
    else:  # 15% custom format
        return base_time.strftime("%d-%b-%Y %H:%M:%S")

def extra_fields():
    """Add extra fields for ~15% of normal lines."""
    if random.random() < 0.15:
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'curl/7.68.0',
            'Python-urllib/3.9'
        ]
        referrers = ['"-"', '"https://example.com"', '"http://internal/admin"']
        extra = f" {random.choice(user_agents)} {random.choice(referrers)}"
        return extra
    return ""

def generate_malformed_line():
    """Generate various malformed or corrupted lines."""
    mal_type = random.choice([
        "partial", "garbage", "json_mixed", "stack_trace", "blank", 
        "missing_fields", "extra_commas", "wrong_encoding_seed"
    ])
    
    if mal_type == "blank":
        return ""
    elif mal_type == "partial":
        return f"{timestamp_variants(datetime.now())} {random_ip()} GET /api/users -".split("GET")[0]
    elif mal_type == "garbage":
        garbage = [
            "\x00\x01\x02Hello\xFF\xFE",
            "\uFFFF\uDDDDAAAA",
            "=== RANDOM BINARY BLOB ===",
            "~~~~~~~~~~~~~~~~~~~~~~"
        ]
        return random.choice(garbage)
    elif mal_type == "json_mixed":
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": "JSON format injected",
            "level": random.choice(["INFO", "WARN", "ERROR"])
        }
        return json.dumps(log_entry)
    elif mal_type == "stack_trace":
        return "  File \"server.py\", line 42, in handle_request\n    raise ConnectionError()"
    elif mal_type == "missing_fields":
        ip = random_ip()
        method = random_method()
        path = random_path()
        return f"{timestamp_variants(datetime.now())} {ip} {method} {path}"
    elif mal_type == "extra_commas":
        ip = random_ip()
        method = random_method()
        path = random_path()
        status = random_status()
        time_val = random_response_time()
        return f"{timestamp_variants(datetime.now())},{ip},{method},{path},{status},{time_val},,extra,,,garbage"
    else:  # wrong_encoding_seed — simulated corrupt byte
        normal_line = f"{timestamp_variants(datetime.now())} {random_ip()} {random_method()} {random_path()} {random_status()} {random_response_time()}"
        # Corrupt by replacing a random character with non-UTF8 byte representation
        if len(normal_line) > 10:
            pos = random.randint(5, len(normal_line)-5)
            corrupt_byte = bytes([random.choice([0xFF, 0xFE, 0x80, 0xC0])]).decode('utf-8', errors='replace')
            return normal_line[:pos] + corrupt_byte + normal_line[pos+1:]
        return normal_line

def generate_log_file(filepath, num_lines=500):
    """Main generator function."""
    
    start_time = datetime(2024, 3, 15, 0, 0, 0)
    lines = []
    
    for i in range(num_lines):
        # 5-10% totally malformed lines
        if random.random() < 0.07:  # 7% malformed
            lines.append(generate_malformed_line())
            continue
        
        # 2-3% different log format (old format with hyphens vs spaces)
        if random.random() < 0.025:
            ts = timestamp_variants(start_time + timedelta(seconds=i*random.uniform(0.1, 5)))
            ip = random_ip()
            method = random_method()
            path = random_path()
            status = random_status()
            time_val = random_response_time()
            # Old format: timestamp|ip|method|path|status|time
            lines.append(f"{ts}|{ip}|{method}|{path}|{status}|{time_val}")
            continue
        
        # Normal line with possible extra fields
        timestamp = timestamp_variants(start_time + timedelta(seconds=i*random.uniform(0.1, 5)))
        ip = random_ip()
        method = random_method()
        path = random_path()
        status = random_status()
        response_time = random_response_time()
        
        # Randomly replace status with - (3% chance)
        if random.random() < 0.03:
            status = "-"
        
        normal_line = f"{timestamp} {ip} {method} {path} {status} {response_time}"
        normal_line += extra_fields()
        
        # Occasionally add leading whitespace (4% chance)
        if random.random() < 0.04:
            normal_line = "  " + normal_line
        
    
        
        lines.append(normal_line)
    
    
    random.shuffle(lines)
    
    
    with open(filepath, 'w', encoding='utf-8', errors='replace') as f:
        f.write("\n".join(lines))
    
    print(f"Generated {num_lines} lines (approx {len([l for l in lines if l and not l.startswith('  File')])} actual log entries)")
    print(f"File saved: {filepath}")

if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "../sampleLog.txt"
    num_lines = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    
    generate_log_file(output_file, num_lines)