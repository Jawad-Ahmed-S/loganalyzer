from dateutil import parser
import datetime
def parse_entry(line):
    blocks = line.strip().split()    
    result = {}
    if len(blocks) > 1 and ':' in blocks[1] and blocks[1][0].isdigit():
        result['timestamp'] = normalizeTimestamp(blocks[0] + ' ' + blocks[1])
        rest = blocks[2:]
    else:
        result['timestamp'] = normalizeTimestamp(blocks[0])
        rest = blocks[1:]
        
    for block in rest:
        
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
    # Unix timestamp (10 digits)
    if b.isdigit() and len(b) == 10:
        return True
    
    # ISO format with T: 2024-03-15T14:23:01Z or 2024-03-15T14:23:01
    if 'T' in b and ('-' in b or '/' in b):
        return True
    
    # Date with spaces: 2024/03/15 14:23:01 or 15-Mar-2024 14:23:01
    if ('-' in b or '/' in b) and ':' in b:
        return True
    
    # Just time parts (colons and digits)
    if ':' in b:
        parts = b.split(':')
        if len(parts) >= 2:
            return all(p[:2].isdigit() for p in parts[:2])
    
    return False

def is_responseTime(b):
    # Remove unit suffix if present
    t = b
    units = ['ms', 's', 'µs', 'ns', 'min']
    for unit in units:
        if b.endswith(unit):
            t = b[:-len(unit)]
            break
    
    # Check if remaining is a valid number (int or float)
    try:
        float(t)
        return True
    except:
        return False    
    
def normalizeTimestamp(raw):
    try:
        if raw.isdigit() and len(raw) == 10:
            # UTC timestamp
            dt = datetime.datetime.utcfromtimestamp(int(raw))
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
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



    
# entry = "1710512581 10.0.0.7 POST /api/login 401 89ms"
# res = parse_entry(entry)
# print(res)