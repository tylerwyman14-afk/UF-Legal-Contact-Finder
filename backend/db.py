import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alumni.db")

ORG_TYPES = ("law_firm", "in_house", "judiciary_government")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS people (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name        TEXT NOT NULL,
                title            TEXT NOT NULL,
                organization     TEXT NOT NULL,
                org_type         TEXT NOT NULL CHECK(org_type IN ('law_firm','in_house','judiciary_government')),
                practice_area    TEXT,
                city             TEXT,
                state            TEXT,
                uf_degree        TEXT,
                uf_grad_year     INTEGER,
                email            TEXT,
                phone            TEXT,
                contact_form_url TEXT,
                linkedin_url     TEXT,
                source_url       TEXT NOT NULL,
                source_note      TEXT,
                date_verified    TEXT NOT NULL,
                confidence       TEXT DEFAULT 'verified' CHECK(confidence IN ('verified','likely','needs_review')),
                notes            TEXT,
                created_at       TEXT DEFAULT (datetime('now')),
                updated_at       TEXT DEFAULT (datetime('now')),
                UNIQUE(full_name, organization)
            );
            CREATE INDEX IF NOT EXISTS idx_people_org_type ON people(org_type);
            CREATE INDEX IF NOT EXISTS idx_people_state ON people(state);
            CREATE INDEX IF NOT EXISTS idx_people_practice ON people(practice_area);
        """)


def upsert_person(data: dict) -> int:
    fields = [
        "full_name", "title", "organization", "org_type", "practice_area",
        "city", "state", "uf_degree", "uf_grad_year", "email", "phone",
        "contact_form_url", "linkedin_url", "source_url", "source_note",
        "date_verified", "confidence", "notes",
    ]
    row = {f: data.get(f) for f in fields}
    if not row.get("confidence"):
        row["confidence"] = "verified"

    with get_conn() as conn:
        cols = ", ".join(fields)
        placeholders = ", ".join(f":{f}" for f in fields)
        updates = ", ".join(f"{f}=excluded.{f}" for f in fields if f not in ("full_name", "organization"))
        cur = conn.execute(
            f"""
            INSERT INTO people ({cols}) VALUES ({placeholders})
            ON CONFLICT(full_name, organization) DO UPDATE SET
                {updates},
                updated_at = datetime('now')
            """,
            row,
        )
        conn.commit()
        if cur.lastrowid:
            return cur.lastrowid
        existing = conn.execute(
            "SELECT id FROM people WHERE full_name=? AND organization=?",
            (row["full_name"], row["organization"]),
        ).fetchone()
        return existing["id"] if existing else None


def list_people(q=None, org_type=None, practice_area=None, state=None, limit=200, offset=0):
    clauses = []
    params = {}
    if q:
        clauses.append("(full_name LIKE :q OR organization LIKE :q OR title LIKE :q)")
        params["q"] = f"%{q}%"
    if org_type:
        clauses.append("org_type = :org_type")
        params["org_type"] = org_type
    if practice_area:
        clauses.append("practice_area = :practice_area")
        params["practice_area"] = practice_area
    if state:
        clauses.append("state = :state")
        params["state"] = state

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params["limit"] = limit
    params["offset"] = offset

    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM people
            {where}
            ORDER BY organization, full_name
            LIMIT :limit OFFSET :offset
            """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def get_person(person_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        return dict(row) if row else None


def delete_person(person_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM people WHERE id = ?", (person_id,))
        conn.commit()
        return cur.rowcount > 0


def distinct_filters():
    with get_conn() as conn:
        org_types = [r[0] for r in conn.execute(
            "SELECT DISTINCT org_type FROM people WHERE org_type IS NOT NULL ORDER BY org_type"
        )]
        practice_areas = [r[0] for r in conn.execute(
            "SELECT DISTINCT practice_area FROM people WHERE practice_area IS NOT NULL AND practice_area != '' ORDER BY practice_area"
        )]
        states = [r[0] for r in conn.execute(
            "SELECT DISTINCT state FROM people WHERE state IS NOT NULL AND state != '' ORDER BY state"
        )]
        return {"org_type": org_types, "practice_area": practice_areas, "state": states}
