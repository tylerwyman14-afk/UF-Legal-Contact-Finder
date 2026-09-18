"""Load researched alumni records from data/research/*.json into alumni.db.

Usage: python scripts/seed_from_json.py

Every record must already have a real `source_url` and `date_verified` —
this script only loads data, it does not fetch or verify anything.
"""
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.db import init_db, upsert_person

REQUIRED_FIELDS = ["full_name", "title", "organization", "org_type", "source_url", "date_verified"]
VALID_ORG_TYPES = ("law_firm", "in_house", "judiciary_government")


def load_batch(path: Path):
    records = json.loads(path.read_text(encoding="utf-8"))
    inserted, skipped = 0, 0
    for rec in records:
        missing = [f for f in REQUIRED_FIELDS if not rec.get(f)]
        if missing:
            print(f"  SKIP (missing {missing}): {rec.get('full_name', '?')}")
            skipped += 1
            continue
        if rec["org_type"] not in VALID_ORG_TYPES:
            print(f"  SKIP (bad org_type '{rec['org_type']}'): {rec.get('full_name', '?')}")
            skipped += 1
            continue
        upsert_person(rec)
        inserted += 1
    return inserted, skipped


def main():
    init_db()
    research_dir = BASE_DIR / "data" / "research"
    files = sorted(research_dir.glob("*.json"))
    if not files:
        print(f"No JSON files found in {research_dir}")
        return

    total_inserted, total_skipped = 0, 0
    for path in files:
        print(f"Loading {path.name}...")
        inserted, skipped = load_batch(path)
        print(f"  {inserted} inserted/updated, {skipped} skipped")
        total_inserted += inserted
        total_skipped += skipped

    print(f"\nDone. {total_inserted} total records loaded, {total_skipped} skipped.")


if __name__ == "__main__":
    main()
