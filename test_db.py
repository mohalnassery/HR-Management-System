import psycopg2

try:
    conn = psycopg2.connect(
        dbname="hrms_db",
        user="HRAdmin",
        password="your_postgres_password",
        host="localhost",
        port="5432"
    )
    print("Successfully connected to the database!")
    conn.close()
except Exception as e:
    print(f"Error connecting to the database: {e}")
