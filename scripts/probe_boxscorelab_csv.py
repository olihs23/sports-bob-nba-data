#!/usr/bin/env python3
"""Read-only audit of BoxScore Lab 2026-27 licensed team ratings CSV."""
import csv,json,io,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
url="https://boxscorelab.com/downloads/2026-27-team-standings.csv"
obj={"checkedAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"source":url}
try:
 req=urllib.request.Request(url,headers={"User-Agent":"SportsBobResearch/0.1 (+CC BY 4.0 CSV validation)","Accept":"text/csv,text/plain;q=0.9,*/*;q=0.2"})
 with urllib.request.urlopen(req,timeout=17) as r:
  body=r.read(120_001)
  obj["status"]=r.status;obj["mimeType"]=r.headers.get("Content-Type")
 if len(body)>120_000:raise ValueError("Too large")
 text=body.decode("utf-8-sig")
 reader=csv.DictReader(io.StringIO(text))
 rows=list(reader)
 obj["columns"]=reader.fieldnames
 obj["rows"]=len(rows)
 obj["sampleRows"]=rows[:3]
 obj["lastRow"]=rows[-1] if rows else {}
except Exception as e:obj["error"]=f"{type(e).__name__}: {str(e)[:200]}"
Path("data/league").mkdir(parents=True,exist_ok=True)
Path("data/league/boxscorelab_csv_probe.json").write_text(json.dumps(obj,indent=2)+"\n")
print(json.dumps(obj,indent=2))
