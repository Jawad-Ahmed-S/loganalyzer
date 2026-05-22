import json
from parser import parse_entry
def parse_file(filepath):
    entries = []
    skipped = []
    
    with open(filepath, 'r', errors='ignore') as f:  # errors='ignore' handles UTF-8 garbage
        for line in f:
            try:
                result = parse_entry(line)
                if result:
                    entries.append(result)
                else:
                    skipped.append(line.strip())
            except:
                skipped.append(line.strip())
    
    print(f"Parsed: {len(entries)} | Skipped: {len(skipped)}")
    
    with open('output.json', 'w') as f:
        json.dump(entries, f, indent=2)
    
    return entries, skipped

parse_file('../scripts/sampleLog.txt')