import os
import sqlite3
import tempfile
import pytest

# Import the module under test
from resort_database import init_database, populate_resorts, get_closest_resorts

@pytest.fixture
def temp_db_path(tmp_path):
    db_file = tmp_path / "test.db"
    return str(db_file)

@pytest.fixture
def setup_database(temp_db_path):
    # Initialize the database schema
    init_database(temp_db_path)
    return temp_db_path

@pytest.fixture
def sample_resorts(setup_database):
    """Fixture to populate sample resorts into the database for testing get_closest_resorts."""
    db_path = setup_database
    # Insert sample data tailored for tests
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    sample_data = [
        ("Alpine Meadows", 39.1687, -120.2385, "USA"),
        ("Whistler Blackcomb", 50.1163, -122.9500, "Canada"),
        ("Banff Resort", 51.1784, -115.5708, "Canada"),
        ("Chamonix Mont-Blanc", 45.9237, 6.8694, "France"),
    ]
    cursor.executemany("INSERT INTO resorts (name, latitude, longitude, country) VALUES (?, ?, ?, ?)", sample_data)
    conn.commit()
    conn.close()
    return sample_data

def test_init_database_success(temp_db_path):
    # Test successful database initialization
    init_database(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    # Verify that the table 'resorts' exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resorts'")
    table = cursor.fetchone()
    conn.close()
    assert table is not None, "Table 'resorts' should exist after initialization"

def test_init_database_failure(monkeypatch, temp_db_path):
    # Simulate a database connection error to test exception handling in init_database
    def fake_connect(*args, **kwargs):
        raise sqlite3.DatabaseError("Simulated connection error")
    monkeypatch.setattr(sqlite3, "connect", fake_connect)
    with pytest.raises(sqlite3.DatabaseError):
        init_database(temp_db_path)

def test_populate_resorts_empty_db(temp_db_path):
    # Initialize the database
    init_database(temp_db_path)
    # Ensure database is empty
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM resorts")
    count_before = cursor.fetchone()[0]
    conn.close()
    assert count_before == 0, "Database should be empty before population"
    
    # Populate the database
    populate_resorts(temp_db_path)
    
    # Verify that data was inserted
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM resorts")
    count_after = cursor.fetchone()[0]
    conn.close()
    assert count_after

> 0, "Database should be populated with data"

def test_populate_resorts_prepopulated(temp_db_path):
    # Initialize the database and prepopulate with a resort
    init_database(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resorts (name, latitude, longitude, country) VALUES (?, ?, ?, ?)",
        ("Prepopulated Resort", 40.0, -105.0, "USA")
    )
    conn.commit()
    conn.close()
    
    # Count before population
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM resorts")
    count_before = cursor.fetchone()[0]
    conn.close()
    
    # Call populate_resorts; it should detect pre-population and skip insertion
    populate_resorts(temp_db_path)
    
    # Count after population remains the same
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM resorts")
    count_after = cursor.fetchone()[0]
    conn.close()
    
    assert count_after == count_before, "Database population should be skipped when already populated"

def test_populate_resorts_failure(monkeypatch, temp_db_path):
    # Initialize the database
    init_database(temp_db_path)
    
    # Monkeypatch sqlite3.connect to simulate an insertion error
    def fake_connect(*args, **kwargs):
        raise sqlite3.DatabaseError("Simulated insertion error")
    monkeypatch.setattr(sqlite3, "connect", fake_connect)
    
    with pytest.raises(sqlite3.DatabaseError):
        populate_resorts(temp_db_path)

def test_get_closest_resorts_no_filter(sample_resorts, temp_db_path):
    # Get all resorts when no filter is provided
    # Assume a reference point near (45.0, -120.0)
    results = get_closest_resorts(temp_db_path, 45.0, -120.0)
    # Verify that all sample resorts are returned (order may vary)
    assert len(results) == len(sample_resorts), "Should return all resorts when no filter is applied"

def test_get_closest_resorts_with_filter(sample_resorts, temp_db_path):
    # Get resorts with a query filter: country = 'Canada'
    results = get_closest_resorts(temp_db_path, 45.0, -120.0, filters={"country": "Canada"})
    # Verify that each returned resort has country 'Canada'
    for resort in results:
        # Assume resort is a tuple and country is the last element
        assert resort[-1] == "Canada", "Returned resort should be in Canada"

def test_get_closest_resorts_with_custom_limit(sample_resorts, temp_db_path):
    # Request only one resort using a custom limit
    results = get_closest_resorts(temp_db_path, 45.0, -120.0, limit=1)
    assert len(results) == 1, "Should return exactly one resort with custom limit"

def test_get_closest_resorts_failure(monkeypatch, temp_db_path):
    # Simulate a database error when connecting for get_closest_resorts
    def fake_connect(*args, **kwargs):
        raise sqlite3.DatabaseError("Simulated connection failure")
    monkeypatch.setattr(sqlite3, "connect", fake_connect)
    with pytest.raises(sqlite3.DatabaseError):
        get_closest_resorts(temp_db_path, 45.0, -120.0)

def test_full_workflow(temp_db_path):
    # Integration test: initialize, populate, and query
    init_database(temp_db_path)
    populate_resorts(temp_db_path)
    
    # Query without filter
    results_no_filter = get_closest_resorts(temp_db_path, 45.0, -120.0)
    assert len(results_no_filter) > 0, "Integration: should retrieve resorts without filter"
    
    # Query with filter, e.g., only USA resorts
    results_filtered = get_closest_resorts(temp_db_path, 45.0, -120.0, filters={"country": "USA"})
    # Ensure that filtered results are a subset of the no-filter results
    for resort in results_filtered:
        assert resort[-1] == "USA", "Integration: filtered resort should be in USA"

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))