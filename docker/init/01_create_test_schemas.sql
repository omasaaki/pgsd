-- Test schema initialization for PGSD integration tests
-- This script runs automatically when PostgreSQL containers start

\echo 'Creating test schemas and sample data...'

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS test_schema_simple;
CREATE SCHEMA IF NOT EXISTS test_schema_complex;

-- Simple test schema
CREATE TABLE test_schema_simple.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_schema_simple.posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES test_schema_simple.users(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    published_at TIMESTAMP
);

-- Insert sample data
INSERT INTO test_schema_simple.users (username, email) VALUES 
    ('john_doe', 'john@example.com'),
    ('jane_smith', 'jane@example.com'),
    ('admin_user', 'admin@example.com');

INSERT INTO test_schema_simple.posts (user_id, title, content, published_at) VALUES 
    (1, 'First Post', 'This is the first post content', NOW()),
    (1, 'Second Post', 'Another post by John', NOW() - INTERVAL '1 day'),
    (2, 'Jane''s Post', 'Post by Jane Smith', NOW() - INTERVAL '2 hours');

-- Complex test schema with advanced features
CREATE TYPE test_schema_complex.status_type AS ENUM ('active', 'inactive', 'pending');

CREATE TABLE test_schema_complex.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status test_schema_complex.status_type DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_active_category UNIQUE (name)
);

CREATE TABLE test_schema_complex.products (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES test_schema_complex.categories(id),
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) CHECK (price > 0),
    metadata JSONB,
    search_vector TSVECTOR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_products_category ON test_schema_complex.products(category_id);
CREATE INDEX idx_products_search ON test_schema_complex.products USING gin(search_vector);
CREATE INDEX idx_products_metadata ON test_schema_complex.products USING gin(metadata);

-- Create view
CREATE VIEW test_schema_complex.active_products AS
SELECT p.*, c.name as category_name
FROM test_schema_complex.products p
JOIN test_schema_complex.categories c ON p.category_id = c.id
WHERE c.status = 'active';

-- Insert sample data
INSERT INTO test_schema_complex.categories (name, description, status) VALUES 
    ('Electronics', 'Electronic devices and gadgets', 'active'),
    ('Books', 'Physical and digital books', 'active'),
    ('Clothing', 'Apparel and accessories', 'pending');

INSERT INTO test_schema_complex.products (category_id, name, price, metadata) VALUES 
    (1, 'Laptop Computer', 999.99, '{"brand": "TechCorp", "model": "X1", "warranty": "2 years"}'),
    (1, 'Smartphone', 599.99, '{"brand": "PhoneCorp", "model": "S10", "color": "black"}'),
    (2, 'Programming Book', 49.99, '{"author": "John Smith", "pages": 350, "language": "Python"}'),
    (2, 'Database Guide', 39.99, '{"author": "Jane Doe", "pages": 280, "language": "SQL"}');

-- Update search vectors
UPDATE test_schema_complex.products 
SET search_vector = to_tsvector('english', name || ' ' || COALESCE(metadata->>'brand', ''));

-- Create some functions and triggers for comprehensive testing
CREATE OR REPLACE FUNCTION test_schema_complex.update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = to_tsvector('english', NEW.name || ' ' || COALESCE(NEW.metadata->>'brand', ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_product_search_vector
    BEFORE INSERT OR UPDATE ON test_schema_complex.products
    FOR EACH ROW EXECUTE FUNCTION test_schema_complex.update_search_vector();

-- Create sequences for testing
CREATE SEQUENCE test_schema_complex.custom_id_seq START 1000;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA test_schema_simple TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA test_schema_simple TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA test_schema_complex TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA test_schema_complex TO test_user;
GRANT USAGE ON SCHEMA test_schema_simple TO test_user;
GRANT USAGE ON SCHEMA test_schema_complex TO test_user;

\echo 'Test schemas created successfully!'