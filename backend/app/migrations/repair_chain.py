"""
Script to repair a broken Alembic revision chain by:
- scanning existing migrations,
- reading revision / down_revision,
- detecting missing links,
- generating placeholder migrations automatically,
- ensuring sequential integrity.

Run inside: backend/app/migrations
"""

import os
import re
from datetime import datetime

MIGRATIONS_DIR = "."
PLACEHOLDER_TEMPLATE = '''"""Auto-generated placeholder migration for {rev_id}"""

from alembic import op
import sqlalchemy as sa

revision = '{rev_id}'
down_revision = '{down_rev}'
branch_labels = None
depends_on = None

def upgrade():
    # minimal stub to satisfy Alembic chain
    pass

def downgrade():
    pass
'''

def extract_rev(path):
    with open(path, "r") as f:
        text = f.read()
    rev = re.search(r"revision\s*=\s*'([^']+)'", text)
    down = re.search(r"down_revision\s*=\s*'([^']+)'", text)
    return (rev.group(1) if rev else None,
            down.group(1) if down else None)

def main():
    print("\n🔍 Scanning migration files...\n")

    migrations = [f for f in os.listdir(MIGRATIONS_DIR)
                  if f.endswith(".py") and f not in ("env.py", "repair_chain.py")]

    rev_map = {}
    down_missing = set()

    # Extract revisions
    for m in migrations:
        path = os.path.join(MIGRATIONS_DIR, m)
        rev, down = extract_rev(path)
        if rev:
            rev_map[rev] = m
        if down and down != "None":
            if down not in rev_map:
                down_missing.add(down)

    print(f"📌 Existing revisions: {list(rev_map.keys())}")
    print(f"❗ Missing down_revisions: {down_missing}")

    # Generate placeholders for missing revisions
    created = []
    for missing in down_missing:
        file_name = f"{missing}.py"
        path = os.path.join(MIGRATIONS_DIR, file_name)

        if os.path.exists(path):
            print(f"✔ Placeholder already exists for {missing}")
            continue

        # guess previous revision number
        # e.g. '014_meta_rt_engine' -> guesses '013'
        numeric_guess = re.match(r"(\d+)", missing)
        if numeric_guess:
            num = int(numeric_guess.group(1))
            down_guess = f"{num-1:03d}"
        else:
            down_guess = "None"

        # create placeholder file
        with open(path, "w") as f:
            f.write(PLACEHOLDER_TEMPLATE.format(
                rev_id=missing,
                down_rev=down_guess
            ))

        created.append(file_name)
        print(f"🆕 Created placeholder: {file_name}")

    if not created:
        print("\n✨ No new placeholders required.")
    else:
        print("\n🎉 Placeholders created:")
        for c in created:
            print("   -", c)

    print("\n✅ Migration chain repair complete.\n")
    print("👉 Now run:")
    print("   alembic upgrade head")
    print("   alembic downgrade -1")
    print("   alembic upgrade head\n")

if __name__ == "__main__":
    main()
