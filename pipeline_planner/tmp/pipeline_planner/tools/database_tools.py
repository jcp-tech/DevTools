
import json

def db_reader(query: str) -> str:
    """Provides read-only access to the database for debugging data issues.

    Args:
        query: The SQL query to execute (e.g., SELECT statements).

    Returns:
        A JSON string representing the query results or an error message.
    """
    print(f"Executing DB Read query: {query}")
    # Simulate database read operations
    if "SELECT * FROM users WHERE id" in query:
        return json.dumps([{"id": 1, "name": "Test User", "status": "active"}])
    return "No data found or query not permitted for read-only access."

def db_writer(update_statement: str) -> str:
    """Provides write permissions to the database to fix data entries (Admin-level).

    Args:
        update_statement: The SQL statement to execute (e.g., UPDATE, INSERT, DELETE).

    Returns:
        A confirmation message or an error.
    """
    print(f"Attempting to execute DB Write: {update_statement[:100]}...")
    # Simulate database write operation
    if "UPDATE users SET status" in update_statement:
        return "Database successfully updated. User status changed."
    return "Database write failed or statement not recognized."
