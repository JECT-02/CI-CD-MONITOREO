#!/usr/bin/env python3
"""Fix malformed JSON in result files - codigo values with leading zeros"""
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
results_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "resultados")

fixed = 0
for fname in sorted(os.listdir(results_dir)):
    path = os.path.join(results_dir, fname)
    if not fname.endswith(".jsonl"):
        continue
    
    with open(path) as f:
        content = f.read()
    
    # Fix "codigo": 000000 -> "codigo": "000"
    # Fix "codigo": 000 -> "codigo": "000"
    # Fix "codigo": 200 -> "codigo": "200"
    # Handle any numeric codigo value
    new_content = re.sub(r'"codigo": (\d+)', r'"codigo": "\1"', content)
    
    if new_content != content:
        with open(path, "w") as f:
            f.write(new_content)
        fixed += 1
        print(f"Fixed: {fname}")

print(f"\nFixed {fixed} files")
