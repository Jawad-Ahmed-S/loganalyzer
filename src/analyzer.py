from collections import defaultdict
import json
from datetime import datetime

def analyze(entries):
    stats = {
        'total': len(entries),
        'time_range': get_time_range(entries),
        'traffic_by_hour': traffic_by_hour(entries),
        'top_endpoints': top_endpoints(entries),
        'slowest_endpoints': slowest_endpoints(entries),
        'status_distribution': status_distribution(entries),
        'failed_logins_by_ip': failed_logins_by_ip(entries),
        'response_time_buckets': response_time_buckets(entries),
        'top_ips': top_ips(entries),
    }
    return stats

def get_time_range(entries):
    timestamps = [e['timestamp'] for e in entries if e.get('timestamp')]
    if not timestamps:
        return None
    timestamps.sort()
    return {'start': timestamps[0], 'end': timestamps[-1]}

def traffic_by_hour(entries):
    counts = defaultdict(int)
    for e in entries:
        if e.get('timestamp'):
            hour = e['timestamp'][:13]  # "2024-03-15T14"
            counts[hour] += 1
    return dict(sorted(counts.items()))

def top_endpoints(entries, n=10):
    counts = defaultdict(int)
    for e in entries:
        if e.get('path'):
            counts[e['path']] += 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

def slowest_endpoints(entries, n=10):
    times = defaultdict(list)
    for e in entries:
        if e.get('path') and e.get('response'):
            times[e['path']].append(e['response'])
    avgs = {path: sum(t)/len(t) for path, t in times.items()}
    return sorted(avgs.items(), key=lambda x: x[1], reverse=True)[:n]

def status_distribution(entries):
    buckets = {'2xx': defaultdict(int), '4xx': defaultdict(int), '5xx': defaultdict(int), 'other': defaultdict(int)}
    for e in entries:
        s = int(e['status']) if e.get('status') else None
        if not s:
            continue
        if 200 <= s < 300:
            buckets['2xx'][s] += 1
        elif 400 <= s < 500:
            buckets['4xx'][s] += 1
        elif 500 <= s < 600:
            buckets['5xx'][s] += 1
        else:
            buckets['other'][s] += 1
    return {k: dict(v) for k, v in buckets.items()}

def failed_logins_by_ip(entries, n=10):
    counts = defaultdict(int)
    for e in entries:
        if int(e.get('status', 0)) == 401 and e.get('ip'):
            counts[e['ip']] += 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

def response_time_buckets(entries):
    buckets = {'<100ms': 0, '100-500ms': 0, '500-1000ms': 0, '>1000ms': 0}
    for e in entries:
        r = e.get('response')
        if r is None:
            continue
        if r < 100:
            buckets['<100ms'] += 1
        elif r < 500:
            buckets['100-500ms'] += 1
        elif r < 1000:
            buckets['500-1000ms'] += 1
        else:
            buckets['>1000ms'] += 1
    return buckets

def top_ips(entries, n=10):
    counts = defaultdict(int)
    for e in entries:
        if e.get('ip'):
            counts[e['ip']] += 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]