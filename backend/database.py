"""
Supabase PostgreSQL Database Layer
Handles patient management, band assignment, alarm events, and nurse proximity sessions
"""
import asyncpg
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, Dict, List, Any
import json

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BAND_ID = os.getenv("BAND_ID", "BAND_01")

# Global connection pool
pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Initialize database connection pool and create tables"""
    global pool
    
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Use transaction pooler (port 5432) instead of session pooler to avoid connection limits
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=50)
    
    # Create tables if they don't exist
    async with pool.acquire() as conn:
        # Patients table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                age INTEGER NOT NULL,
                gender VARCHAR(10),
                blood_type VARCHAR(5),
                weight FLOAT,
                height FLOAT,
                problem TEXT NOT NULL,
                medical_history JSONB,
                allergies JSONB,
                current_medications JSONB,
                emergency_contact VARCHAR(255),
                emergency_phone VARCHAR(20),
                patient_type VARCHAR(20) NOT NULL CHECK (patient_type IN ('GENERAL', 'CRITICAL')),
                status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISCHARGED')),
                demo_mode BOOLEAN DEFAULT FALSE,
                demo_scenario VARCHAR(50),
                disease VARCHAR(255),
                body_strength VARCHAR(20),
                genetic_condition VARCHAR(50),
                admission_time TIMESTAMP NOT NULL DEFAULT NOW(),
                discharge_time TIMESTAMP
            );
        """)
        
        # Vital signs logs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS vital_logs (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
                heart_rate FLOAT,
                spo2 FLOAT,
                temperature FLOAT,
                bp_systolic FLOAT,
                bp_diastolic FLOAT,
                respiratory_rate FLOAT,
                blood_glucose FLOAT,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """)
        
        # Create index for vital logs queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_vital_logs_patient_time 
            ON vital_logs(patient_id, timestamp DESC);
        """)
        
        # Band assignment table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS band_assignment (
                id SERIAL PRIMARY KEY,
                band_id VARCHAR(50) NOT NULL,
                patient_id INTEGER NOT NULL REFERENCES patients(id),
                assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
                released_at TIMESTAMP,
                CONSTRAINT unique_active_band UNIQUE (band_id, patient_id)
            );
        """)
        
        # Create index for active band queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_band_active 
            ON band_assignment(band_id) 
            WHERE released_at IS NULL;
        """)
        
        # Alarm events table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alarm_events (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER NOT NULL REFERENCES patients(id),
                vitals JSONB NOT NULL,
                alarm_status VARCHAR(50) NOT NULL,
                proximity_alert_sent BOOLEAN DEFAULT FALSE,
                nurse_in_proximity BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """)
        
        # Create index for patient alarm history queries
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_alarm_patient_time 
            ON alarm_events(patient_id, timestamp DESC);
        """)
        
        # Nurse sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS nurse_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                device_info TEXT,
                registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
                last_proximity_update TIMESTAMP,
                ble_devices_nearby JSONB
            );
        """)
        
        print("✅ Database tables initialized successfully")


async def close_db():
    """Close database connection pool"""
    global pool
    if pool:
        await pool.close()
        print("✅ Database connection pool closed")


async def get_connection():
    """Get database connection from pool"""
    if not pool:
        await init_db()
    return pool


# ========== PATIENT CRUD OPERATIONS ==========

async def create_patient(
    name: str,
    age: int,
    problem: str,
    patient_type: str,
    demo_mode: bool = False,
    demo_scenario: Optional[str] = None,
    gender: Optional[str] = None,
    blood_type: Optional[str] = None,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    medical_history: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None,
    current_medications: Optional[List[Dict[str, str]]] = None,
    emergency_contact: Optional[str] = None,
    emergency_phone: Optional[str] = None,
    disease: Optional[str] = None,
    body_strength: Optional[str] = None,
    genetic_condition: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new patient record with complete medical information"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO patients (
                name, age, problem, patient_type, demo_mode, demo_scenario,
                gender, blood_type, weight, height, medical_history, allergies,
                current_medications, emergency_contact, emergency_phone,
                disease, body_strength, genetic_condition
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING id, name, age, gender, blood_type, weight, height, problem, 
                      medical_history, allergies, current_medications, emergency_contact, 
                      emergency_phone, patient_type, status, demo_mode, demo_scenario, 
                      disease, body_strength, genetic_condition, admission_time
        """, name, age, problem, patient_type, demo_mode, demo_scenario,
            gender, blood_type, weight, height,
            json.dumps(medical_history) if medical_history else None,
            json.dumps(allergies) if allergies else None,
            json.dumps(current_medications) if current_medications else None,
            emergency_contact, emergency_phone,
            disease, body_strength, genetic_condition)
        
        result = dict(row)
        # Parse JSON fields
        if result.get('medical_history'):
            result['medical_history'] = json.loads(result['medical_history']) if isinstance(result['medical_history'], str) else result['medical_history']
        if result.get('allergies'):
            result['allergies'] = json.loads(result['allergies']) if isinstance(result['allergies'], str) else result['allergies']
        if result.get('current_medications'):
            result['current_medications'] = json.loads(result['current_medications']) if isinstance(result['current_medications'], str) else result['current_medications']
        
        return result


