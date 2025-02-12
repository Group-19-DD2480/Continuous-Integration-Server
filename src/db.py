import sqlite3
from flask import g

DATABASE = "ci_server.db"


# Initialise the database
def initialise_db():
    try:
        conn = sqlite3.connect(DATABASE)

        # Create the table if it doesn't exist
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS builds (
                id INTEGER PRIMARY KEY,
                commit_identifier TEXT NOT NULL,
                build_date TEXT NOT NULL,
                status TEXT not null,
                test_output TEXT not null
            )
        """
        )
        conn.commit()
        return conn

    except sqlite3.Error as e:
        print("Database error:", e)
        return None


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db


def close_db():
    db = g.pop("db", None)
    if db is not None:
        db.close()


# Insert a new build record
def insert_build(conn, commit_identifier, build_date, status, test_output):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO builds (commit_identifier, build_date, status, test_output)
        VALUES (?, ?, ?, ?)
    """,
        (commit_identifier, build_date, status, test_output,),
    )
    conn.commit()
    return cursor.lastrowid


# Get all build records
def get_builds(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM builds")
    return cursor.fetchall()


# Get a specific build record
def get_build(conn, build_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM builds WHERE id = ?", (build_id,))
    return cursor.fetchone()
