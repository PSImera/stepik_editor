import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8-sig") as f:
    data = json.load(f)
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
