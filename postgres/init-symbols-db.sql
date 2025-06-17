-- Initialize Symbol Server database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Symbols table for storing symbol metadata
CREATE TABLE IF NOT EXISTS symbols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_identifier VARCHAR(50) NOT NULL,
    ios_version VARCHAR(20) NOT NULL,
    build_version VARCHAR(20) NOT NULL,
    kernel_path TEXT NOT NULL,
    symbols_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_identifier, ios_version, build_version)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_symbols_device_version 
ON symbols(device_identifier, ios_version, build_version);

-- Symbol cache table
CREATE TABLE IF NOT EXISTS symbol_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    symbol_data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for cache lookups
CREATE INDEX IF NOT EXISTS idx_symbol_cache_key ON symbol_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_symbol_cache_expires ON symbol_cache(expires_at);

-- Create symbol admin user (already created by Docker)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO symbols_admin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO symbols_admin;
