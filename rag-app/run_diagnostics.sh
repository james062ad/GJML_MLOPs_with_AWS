#!/bin/bash
# Script to run PostgreSQL diagnostics in a temporary environment

# Exit on error
set -e

# Store the original directory
ORIGINAL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Original directory: $ORIGINAL_DIR"

# Create a temporary directory for the virtual environment
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Create and activate a virtual environment
echo "Creating virtual environment..."
python3 -m venv "$TEMP_DIR/venv"
source "$TEMP_DIR/venv/bin/activate"

# Install required packages
echo "Installing required packages..."
pip install psycopg2-binary python-dotenv

# Copy the diagnostic script to the temporary directory
echo "Copying diagnostic script..."
cp "$ORIGINAL_DIR/diagnose_postgres.py" "$TEMP_DIR/"

# Copy the .env file if it exists
if [ -f "$ORIGINAL_DIR/.env" ]; then
    echo "Copying .env file..."
    cp "$ORIGINAL_DIR/.env" "$TEMP_DIR/"
fi

# Change to the temporary directory
cd "$TEMP_DIR"

# Run the diagnostic script
echo "Running diagnostic script..."
python diagnose_postgres.py

# Get the output file name
OUTPUT_FILE=$(ls postgres_diagnostic_*.txt)
echo "Diagnostic output saved to: $OUTPUT_FILE"

# Copy the output file back to the original directory
echo "Copying output file back to original directory..."
cp "$TEMP_DIR/$OUTPUT_FILE" "$ORIGINAL_DIR/"

# Deactivate the virtual environment
deactivate

# Clean up
echo "Cleaning up..."
rm -rf "$TEMP_DIR"

echo "Diagnostics completed. Output file: $ORIGINAL_DIR/$OUTPUT_FILE" 