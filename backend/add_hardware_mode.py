"""
Database Migration: Add hardware_mode column to patients table
Run this script once to update the database schema
"""
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def migrate():
    """Add hardware_mode column to patients table"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    print("🔄 Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Check if column already exists
        result = await conn.fetchval("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'patients' AND column_name = 'hardware_mode'
        """)
        
        if result > 0:
            print("✅ Column 'hardware_mode' already exists in patients table")
        else:
            print("🔄 Adding 'hardware_mode' column to patients table...")
            await conn.execute("""
                ALTER TABLE patients
                ADD COLUMN hardware_mode BOOLEAN DEFAULT FALSE
            """)
            print("✅ Column 'hardware_mode' added successfully")
        
        # Verify the column
        columns = await conn.fetch("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'patients'
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Current patients table schema:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (default: {col['column_default']})")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await conn.close()
        print("\n✅ Database connection closed")

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Add hardware_mode column")
    print("=" * 60)
    asyncio.run(migrate())
