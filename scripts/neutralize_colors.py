from pathlib import Path

# Fix MonitoringPage.tsx
p_mon = Path('frontend/src/pages/MonitoringPage.tsx')
text_mon = p_mon.read_text(encoding='utf-8')
text_mon = text_mon.replace('stroke="#06b6d4"', 'stroke="#94a3b8"')
text_mon = text_mon.replace('stroke="#8b5cf6"', 'stroke="#94a3b8"')
p_mon.write_text(text_mon, encoding='utf-8')

# Fix demo/index.ts
p_demo = Path('frontend/src/data/demo/index.ts')
text_demo = p_demo.read_text(encoding='utf-8')
text_demo = text_demo.replace("'#06b6d4'", "'#0F766E'")
p_demo.write_text(text_demo, encoding='utf-8')

print("Old-identity colors successfully neutralized.")

