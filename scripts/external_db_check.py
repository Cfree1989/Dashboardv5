import os
import psycopg2
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_job_status():
    """Connects to the database and checks job counts for UPLOADED status."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in environment variables.")
        return

    # For local script execution, connect to localhost instead of the 'db' container hostname
    db_url = db_url.replace("@db:", "@localhost:")
    # Also, adjust the port if it's the standard one, to match docker-compose port forwarding
    db_url = db_url.replace(":5432/", ":5433/")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        print("Successfully connected to the database.")
        print("-" * 30)

        previous_count = -1

        while True:
            # Execute the query
            cursor.execute("SELECT COUNT(*) FROM job WHERE status = 'UPLOADED';")
            count = cursor.fetchone()[0]

            # Get current timestamp
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

            # Print if the count has changed
            if count != previous_count:
                print(f"[{timestamp}] UPLOADED job count: {count}")
                previous_count = count
            
            # Wait for a short interval before checking again
            time.sleep(2)

    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    finally:
        # Ensure the connection is closed
        if 'conn' in locals() and conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    check_job_status()
