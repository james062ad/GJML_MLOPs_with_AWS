-- Create the database if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mydb') THEN
      CREATE DATABASE mydb;
   END IF;
END
$do$; 