async def get_patient_by_id(patient_id: int) -> Optional[Dict[str, Any]]:
    """Get patient by ID with all medical information"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, name, age, gender, blood_type, weight, height, problem, 
                   medical_history, allergies, current_medications, emergency_contact, 
                   emergency_phone, patient_type, status, demo_mode, demo_scenario, 
                   disease, body_strength, genetic_condition,
                   admission_time, discharge_time
            FROM patients
            WHERE id = $1
        """, patient_id)
        
        if not row:
            return None
        
        result = dict(row)
        # Parse JSON fields
        if result.get('medical_history'):
            result['medical_history'] = json.loads(result['medical_history']) if isinstance(result['medical_history'], str) else result['medical_history']
        if result.get('allergies'):
            result['allergies'] = json.loads(result['allergies']) if isinstance(result['allergies'], str) else result['allergies']
        if result.get('current_medications'):
            result['current_medications'] = json.loads(result['current_medications']) if isinstance(result['current_medications'], str) else result['current_medications']
        
        return result


async def get_active_patient() -> Optional[Dict[str, Any]]:
    """Get currently active patient (only one should exist) with all medical information"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT p.id, p.name, p.age, p.gender, p.blood_type, p.weight, p.height, 
                   p.problem, p.medical_history, p.allergies, p.current_medications, 
                   p.emergency_contact, p.emergency_phone, p.patient_type, p.status, 
                   p.demo_mode, p.demo_scenario, p.disease, p.body_strength, p.genetic_condition,
                   p.admission_time, p.discharge_time,
                   ba.band_id, ba.assigned_at
            FROM patients p
            JOIN band_assignment ba ON p.id = ba.patient_id
            WHERE p.status = 'ACTIVE' AND ba.released_at IS NULL
            ORDER BY p.admission_time DESC
            LIMIT 1
        """)
        
        if not row:
            return None
        
        result = dict(row)
        # Parse JSON fields
        if result.get('medical_history'):
            result['medical_history'] = json.loads(result['medical_history']) if isinstance(result['medical_history'], str) else result['medical_history']
        if result.get('allergies'):
            result['allergies'] = json.loads(result['allergies']) if isinstance(result['allergies'], str) else result['allergies']
        if result.get('current_medications'):
            result['current_medications'] = json.loads(result['current_medications']) if isinstance(result['current_medications'], str) else result['current_medications']
        
        return result


async def discharge_patient(patient_id: int) -> bool:
    """Discharge a patient and release band"""
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Update patient status
            result = await conn.execute("""
                UPDATE patients
                SET status = 'DISCHARGED', discharge_time = NOW()
                WHERE id = $1 AND status = 'ACTIVE'
            """, patient_id)
            
            if result == "UPDATE 0":
                return False
            
            # Release band assignment
            await conn.execute("""
                UPDATE band_assignment
                SET released_at = NOW()
                WHERE patient_id = $1 AND released_at IS NULL
            """, patient_id)
            
            # Log the discharge count (no limit - keeping all records)
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM patients WHERE status = 'DISCHARGED'
            """)
            print(f"📊 Total discharged patients in database: {count}")
            
            return True


# ========== BAND ASSIGNMENT OPERATIONS ==========

async def assign_band_to_patient(patient_id: int, band_id: str = None) -> Dict[str, Any]:
    """Assign BAND_01 to a patient"""
    if band_id is None:
        band_id = BAND_ID
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO band_assignment (band_id, patient_id)
            VALUES ($1, $2)
            RETURNING id, band_id, patient_id, assigned_at
        """, band_id, patient_id)
        
        return dict(row)


