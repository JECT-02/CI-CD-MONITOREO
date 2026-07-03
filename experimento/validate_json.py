#!/usr/bin/env python3
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
results_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "resultados")

bad_files = []
for fname in sorted(os.listdir(results_dir)):
    path = os.path.join(results_dir, fname)
    if not fname.endswith(".jsonl"):
        continue
    try:
        with open(path) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"BAD JSON: {fname} line {i}: {e}")
                    print(f"  Content: {line[:200]}")
                    bad_files.append(fname)
                    break
    except Exception as e:
        print(f"ERROR reading {fname}: {e}")
        bad_files.append(fname)

if not bad_files:
    print("All JSON files valid!")
else:
    print(f"\n{len(bad_files)} bad files: {bad_files}")
