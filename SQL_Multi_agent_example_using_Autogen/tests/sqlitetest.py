import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('database.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Query the sqlite_master table to get information about existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# Fetch all table names
table_names = cursor.fetchall()

# Print the names of existing tables
for table in table_names:
    print(table[0])

# Close the cursor and connection
cursor.close()
conn.close()