async def is_band_available(band_id: str = None) -> bool:
    """Check if BAND_01 is available (not assigned to any active patient)"""
    if band_id is None:
        band_id = BAND_ID
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM band_assignment
            WHERE band_id = $1 AND released_at IS NULL
        """, band_id)
        
        return row is None


async def get_patient_by_band(band_id: str = None) -> Optional[Dict[str, Any]]:
    """Get active patient assigned to a band with all medical information"""
    if band_id is None:
        band_id = BAND_ID
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT p.id, p.name, p.age, p.gender, p.blood_type, p.weight, p.height,
                   p.problem, p.medical_history, p.allergies, p.current_medications,
                   p.emergency_contact, p.emergency_phone, p.patient_type, p.status,
                   p.demo_mode, p.demo_scenario, p.admission_time, p.discharge_time,
                   ba.band_id, ba.assigned_at
            FROM patients p
            JOIN band_assignment ba ON p.id = ba.patient_id
            WHERE ba.band_id = $1 AND ba.released_at IS NULL AND p.status = 'ACTIVE'
        """, band_id)
        
        if not row:
            return None
        
        result = dict(row)
        # Parse JSON fields
        if result.get('medical_history'):
            result['medical_history'] = json.loads(result['medical_history']) if isinstance(result['medical_history'], str) else result['medical_history']
        if result.get('allergies'):
            result['allergies'] = json.loads(result['allergies']) if isinstance(result['allergies'], str) else result['allergies']
        if result.get('current_medications'):
            result['current_medications'] = json.loads(result['current_medications']) if isinstance(result['current_medications'], str) else result['current_medications']
        
        return result


# ========== ALARM EVENT OPERATIONS ==========

async def log_alarm_event(
    patient_id: int,
    vitals: Dict[str, Any],
    alarm_status: str,
    proximity_alert_sent: bool = False,
    nurse_in_proximity: bool = False
) -> Dict[str, Any]:
    """Log an alarm event"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO alarm_events (patient_id, vitals, alarm_status, proximity_alert_sent, nurse_in_proximity)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, patient_id, vitals, alarm_status, proximity_alert_sent, nurse_in_proximity, timestamp
        """, patient_id, json.dumps(vitals), alarm_status, proximity_alert_sent, nurse_in_proximity)
        
        result = dict(row)
        result['vitals'] = json.loads(result['vitals']) if isinstance(result['vitals'], str) else result['vitals']
        return result


async def get_patient_alarm_history(patient_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get alarm event history for a patient"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, patient_id, vitals, alarm_status, proximity_alert_sent, nurse_in_proximity, timestamp
            FROM alarm_events
            WHERE patient_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """, patient_id, limit)
        
        results = [dict(row) for row in rows]
        for result in results:
            result['vitals'] = json.loads(result['vitals']) if isinstance(result['vitals'], str) else result['vitals']
        return results


# ========== NURSE SESSION OPERATIONS ==========

async def create_nurse_session(session_id: str, device_info: str = None) -> Dict[str, Any]:
    """Register a new nurse session"""
    print(f"🔵 DB: Creating nurse session - session_id: {session_id}, device_info: {device_info}")
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO nurse_sessions (session_id, device_info)
                VALUES ($1, $2)
                ON CONFLICT (session_id) DO UPDATE 
                SET registered_at = NOW()
                RETURNING session_id, device_info, registered_at
            """, session_id, device_info)
            
            result = dict(row)
            print(f"✅ DB: Nurse session created successfully: {result}")
            return result
    except Exception as e:
        print(f"❌ DB: Failed to create nurse session: {type(e).__name__}: {str(e)}")
        raise


async def update_nurse_proximity(session_id: str, ble_devices: List[str]) -> bool:
    """Update nurse proximity data with detected BLE devices"""
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE nurse_sessions
            SET last_proximity_update = NOW(),
                ble_devices_nearby = $2
            WHERE session_id = $1
        """, session_id, json.dumps(ble_devices))
        
        return result != "UPDATE 0"


async def get_nurse_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get nurse session by ID"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT session_id, device_info, registered_at, last_proximity_update, ble_devices_nearby
            FROM nurse_sessions
            WHERE session_id = $1
        """, session_id)
        
        if row:
            result = dict(row)
            result['ble_devices_nearby'] = json.loads(result['ble_devices_nearby']) if result['ble_devices_nearby'] else []
            return result
        return None


async def check_nurse_proximity(band_id: str = None) -> bool:
    """Check if any nurse is in BLE proximity of the band (within last 10 seconds)"""
    if band_id is None:
        band_id = BAND_ID
    
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT session_id
            FROM nurse_sessions
            WHERE last_proximity_update > NOW() - INTERVAL '10 seconds'
            AND ble_devices_nearby::jsonb ? $1
            LIMIT 1
        """, band_id)
        
        return row is not None


async def get_nurses_in_proximity(band_id: str = None) -> List[str]:
    """Get list of nurse session IDs currently in proximity to the band"""
    if band_id is None:
        band_id = BAND_ID
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT session_id
            FROM nurse_sessions
            WHERE last_proximity_update > NOW() - INTERVAL '10 seconds'
            AND ble_devices_nearby::jsonb ? $1
        """, band_id)
        
        return [row['session_id'] for row in rows]


# ========== DISCHARGED PATIENT HISTORY OPERATIONS ==========

