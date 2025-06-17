-- IPSW Symbol Server Database Initialization
CREATE DATABASE IF NOT EXISTS symbolserver;

-- Create symbols table
CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    device_model VARCHAR(50) NOT NULL,
    ios_version VARCHAR(20) NOT NULL,
    build_version VARCHAR(20) NOT NULL,
    symbol_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_symbols_device_version ON symbols(device_model, ios_version, build_version);

-- Create cache table
CREATE TABLE IF NOT EXISTS cache_metadata (
    cache_key VARCHAR(50) PRIMARY KEY,
    device_model VARCHAR(50) NOT NULL,
    ios_version VARCHAR(20) NOT NULL,
    build_version VARCHAR(20) NOT NULL,
    access_count INTEGER DEFAULT 1,
    last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_last_access ON cache_metadata(last_access);

-- Create S3 download tracking table
CREATE TABLE IF NOT EXISTS s3_downloads (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    s3_key VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_s3_downloads_status ON s3_downloads(status);
CREATE INDEX IF NOT EXISTS idx_s3_downloads_filename ON s3_downloads(filename);
