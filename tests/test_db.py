import pytest
import sys
import os
import sqlite3
import pytest
from flask import Flask, g

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from db import *

@pytest.fixture
def app_context(tmp_path, monkeypatch):
    # Create a Flask app.
    app = Flask(__name__)

    # Use a temporary file as the database.
    temp_db_path = tmp_path / "test_ci_server.db"
    monkeypatch.setattr("db.DATABASE", str(temp_db_path))

    # Push an application context so that `g` is available.
    with app.app_context():
        # Initialise the database (this will create the schema in temp_db_path)
        initialise_db()
        yield app
        # The temporary directory will be automatically cleaned up by pytest.

# test initialise_db
def test_initialise_db(tmp_path, monkeypatch):
    # Use a separate temporary database file.
    temp_db_path = tmp_path / "init_test.db"
    monkeypatch.setattr("db.DATABASE", str(temp_db_path))
    conn = initialise_db()
    # Check that the file was created.
    assert os.path.exists(str(temp_db_path))
    
    # Verify that the 'builds' table exists.
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='builds';"
    )
    table = cursor.fetchone()
    assert table is not None
    conn.close()


# test helper functions
def test_insert_and_query_builds(app_context):
    # Get a connection from the request context.
    db_conn = get_db()
    assert isinstance(db_conn, sqlite3.Connection)

    # Insert a new build record.
    commit_identifier = "abc123"
    build_date = "2023-10-10"
    status = "success"
    build_id = insert_build(db_conn, commit_identifier, build_date, status)
    assert isinstance(build_id, int)

    # Retrieve all build records.
    builds = get_builds(db_conn)
    # We expect one record.
    assert len(builds) == 1
    # SQLite returns rows as tuples: (id, commit_identifier, build_date)
    row = builds[0]
    assert row[0] == build_id
    assert row[1] == commit_identifier
    assert row[2] == build_date

    # Retrieve the specific build by its ID.
    build = get_build(db_conn, build_id)
    assert build is not None
    assert build[0] == build_id
    assert build[1] == commit_identifier
    assert build[2] == build_date


def test_close_db(app_context):
    # Create a DB connection.
    db_conn = get_db()
    assert db_conn is not None
    # Close it.
    close_db()
    # Confirm that 'db' is no longer in the Flask global `g`.
    assert "db" not in g

    # If we ask for the connection again, a new one should be created.
    new_db_conn = get_db()
    assert new_db_conn is not None
    assert new_db_conn != db_conn