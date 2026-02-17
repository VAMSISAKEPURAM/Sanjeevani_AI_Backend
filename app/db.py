import os
import mysql.connector
from urllib.parse import urlparse

def get_db_connection():
    try:
        # Default to the provided Railway URL if variable is not set
        # Note: In production Railway environment, DATABASE_URL is set automatically.
        default_url = "mysql://root:lYsaEQLGNucDdeTffvzVAVhzqvjjlbxV@gondola.proxy.rlwy.net:39198/railway"
        database_url = os.getenv("DATABASE_URL", default_url)

        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")

        # Parse the DATABASE_URL (format: mysql://user:password@host:port/dbname)
        url = urlparse(database_url)
        
        conn = mysql.connector.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path.lstrip('/'),
            port=url.port or 3306
        )
        return conn
    except Exception as e:
        raise RuntimeError(f"Database connection error: {e}")
