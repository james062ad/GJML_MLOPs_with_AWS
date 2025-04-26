#!/usr/bin/env python3
"""
PostgreSQL Diagnostic Script

This script performs various diagnostic checks on a PostgreSQL database
and outputs the results to a file for analysis.
"""

import os
import subprocess
import sys
import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables from .env file
load_dotenv()

# Get PostgreSQL connection details from environment variables
# Override the host with localhost for running outside Docker
DB_HOST = "localhost"  # Override with localhost instead of os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Create output file with timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"postgres_diagnostic_{timestamp}.txt"

def run_command(command, description):
    """Run a shell command and return its output"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def execute_query(query, description):
    """Execute a PostgreSQL query using psycopg2 and return the results"""
    print(f"Running: {description}")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Format the results
        if cursor.description:
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            # Get rows
            rows = cursor.fetchall()
            
            # Format as a table
            result = " | ".join(columns) + "\n"
            result += "-" * (sum(len(col) for col in columns) + 3 * (len(columns) - 1)) + "\n"
            
            for row in rows:
                result += " | ".join(str(cell) for cell in row) + "\n"
        else:
            # For commands that don't return data
            result = "Command executed successfully.\n"
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def check_postgres_connection():
    """Check if we can connect to PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return f"Successfully connected to PostgreSQL: {version}"
    except Exception as e:
        return f"Failed to connect to PostgreSQL: {str(e)}"

def main():
    """Main function to run all diagnostics"""
    with open(output_file, "w") as f:
        f.write(f"PostgreSQL Diagnostic Report - {datetime.datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        
        # Connection details
        f.write("Connection Details:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Host: {DB_HOST} (overridden to localhost for external access)\n")
        f.write(f"Port: {DB_PORT}\n")
        f.write(f"Database: {DB_NAME}\n")
        f.write(f"User: {DB_USER}\n")
        f.write("\n")
        
        # Check PostgreSQL connection
        f.write("PostgreSQL Connection:\n")
        f.write("-" * 80 + "\n")
        connection_status = check_postgres_connection()
        f.write(connection_status + "\n\n")
        
        # PostgreSQL version
        f.write("PostgreSQL Version:\n")
        f.write("-" * 80 + "\n")
        version_output = execute_query("SELECT version();", "Checking PostgreSQL version")
        f.write(version_output + "\n")
        
        # Check pgvector extension
        f.write("pgvector Extension:\n")
        f.write("-" * 80 + "\n")
        vector_output = execute_query("SELECT * FROM pg_extension WHERE extname = 'vector';", "Checking pgvector extension")
        f.write(vector_output + "\n")
        
        # Check papers table structure
        f.write("Papers Table Structure:\n")
        f.write("-" * 80 + "\n")
        table_output = execute_query("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'papers'
            ORDER BY ordinal_position;
        """, "Checking papers table structure")
        f.write(table_output + "\n")
        
        # Check indexes on papers table
        f.write("Indexes on Papers Table:\n")
        f.write("-" * 80 + "\n")
        indexes_output = execute_query("""
            SELECT
                i.relname AS index_name,
                a.attname AS column_name,
                ix.indisunique AS is_unique
            FROM
                pg_class t,
                pg_class i,
                pg_index ix,
                pg_attribute a
            WHERE
                t.oid = ix.indrelid
                AND i.oid = ix.indexrelid
                AND a.attrelid = t.oid
                AND a.attnum = ANY(ix.indkey)
                AND t.relkind = 'r'
                AND t.relname = 'papers'
            ORDER BY
                t.relname,
                i.relname;
        """, "Checking indexes on papers table")
        f.write(indexes_output + "\n")
        
        # Check for locks
        f.write("Active Locks:\n")
        f.write("-" * 80 + "\n")
        locks_output = execute_query("""
            SELECT blocked_locks.pid AS blocked_pid,
                   blocked_activity.usename AS blocked_user,
                   blocking_locks.pid AS blocking_pid,
                   blocking_activity.usename AS blocking_user,
                   blocked_activity.query AS blocked_statement,
                   blocking_activity.query AS current_statement_in_blocking_process
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
            JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
            JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
            WHERE NOT blocked_locks.granted;
        """, "Checking for active locks")
        f.write(locks_output + "\n")
        
        # Check table statistics
        f.write("Table Statistics:\n")
        f.write("-" * 80 + "\n")
        stats_output = execute_query("SELECT relname, n_live_tup, n_dead_tup FROM pg_stat_user_tables WHERE relname = 'papers';", "Checking table statistics")
        f.write(stats_output + "\n")
        
        # Check for the problematic file
        f.write("Checking for Problematic File:\n")
        f.write("-" * 80 + "\n")
        try:
            # Try to find the PostgreSQL data directory
            data_dir_output = execute_query("SHOW data_directory;", "Finding PostgreSQL data directory")
            f.write(data_dir_output + "\n")
            
            # Extract the data directory path
            data_dir = None
            for line in data_dir_output.split('\n'):
                if line.strip() and not line.startswith('data_directory'):
                    data_dir = line.strip()
                    break
            
            if data_dir:
                # Check if the problematic file exists
                file_path = os.path.join(data_dir, "base/16384/2602")
                if os.path.exists(file_path):
                    file_info = run_command(f"ls -la {file_path}", f"Checking file {file_path}")
                    f.write(file_info + "\n")
                else:
                    f.write(f"File {file_path} does not exist.\n")
            else:
                f.write("Could not determine PostgreSQL data directory.\n")
        except Exception as e:
            f.write(f"Error checking for problematic file: {str(e)}\n")
        
        # Try a simple query without vector operations
        f.write("Simple Query Test:\n")
        f.write("-" * 80 + "\n")
        simple_query_output = execute_query("SELECT id, title FROM papers LIMIT 5;", "Running simple query")
        f.write(simple_query_output + "\n")
        
        # Try a vector query without ORDER BY
        f.write("Vector Query Test (without ORDER BY):\n")
        f.write("-" * 80 + "\n")
        try:
            # Create a simple vector for testing
            test_vector = "[0]" + ",0" * 383  # 384-dimensional vector of zeros
            vector_query_output = execute_query(
                f"SELECT id, title, embedding <=> '{test_vector}'::vector AS similarity FROM papers LIMIT 5;",
                "Running vector query without ORDER BY"
            )
            f.write(vector_query_output + "\n")
        except Exception as e:
            f.write(f"Error running vector query: {str(e)}\n")
        
        # Check PostgreSQL configuration
        f.write("PostgreSQL Configuration:\n")
        f.write("-" * 80 + "\n")
        config_output = execute_query("""
            SELECT name, setting, unit, context, short_desc
            FROM pg_settings
            WHERE name IN ('work_mem', 'maintenance_work_mem', 'effective_cache_size', 'shared_buffers', 'max_connections');
        """, "Checking PostgreSQL configuration")
        f.write(config_output + "\n")
        
        # Check for table corruption
        f.write("Table Corruption Check:\n")
        f.write("-" * 80 + "\n")
        corruption_output = execute_query("VACUUM VERBOSE papers;", "Checking for table corruption")
        f.write(corruption_output + "\n")
        
        # Summary
        f.write("\nDiagnostic Summary:\n")
        f.write("-" * 80 + "\n")
        f.write("Diagnostic completed. Check the output above for any issues.\n")
        f.write("If you see errors related to 'base/16384/2602', this indicates a file system issue.\n")
        f.write("If you see errors related to vector operations, check the pgvector installation.\n")
        f.write("If you see lock-related errors, there might be concurrent operations causing issues.\n")
    
    print(f"Diagnostic completed. Results saved to {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 