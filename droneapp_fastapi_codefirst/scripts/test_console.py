from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(text('select id, email, role, created_at from users order by id'))
    for r in rows:
        print(r)
