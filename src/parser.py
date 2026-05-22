from dateutil import parser
import datetime
def parse_entry(line):
    blocks = line.strip().split()    
    result = {}
    for block in blocks:
        
        if is_timestamp(block):
            result['timestamp'] = normalizeTimestamp(block)
        elif is_method(block):
            result['method'] = block
        elif is_ip(block):
            result['ip'] = block
        elif is_path(block):
            result['path'] = block
        elif 'status' not in result and is_status(block):
            result['status'] = int(block)
        elif 'response' not in result and is_responseTime(block):
            result['response'] = normalizeResponseTime(block)
    if not any(k in result for k in ['method', 'path', 'status']):
        return None
    return result
            
        
def is_method(b):
    return b in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']
    
def is_path(b):
    return b.startswith('/')

def is_status(b):
    return b.isdigit() and 100 <= int(b) <=599

def is_ip(b):
    parts = b.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        if not 0 <= int(part) <= 255:
            return False
    return True

def is_timestamp(b):
    # HH:MM:SS time part — has colons, all parts are digits
    if ':' in b:
        parts = b.split(':')
        return all(p[:2].isdigit() for p in parts)
    
    # date part — has - or / as separator, starts with 4 digit year or 2 digit day
    if '-' in b or '/' in b:
        return any(c.isdigit() for c in b)
    
    # unix epoch — exactly 10 digits
    if b.isdigit() and len(b) == 10:
        return True
    
    return False

def is_responseTime(b):
    t = b
    for unit in ['ms', 'µs', 'ns', 'min', 's']:
        if b.endswith(unit):
            t = b[:-len(unit)]
            break
    try:
        float(t)
        return True
    except:
        return False
    
def normalizeTimestamp(raw):
    try:
        if raw.isdigit() and len(raw) == 10:
            return datetime.datetime.fromtimestamp(int(raw)).isoformat()
        return parser.parse(raw).isoformat()
    except:
        return None
def normalizeResponseTime(b):
    try:
        if b.endswith('ms'):
            return float(b[:-2])
        elif b.endswith('µs'):
            return float(b[:-2]) / 1000
        elif b.endswith('ns'):
            return float(b[:-2]) / 1_000_000
        elif b.endswith('min'):
            return float(b[:-3]) * 60000
        elif b.endswith('s'):
            return float(b[:-1]) * 1000
        else:
            val = float(b)  
            return val
    except:
        return None



    
entry = "2024/03/15 14:23:01 10.0.0.7 POST /api/login 401 89ms"
res = parse_entry(entry)
print(res)