async def get_discharged_patients(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get discharged patient history (all records by default, optional limit) with medical information"""
    async with pool.acquire() as conn:
        if limit:
            rows = await conn.fetch("""
                SELECT id, name, age, gender, blood_type, weight, height, problem, 
                       medical_history, allergies, current_medications, emergency_contact,
                       emergency_phone, patient_type, status, demo_mode, demo_scenario,
                       admission_time, discharge_time
                FROM patients
                WHERE status = 'DISCHARGED'
                ORDER BY discharge_time DESC
                LIMIT $1
            """, limit)
        else:
            rows = await conn.fetch("""
                SELECT id, name, age, gender, blood_type, weight, height, problem, 
                       medical_history, allergies, current_medications, emergency_contact,
                       emergency_phone, patient_type, status, demo_mode, demo_scenario,
                       admission_time, discharge_time
                FROM patients
                WHERE status = 'DISCHARGED'
                ORDER BY discharge_time DESC
            """)
        
        results = [dict(row) for row in rows]
        # Parse JSON fields for all results
        for result in results:
            if result.get('medical_history'):
                result['medical_history'] = json.loads(result['medical_history']) if isinstance(result['medical_history'], str) else result['medical_history']
            if result.get('allergies'):
                result['allergies'] = json.loads(result['allergies']) if isinstance(result['allergies'], str) else result['allergies']
            if result.get('current_medications'):
                result['current_medications'] = json.loads(result['current_medications']) if isinstance(result['current_medications'], str) else result['current_medications']
        
        return results


async def get_patient_statistics() -> Dict[str, Any]:
    """Get patient admission/discharge statistics"""
    async with pool.acquire() as conn:
        # Total counts
        total_admitted = await conn.fetchval("""
            SELECT COUNT(*) FROM patients
        """)
        
        active_patients = await conn.fetchval("""
            SELECT COUNT(*) FROM patients WHERE status = 'ACTIVE'
        """)
        
        discharged_patients = await conn.fetchval("""
            SELECT COUNT(*) FROM patients WHERE status = 'DISCHARGED'
        """)
        
        # Average stay duration for discharged patients
        avg_stay = await conn.fetchval("""
            SELECT AVG(EXTRACT(EPOCH FROM (discharge_time - admission_time))/3600) as avg_hours
            FROM patients
            WHERE status = 'DISCHARGED' AND discharge_time IS NOT NULL
        """)
        
        # Patient type breakdown
        general_count = await conn.fetchval("""
            SELECT COUNT(*) FROM patients WHERE patient_type = 'GENERAL'
        """)
        
        critical_count = await conn.fetchval("""
            SELECT COUNT(*) FROM patients WHERE patient_type = 'CRITICAL'
        """)
        
        return {
            "total_admitted": total_admitted,
            "active_patients": active_patients,
            "discharged_patients": discharged_patients,
            "average_stay_hours": round(avg_stay, 2) if avg_stay else 0,
            "general_ward_count": general_count,
            "critical_ward_count": critical_count
        }


# ========== VITAL SIGNS LOGGING OPERATIONS ==========

async def log_vital_signs(
    patient_id: int,
    heart_rate: float,
    spo2: float,
    temperature: float,
    bp_systolic: float,
    bp_diastolic: float,
    respiratory_rate: Optional[float] = None,
    blood_glucose: Optional[float] = None
) -> Dict[str, Any]:
    """Log vital signs reading for a patient"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO vital_logs (
                patient_id, heart_rate, spo2, temperature, 
                bp_systolic, bp_diastolic, respiratory_rate, blood_glucose
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, patient_id, heart_rate, spo2, temperature, 
                      bp_systolic, bp_diastolic, respiratory_rate, blood_glucose, timestamp
        """, patient_id, heart_rate, spo2, temperature, bp_systolic, bp_diastolic, 
            respiratory_rate, blood_glucose)
        
        return dict(row)


async def get_patient_vital_history(patient_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get vital signs history for a patient"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, patient_id, heart_rate, spo2, temperature, 
                   bp_systolic, bp_diastolic, respiratory_rate, blood_glucose, timestamp
            FROM vital_logs
            WHERE patient_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """, patient_id, limit)
        
        return [dict(row) for row in rows]


async def get_latest_vitals(patient_id: int) -> Optional[Dict[str, Any]]:
    """Get most recent vital signs for a patient"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, patient_id, heart_rate, spo2, temperature, 
                   bp_systolic, bp_diastolic, respiratory_rate, blood_glucose, timestamp
            FROM vital_logs
            WHERE patient_id = $1
            ORDER BY timestamp DESC
            LIMIT 1
        """, patient_id)
        
        return dict(row) if row else None
