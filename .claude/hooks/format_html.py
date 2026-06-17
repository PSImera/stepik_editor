import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8-sig") as f:
    content = f.read()
# Зеркалит _write_html в даунлодере: контент шага хранится как content.strip()
# (без финального перевода строки и обрамляющих пробелов) — так его отдаёт Stepik.
normalized = content.strip()
if normalized != content:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(normalized)
