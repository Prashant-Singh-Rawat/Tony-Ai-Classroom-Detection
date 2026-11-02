import re

with open("audit_output/debug_page.html", encoding="utf-8") as f:
    text = f.read()

print("Length:", len(text))
print("Has body:", "<body" in text)
print("Has id=root:", 'id="root"' in text)
print("Has canary:", "canary" in text)

m = re.search(r"<body[^>]*>(.*)</body>", text, re.DOTALL)
if m:
    inner = m.group(1).strip()
    print("Body inner length:", len(inner))
    print("Body inner snippet:", repr(inner[:500]))

