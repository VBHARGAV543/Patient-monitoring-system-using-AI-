-- Migration Script: Add Medical Fields and Vital Logs
-- Run this in Supabase SQL Editor to update existing database

-- Step 1: Add medical fields to patients table
ALTER TABLE patients 
ADD COLUMN IF NOT EXISTS gender VARCHAR(20),
ADD COLUMN IF NOT EXISTS blood_type VARCHAR(10),
ADD COLUMN IF NOT EXISTS weight FLOAT,
ADD COLUMN IF NOT EXISTS height FLOAT,
ADD COLUMN IF NOT EXISTS medical_history JSONB,
ADD COLUMN IF NOT EXISTS allergies JSONB,
ADD COLUMN IF NOT EXISTS current_medications JSONB,
ADD COLUMN IF NOT EXISTS emergency_contact VARCHAR(255),
ADD COLUMN IF NOT EXISTS emergency_phone VARCHAR(50);

-- Step 2: Create vital_logs table
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

-- Step 3: Create index for vital_logs
CREATE INDEX IF NOT EXISTS idx_vital_patient_time 
ON vital_logs(patient_id, timestamp DESC);

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'patients'
ORDER BY ordinal_position;

-- Check if vital_logs table was created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'vital_logs';

-- Success message
SELECT 'Migration completed successfully! All medical fields and vital_logs table are now available.' AS status;
