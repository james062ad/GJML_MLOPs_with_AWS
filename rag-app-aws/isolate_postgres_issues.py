#!/usr/bin/env python3
"""
PostgreSQL Issue Isolation Script

This script performs targeted tests to isolate specific PostgreSQL issues
we're seeing with the vector operations and file system access.
"""

import os
import sys
import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import numpy as np

# Load environment variables from .env file
load_dotenv()

# Database connection details
DB_HOST = "localhost"
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

def get_connection():
    """Create and return a database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def test_basic_connection():
    """Test 1: Basic connection and version check"""
    print("\nTest 1: Basic Connection Test")
    print("-" * 80)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print("✓ Connection successful")
                print(f"✓ PostgreSQL version: {version}")
                return True
    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return False

def test_pgvector_installation():
    """Test 2: Check pgvector installation and version"""
    print("\nTest 2: pgvector Installation Test")
    print("-" * 80)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Check if extension exists
                cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                result = cur.fetchone()
                if result:
                    print("✓ pgvector extension is installed")
                    # Check version
                    cur.execute("SELECT default_version FROM pg_available_extensions WHERE name = 'vector';")
                    version = cur.fetchone()[0]
                    print(f"✓ pgvector version: {version}")
                    return True
                else:
                    print("✗ pgvector extension is not installed")
                    return False
    except Exception as e:
        print(f"✗ Error checking pgvector: {str(e)}")
        return False

def test_papers_table():
    """Test 3: Check papers table structure and data"""
    print("\nTest 3: Papers Table Test")
    print("-" * 80)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Check table existence
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'papers'
                    );
                """)
                if not cur.fetchone()[0]:
                    print("✗ Papers table does not exist")
                    return False
                
                print("✓ Papers table exists")
                
                # Check column structure
                cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'papers'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                print("\nTable structure:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]}")
                
                # Check row count
                cur.execute("SELECT COUNT(*) FROM papers;")
                count = cur.fetchone()[0]
                print(f"\n✓ Total rows: {count}")
                
                # Check for null embeddings
                cur.execute("SELECT COUNT(*) FROM papers WHERE embedding IS NULL;")
                null_count = cur.fetchone()[0]
                print(f"✓ Rows with NULL embeddings: {null_count}")
                
                return True
    except Exception as e:
        print(f"✗ Error checking papers table: {str(e)}")
        return False

def test_vector_operations():
    """Test 4: Test vector operations"""
    print("\nTest 4: Vector Operations Test")
    print("-" * 80)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # First, check vector dimension
                cur.execute("""
                    SELECT embedding::vector
                    FROM papers
                    WHERE embedding IS NOT NULL
                    LIMIT 1;
                """)
                sample_vector = cur.fetchone()
                if not sample_vector:
                    print("✗ No vectors found in the database")
                    return False
                
                vector_dim = len(sample_vector[0])
                print(f"✓ Vector dimension in database: {vector_dim}")
                
                # Create a test vector with the same dimension
                test_vector = ','.join(['0'] * vector_dim)
                test_vector = f"[{test_vector}]"
                
                # Test simple vector comparison
                cur.execute(f"""
                    SELECT id, embedding <=> '{test_vector}'::vector AS distance
                    FROM papers
                    WHERE embedding IS NOT NULL
                    LIMIT 1;
                """)
                result = cur.fetchone()
                if result:
                    print("✓ Vector comparison operation successful")
                    print(f"✓ Sample distance calculation: {result[1]}")
                    return True
                else:
                    print("✗ Vector comparison returned no results")
                    return False
    except Exception as e:
        print(f"✗ Error in vector operations: {str(e)}")
        return False

def test_concurrent_access():
    """Test 5: Test concurrent access"""
    print("\nTest 5: Concurrent Access Test")
    print("-" * 80)
    try:
        # Create two connections
        conn1 = get_connection()
        conn2 = get_connection()
        
        cur1 = conn1.cursor()
        cur2 = conn2.cursor()
        
        # Test 1: Simple concurrent reads
        print("Testing concurrent reads...")
        cur1.execute("SELECT COUNT(*) FROM papers;")
        cur2.execute("SELECT COUNT(*) FROM papers;")
        
        count1 = cur1.fetchone()[0]
        count2 = cur2.fetchone()[0]
        
        print(f"✓ Both connections can read (counts: {count1}, {count2})")
        
        # Test 2: Check for locks
        print("\nChecking for locks...")
        cur1.execute("""
            SELECT blocked_locks.pid AS blocked_pid,
                   blocking_locks.pid AS blocking_pid
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_locks blocking_locks 
                ON blocking_locks.locktype = blocked_locks.locktype
            WHERE NOT blocked_locks.granted;
        """)
        
        locks = cur1.fetchall()
        if not locks:
            print("✓ No locks detected")
        else:
            print(f"! Found {len(locks)} locks")
            for lock in locks:
                print(f"  - Blocked PID: {lock[0]}, Blocking PID: {lock[1]}")
        
        conn1.close()
        conn2.close()
        return True
    except Exception as e:
        print(f"✗ Error in concurrent access test: {str(e)}")
        return False

def main():
    """Run all tests and summarize results"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"postgres_isolation_{timestamp}.txt"
    
    # Redirect stdout to both console and file
    class Logger:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w")
        
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            
        def flush(self):
            self.terminal.flush()
            self.log.flush()
    
    sys.stdout = Logger(output_file)
    
    print(f"PostgreSQL Issue Isolation Report - {datetime.datetime.now()}")
    print("=" * 80)
    
    results = {
        "Basic Connection": test_basic_connection(),
        "pgvector Installation": test_pgvector_installation(),
        "Papers Table": test_papers_table(),
        "Vector Operations": test_vector_operations(),
        "Concurrent Access": test_concurrent_access()
    }
    
    print("\nTest Summary")
    print("=" * 80)
    for test, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test}: {status}")
    
    print(f"\nDetailed results saved to {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 