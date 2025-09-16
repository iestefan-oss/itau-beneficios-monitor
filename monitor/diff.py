import json
from datetime import datetime, timezone

def to_key(item):
    title = (item.get("title") or "").lower().strip()
    pct   = item.get("percent")
    url   = (item.get("offer_url") or "").strip()
    return f"{title}|{pct}|{url}"

def compute_diff(old_items, new_items):
    old_map = {to_key(i): i for i in old_items}
    new_map = {to_key(i): i for i in new_items}

    added = [new_map[k] for k in new_map.keys() - old_map.keys()]
    removed = [old_map[k] for k in old_map.keys() - new_map.keys()]
    changed = []
    for k in new_map.keys() & old_map.keys():
        o, n = old_map[k], new_map[k]
        if (o.get("vigencia") != n.get("vigencia")) or (o.get("raw") != n.get("raw")):
            changed.append({"old": o, "new": n})

    snapshot_time = datetime.now(timezone.utc).isoformat()
    return {"timestamp": snapshot_time, "added": added, "removed": removed, "changed": changed}
