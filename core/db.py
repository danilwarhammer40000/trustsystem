
import sqlite3

DB_PATH = "data.db"

def get_connection():
    return sqlite3.connect(DB_PATH)