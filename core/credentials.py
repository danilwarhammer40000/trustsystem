from datetime import datetime, timedelta
from core.db import get_connection

def create_credential(user_id, username, password, days):
    conn = get_connection()
    cur = conn.cursor()

    expires = datetime.now() + timedelta(days=days)

    cur.execute("""
        INSERT INTO credentials (user_id, username, password, expires_at, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (user_id, username, password, expires))

    conn.commit()
    conn.close()

def get_user_credentials(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM credentials WHERE user_id=?", (user_id,))
    rows = cur.fetchall()

    conn.close()
    return rows

def delete_expired():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM credentials
        WHERE expires_at < CURRENT_TIMESTAMP
    """)

    conn.commit()
    conn.close()
