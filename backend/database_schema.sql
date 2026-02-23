-- Alarm Fatigue Monitoring System - Database Schema
-- Run this SQL in Supabase SQL Editor

-- ============================================
-- TABLE: patients
-- Stores patient admission records with complete medical information
-- ============================================
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL CHECK (age > 0 AND age < 150),
    gender VARCHAR(20),
    blood_type VARCHAR(10),
    weight FLOAT,
    height FLOAT,
    problem TEXT NOT NULL,
    medical_history JSONB,
    allergies JSONB,
    current_medications JSONB,
    emergency_contact VARCHAR(255),
    emergency_phone VARCHAR(50),
    patient_type VARCHAR(20) NOT NULL CHECK (patient_type IN ('GENERAL', 'CRITICAL')),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISCHARGED')),
    demo_mode BOOLEAN DEFAULT FALSE,
    demo_scenario VARCHAR(50),
    admission_time TIMESTAMP NOT NULL DEFAULT NOW(),
    discharge_time TIMESTAMP
);

-- Index for querying active patients
CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(status);

-- ============================================
-- TABLE: band_assignment
-- Tracks which band is assigned to which patient
-- ============================================
CREATE TABLE IF NOT EXISTS band_assignment (
    id SERIAL PRIMARY KEY,
    band_id VARCHAR(50) NOT NULL,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    released_at TIMESTAMP
);

-- Index for active band queries (where released_at IS NULL)
CREATE INDEX IF NOT EXISTS idx_band_active 
ON band_assignment(band_id) 
WHERE released_at IS NULL;

-- Index for patient lookup
CREATE INDEX IF NOT EXISTS idx_band_patient ON band_assignment(patient_id);

-- ============================================
-- TABLE: alarm_events
-- Logs all alarm decisions and routing
-- ============================================
CREATE TABLE IF NOT EXISTS alarm_events (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    vitals JSONB NOT NULL,
    alarm_status VARCHAR(50) NOT NULL,
    proximity_alert_sent BOOLEAN DEFAULT FALSE,
    nurse_in_proximity BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for patient alarm history queries
CREATE INDEX IF NOT EXISTS idx_alarm_patient_time 
ON alarm_events(patient_id, timestamp DESC);

-- Index for alarm status queries
CREATE INDEX IF NOT EXISTS idx_alarm_status ON alarm_events(alarm_status);

-- ============================================
-- TABLE: nurse_sessions
-- Tracks nurse devices for proximity monitoring
-- ============================================
CREATE TABLE IF NOT EXISTS nurse_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    device_info TEXT,
    registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_proximity_update TIMESTAMP,
    ble_devices_nearby JSONB
);

-- Index for proximity queries
CREATE INDEX IF NOT EXISTS idx_nurse_proximity 
ON nurse_sessions(last_proximity_update)
WHERE last_proximity_update IS NOT NULL;

-- ============================================
-- TABLE: vital_logs
-- Stores patient vital signs history
-- ============================================
CREATE TABLE IF NOT EXISTS vital_logs (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    heart_rate INTEGER,
    spo2 INTEGER,
    temperature FLOAT,
    bp_systolic INTEGER,
    bp_diastolic INTEGER,
    respiratory_rate INTEGER,
    blood_glucose INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for patient vital history queries
CREATE INDEX IF NOT EXISTS idx_vital_patient_time 
ON vital_logs(patient_id, timestamp DESC);

-- ============================================
-- SAMPLE QUERIES FOR TESTING
-- ============================================

-- Check if tables were created successfully
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('patients', 'band_assignment', 'alarm_events', 'nurse_sessions', 'vital_logs');

-- View all indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public';

-- ============================================
-- USEFUL QUERIES FOR MONITORING
-- ============================================

-- Get currently active patient with band assignment
-- SELECT p.*, ba.band_id, ba.assigned_at
-- FROM patients p
-- JOIN band_assignment ba ON p.id = ba.patient_id
-- WHERE p.status = 'ACTIVE' AND ba.released_at IS NULL;

-- Get alarm event history for a patient
-- SELECT * FROM alarm_events WHERE patient_id = 1 ORDER BY timestamp DESC LIMIT 20;

-- Check band availability
-- SELECT * FROM band_assignment WHERE band_id = 'BAND_01' AND released_at IS NULL;

-- Get active nurse sessions in proximity (last 10 seconds)
-- SELECT * FROM nurse_sessions 
-- WHERE last_proximity_update > NOW() - INTERVAL '10 seconds';
