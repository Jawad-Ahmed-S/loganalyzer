# Log Analyzer



## 1)  How To Run: 
## Clone 
```bash
git clone https://github.com/Jawad-Ahmed-S/loganalyzer
```

## Setup

```bash
pip install -r requirements.txt
```
It will install python-dateutil
## Run

```bash
python run.py {path/to/logfile.txt}
```

## Generate Sample Log (Just to satisfy the requirement)

```bash
python scripts/generate_log.py
python run.py sampleLog.txt
```


## 2)  Stack Choice:
Python + report in HTML  
### Why I Chose this?
Log parsing is essentially text processing, Python's standard library handles it well.
### Worst Choice:
Node.js, overall good but would need external libraries for most the text processing which python does better.


## 3) Edge Case:
### Split timestamps (2024/03/15 14:23:01 case)
In src/parser.py, lines 4–8, parse_entry() checks whether the second block starts with a digit and contains a colon — if so, it merges blocks 0 and 1 before parsing the timestamp. Without this, 14:23:01 would be passed downstream on its own, either misparsed as a response time or silently dropped, and the entry would have no timestamp.
### Another: Unix epoch misidentified as response time (1710512581 case)
In src/parser.py, is_responseTime(), line 44, there is an explicit early return for any 10-digit all-digit string. A Unix timestamp is a valid float, so without this guard it would be claimed as a 1.7 billion millisecond response time and the timestamp field would never be set. 

## 4)  AI Usage:

### Claude: 

Parser logic (src/parser.py) — Asked for help implementing the field detection functions (is_timestamp, is_method, is_ip, etc.) and the normalization functions (normalizeTimestamp, normalizeResponseTime). AI provided the initial implementations which I took and integrated.

Analyzer (src/analyzer.py) — Asked for help structuring the stat functions (traffic by hour, slowest endpoints, status distribution etc.). AI gave the structure, the logic of grouping and sorting was along the lines of what I had in mind.

Report UI (src/reporter.py) — Asked for help generating the HTML/Chart.js report. AI produced the layout and chart configurations. I directed what sections to include and how to present the data.

### Something I changed: 
1. For the report UI, AI gave me a basic working HTML structure but I redesigned the overall layout — the topbar, the two-column grid sections, which charts go where, what stats to surface (avg response time and error rate as big numbers rather than in a table), and the color coding for slow vs fast endpoints. The Chart.js configurations for switching between bar and line based on time range was also my call. AI handled the boilerplate, I directed what the report actually looks like and what it surfaces.

2. In the parser, AI's original is_responseTime() had no guard against Unix timestamps, a 10-digit number like 1710512581 would have been recorded as a 1.7 billion ms response time. I caught this during testing and added the early return on line 44 myself:

## 5. Honest Gap
The report feels scattered right now — it shows all the data but doesn't tell you what to actually look at. Ideally it should lead with specific insights: a spike in 5xx at a particular hour, one IP responsible for a disproportionate share of traffic, an endpoint whose average response time is way above the rest. With another day I would add a dedicated "highlights" section at the top that surfaces these automatically, so you open the report and immediately know what needs attention rather than having to read every chart yourself.