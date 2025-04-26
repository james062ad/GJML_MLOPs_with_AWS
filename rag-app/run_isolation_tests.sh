#!/bin/bash

# Store the original directory
ORIGINAL_DIR=$(pwd)

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Original directory: $ORIGINAL_DIR"
echo "Created temporary directory: $TEMP_DIR"

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv "$TEMP_DIR/venv"
source "$TEMP_DIR/venv/bin/activate"

# Install required packages
echo "Installing required packages..."
pip install psycopg2-binary python-dotenv numpy

# Copy files to temporary directory
echo "Copying diagnostic script..."
cp "$ORIGINAL_DIR/isolate_postgres_issues.py" "$TEMP_DIR/"
echo "Copying .env file..."
cp "$ORIGINAL_DIR/.env" "$TEMP_DIR/"

# Change to temporary directory and run script
cd "$TEMP_DIR"
echo "Running diagnostic script..."
python3 isolate_postgres_issues.py

# Copy output file back to original directory
echo "Copying output file back to original directory..."
cp postgres_isolation_* "$ORIGINAL_DIR/"

# Clean up
echo "Cleaning up..."
cd "$ORIGINAL_DIR"
rm -rf "$TEMP_DIR"

# Find the most recent output file
OUTPUT_FILE=$(ls -t postgres_isolation_* | head -n 1)
echo "Diagnostics completed. Output file: $ORIGINAL_DIR/$OUTPUT_FILE" 