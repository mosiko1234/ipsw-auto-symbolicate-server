-- Initialize symbols database

CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    library VARCHAR(255) NOT NULL,
    device_model VARCHAR(100) NOT NULL,
    os_version VARCHAR(50) NOT NULL,
    architecture VARCHAR(20) DEFAULT 'arm64',
    symbol_name VARCHAR(500) NOT NULL,
    start_address BIGINT NOT NULL,
    end_address BIGINT NOT NULL,
    symbol_offset BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_symbols_library ON symbols(library);
CREATE INDEX IF NOT EXISTS idx_symbols_device ON symbols(device_model);
CREATE INDEX IF NOT EXISTS idx_symbols_os_version ON symbols(os_version);
CREATE INDEX IF NOT EXISTS idx_symbols_address ON symbols(start_address, end_address);
CREATE INDEX IF NOT EXISTS idx_symbols_lookup ON symbols(library, device_model, os_version, start_address, end_address);

-- Insert some sample data for testing
INSERT INTO symbols (library, device_model, os_version, symbol_name, start_address, end_address, symbol_offset) VALUES
('libsystem_c.dylib', 'iPhone12,1', '14.5', 'malloc', 4294967296, 4294967552, 4294967296),
('libsystem_c.dylib', 'iPhone12,1', '14.5', 'free', 4294967552, 4294967808, 4294967552),
('Foundation', 'iPhone12,1', '14.5', '-[NSString stringWithFormat:]', 4563402752, 4563403264, 4563402752),
('UIKit', 'iPhone12,1', '14.5', '-[UIViewController viewDidLoad]', 4831838208, 4831838976, 4831838208)
ON CONFLICT DO NOTHING;

-- Create a table for crash reports (optional)
CREATE TABLE IF NOT EXISTS crash_reports (
    id SERIAL PRIMARY KEY,
    process_name VARCHAR(255),
    device_model VARCHAR(100),
    os_version VARCHAR(50),
    build_id VARCHAR(100),
    crashed_thread INTEGER,
    crash_content TEXT,
    symbolicated_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_crash_reports_device ON crash_reports(device_model);
CREATE INDEX IF NOT EXISTS idx_crash_reports_os ON crash_reports(os_version);
CREATE INDEX IF NOT EXISTS idx_crash_reports_created ON crash_reports(created_at);

-- Table for tracking scanned IPSW files
CREATE TABLE IF NOT EXISTS scanned_ipsw (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(1024) NOT NULL UNIQUE,
    file_name VARCHAR(255) NOT NULL,
    device_model VARCHAR(100),
    os_version VARCHAR(50),
    build_id VARCHAR(100),
    architecture VARCHAR(20) DEFAULT 'arm64',
    file_size_bytes BIGINT,
    scan_status VARCHAR(20) DEFAULT 'pending', -- pending, scanning, completed, failed
    symbols_extracted INTEGER DEFAULT 0,
    dyld_caches_found INTEGER DEFAULT 0,
    scan_started_at TIMESTAMP,
    scan_completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for scanned IPSW lookup
CREATE INDEX IF NOT EXISTS idx_scanned_ipsw_device ON scanned_ipsw(device_model);
CREATE INDEX IF NOT EXISTS idx_scanned_ipsw_os ON scanned_ipsw(os_version);
CREATE INDEX IF NOT EXISTS idx_scanned_ipsw_status ON scanned_ipsw(scan_status);
CREATE INDEX IF NOT EXISTS idx_scanned_ipsw_path ON scanned_ipsw(file_path);

-- Add foreign key reference to scanned IPSW in symbols table
ALTER TABLE symbols ADD COLUMN IF NOT EXISTS ipsw_scan_id INTEGER REFERENCES scanned_ipsw(id);
CREATE INDEX IF NOT EXISTS idx_symbols_ipsw_scan ON symbols(ipsw_scan_id); 