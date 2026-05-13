import csv
import os

def log_result(entry, log_file="benchmarks/results/log.csv"):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=entry.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(entry)