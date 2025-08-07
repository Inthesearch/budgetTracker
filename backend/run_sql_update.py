#!/usr/bin/env python3
"""
Simple script to run SQL updates for converting category names to lowercase.
"""

import sqlite3
import os

def update_category_names():
    """Update category and subcategory names to lowercase using SQL."""
    db_path = "budget_tracker.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Read and execute the SQL script
        with open('update_names.sql', 'r') as f:
            sql_script = f.read()
        
        # Split the script into individual statements
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement.startswith('SELECT'):
                # For SELECT statements, fetch and display results
                cursor.execute(statement)
                results = cursor.fetchall()
                for row in results:
                    print(row)
            else:
                # For UPDATE statements, execute and show affected rows
                cursor.execute(statement)
                print(f"Updated {cursor.rowcount} rows with: {statement}")
        
        # Commit the changes
        conn.commit()
        print("Successfully updated category and subcategory names to lowercase!")
        
    except Exception as e:
        print(f"Error updating category names: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_category_names()
