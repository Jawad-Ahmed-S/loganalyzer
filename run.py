#!/usr/bin/env python3
import sys
import os
from datetime import datetime


from src.analyzer import analyze
from src.reporter import generate_report
from src.parsedumpjson import parse_file  

def main():
    if len(sys.argv) < 2:
        print(" Usage: python run.py <path_to_logfile>")
        print("\nExample:")
        print("  python run.py sampleLog.txt")
        print("  python run.py ../logs/server.log")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("LOG ANALYZER")
    print("="*50 + "\n")
    
    
    entries, skipped = parse_file(filepath)
    
    if not entries:
        print("No valid entries found!")
        sys.exit(1)
    
    print(f"\nParsing complete!")
    print(f"   • Valid entries: {len(entries)}")
    print(f"   • Skipped lines: {len(skipped)}")
    
    print("\nAnalyzing data...")
    stats = analyze(entries)
    
    
    print("\nGenerating report...")
    report_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    generate_report(stats, skipped_count=len(skipped), output_path=report_path)
    
    print("\n" + "="*50)
    print(f"REPORT GENERATED: {report_path}")
    print(f" Total requests: {stats['total']}")
    print("="*50)

if __name__ == "__main__":
    main()