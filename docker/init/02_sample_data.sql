-- Insert sample data for testing
-- This script populates the test database with realistic test data

\echo 'Inserting sample test data...'

-- Insert sample users
INSERT INTO test_fixtures.sample_users (username, email, is_active) VALUES
    ('testuser1', 'test1@example.com', true),
    ('testuser2', 'test2@example.com', true),
    ('testuser3', 'test3@example.com', false),
    ('admin', 'admin@example.com', true)
ON CONFLICT (username) DO NOTHING;

-- Insert sample posts
INSERT INTO test_fixtures.sample_posts (user_id, title, content, status, published_at) VALUES
    (1, 'First Post', 'This is the content of the first post', 'published', CURRENT_TIMESTAMP - INTERVAL '1 day'),
    (1, 'Draft Post', 'This is a draft post', 'draft', NULL),
    (2, 'Second User Post', 'Content from second user', 'published', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
    (4, 'Admin Announcement', 'Important announcement from admin', 'published', CURRENT_TIMESTAMP - INTERVAL '1 hour')
ON CONFLICT DO NOTHING;

-- Create sample data in sample_data schema for more complex tests
CREATE TABLE IF NOT EXISTS sample_data.complex_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    data JSONB,
    tags TEXT[],
    metadata HSTORE,
    geom GEOMETRY(POINT, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert complex sample data
INSERT INTO sample_data.complex_table (name, data, tags) VALUES
    ('Sample 1', '{"type": "test", "value": 123}', ARRAY['tag1', 'tag2']),
    ('Sample 2', '{"type": "production", "value": 456}', ARRAY['tag2', 'tag3']),
    ('Sample 3', '{"type": "development", "value": 789}', ARRAY['tag1', 'tag3'])
ON CONFLICT DO NOTHING;

-- Create a view for testing view extraction
CREATE OR REPLACE VIEW test_fixtures.active_user_posts AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    p.id as post_id,
    p.title,
    p.content,
    p.published_at
FROM test_fixtures.sample_users u
JOIN test_fixtures.sample_posts p ON u.id = p.user_id
WHERE u.is_active = true AND p.status = 'published';

-- Create a function for testing function extraction
CREATE OR REPLACE FUNCTION test_fixtures.get_user_post_count(user_id_param INTEGER)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM test_fixtures.sample_posts
        WHERE user_id = user_id_param
    );
END;
$$ LANGUAGE plpgsql;

-- Create a trigger for testing trigger extraction
CREATE OR REPLACE FUNCTION test_fixtures.update_post_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_post_timestamp_trigger
    BEFORE UPDATE ON test_fixtures.sample_posts
    FOR EACH ROW
    EXECUTE FUNCTION test_fixtures.update_post_timestamp();

\echo 'Sample data insertion completed.'