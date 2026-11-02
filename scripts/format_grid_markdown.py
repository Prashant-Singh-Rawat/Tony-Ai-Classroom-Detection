import json

with open("docs/stage1b_grid_results.json", "r") as f:
    grid = json.load(f)

for m_name in ["yolov8n.pt", "yolov8s.pt", "yolo11n.pt"]:
    title = m_name.replace(".pt", "")
    print(f"#### Model: {title}\n")
    print("| Imgsz | Conf | Prec@0.3 | Rec@0.3 | F1@0.3 | Prec@0.5 | Rec@0.5 | F1@0.5 | Duplicates | Latency | FPS | Row 1 (Front) | Row 2 | Row 3 | Row 4 (Rear) | <45px | 45-74px | >=75px |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    m_items = [x for x in grid if x["model"] == m_name]
    for r in m_items:
        row_rec = r["row_recall_30"]
        h_rec = r["height_recall_30"]
        r1 = row_rec.get("r1", "-")
        r2 = row_rec.get("r2", "-")
        r3 = row_rec.get("r3", "-")
        r4 = row_rec.get("r4", "-")
        h1 = h_rec.get("<45px", "-")
        h2 = h_rec.get("45-74px", "-")
        h3 = h_rec.get(">=75px", "-")
        print(f"| {r['imgsz']} | {r['conf']} | {r['prec30']}% | {r['rec30']}% | {r['f1_30']}% | {r['prec50']}% | {r['rec50']}% | {r['f1_50']}% | {r['duplicates']} | {r['med_latency_ms']} ms | {r['fps']} | {r1} | {r2} | {r3} | {r4} | {h1} | {h2} | {h3} |")
    print("\n")
