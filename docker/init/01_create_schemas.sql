-- Initialize test database with basic schemas and data
-- This script runs automatically when PostgreSQL containers start

\echo 'Creating test database initialization...'

-- Create additional schemas for testing
CREATE SCHEMA IF NOT EXISTS test_fixtures;
CREATE SCHEMA IF NOT EXISTS sample_data;

-- Set search path to include test schemas
ALTER DATABASE pgsd_test SET search_path TO public, test_fixtures, sample_data;

-- Create a basic table for connection testing
CREATE TABLE IF NOT EXISTS public.connection_test (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert a test record
INSERT INTO public.connection_test (test_name) VALUES ('Database initialization test')
ON CONFLICT DO NOTHING;

-- Create basic test fixtures in test_fixtures schema
CREATE TABLE IF NOT EXISTS test_fixtures.sample_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_fixtures.sample_posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES test_fixtures.sample_users(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better test performance
CREATE INDEX IF NOT EXISTS idx_sample_users_username ON test_fixtures.sample_users(username);
CREATE INDEX IF NOT EXISTS idx_sample_posts_user_id ON test_fixtures.sample_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_sample_posts_status ON test_fixtures.sample_posts(status);

\echo 'Database initialization completed.'