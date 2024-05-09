import sqlite3
import pandas as pd
import csv
import os

def get_csv_files(path):
    """
    Function to get CSV files in a given directory path.

    Args:
    - path (str): Path to the directory containing CSV files.

    Returns:
    - csv_tables (list): List of tuples where each tuple contains the table name and the corresponding CSV file name.
    """
    csv_tables = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.csv'):
                table_name = os.path.splitext(file)[0]
                csv_tables.append((table_name, os.path.join(root, file)))
    return csv_tables

def get_schema(csv_tables):
    # Infer schema from CSV files
    schema = {}
    for table, csv_file in csv_tables:
        df = pd.read_csv(csv_file, nrows=1)
        schema[table] = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}
    return schema

def create_sqlite_database(csv_tables):
    """
    Function to create a SQLite database with tables from CSV files.

    Args:
    - csv_tables (list): List of tuples where each tuple contains the table name and the corresponding CSV file name.

    Returns:
    - conn (sqlite3.Connection): SQLite database connection object.
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    for table, csv_file in csv_tables:
        # Read CSV to infer schema
        df = pd.read_csv(csv_file, nrows=1)
        columns = df.columns.tolist()
        dtypes = df.dtypes.tolist()

        # Create table with inferred schema
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table} ("
        for col, dtype in zip(columns, dtypes):
            create_table_query += f"'{col}' {dtype}, "
        create_table_query = create_table_query.rstrip(", ") + ")"
        cursor.execute(create_table_query)

        # Insert data from CSV into table
        with open(csv_file, 'r') as file:
            next(file)  # Skip header
            data = [tuple(row) for row in csv.reader(file)]
            placeholders = ", ".join(['?'] * len(columns))
            insert_query = f"INSERT INTO {table} VALUES ({placeholders})"
            cursor.executemany(insert_query, data)

    conn.commit()
    return conn

def generate_sql_prompt(schema):
    """
    Function to generate a SQL prompt based on given schema.

    Args:
    - schema (dict): Dictionary containing table names as keys and their corresponding schema as values.

    Returns:
    - prompt (str): Generated SQL prompt.
    """
    prompt = "You are SQL Query Generator. Kindly generate the SQL query using only the listed columns in the schema below. Do not use any column outside the provided schema.\n\n"

    for table, columns in schema.items():
        prompt += f"Schema for table '{table}':\n"
        for column, datatype in columns.items():
            prompt += f"- {column}: {datatype}\n"
        prompt += "\n"

    prompt += "Use LIKE with '%' for the right match against the columns. Only use the above mentioned columns in making SQL query.\n\n"

    return prompt


if __name__=="__main__":

    # Example usage:
    csv_tables = [("table1", "table1.csv"), ("table2", "table2.csv")]  # Replace with your CSV table names and file names
    conn = create_sqlite_database(csv_tables)

    # Infer schema from CSV files
    schema = {}
    for table, csv_file in csv_tables:
        df = pd.read_csv(csv_file, nrows=1)
        schema[table] = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}

    sql_prompt = generate_sql_prompt(schema)
    print(sql_prompt)
