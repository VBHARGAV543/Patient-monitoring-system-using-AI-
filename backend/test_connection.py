"""
Test Supabase connection
Run this to verify database connectivity before starting the server
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def test_connection():
    """Test basic connection to Supabase"""
    print("🔍 Testing Supabase connection...")
    print(f"📍 Connection URL: {DATABASE_URL[:50]}... (truncated)")
    
    try:
        # Try to create a simple connection
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connection successful!")
        
        # Test a simple query
        version = await conn.fetchval('SELECT version();')
        print(f"✅ PostgreSQL version: {version[:50]}...")
        
        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('patients', 'band_assignment', 'alarm_events', 'nurse_sessions')
        """)
        
        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table['table_name']}")
        else:
            print("⚠️  No tables found. Run database_schema.sql in Supabase SQL Editor.")
        
        await conn.close()
        print("\n✅ All tests passed! Database is ready.")
        return True
        
    except asyncpg.exceptions.InvalidPasswordError:
        print("❌ Authentication failed - Check password in .env file")
        print("   Make sure @ symbol is encoded as %40")
        return False
        
    except asyncpg.exceptions.InvalidCatalogNameError:
        print("❌ Database 'postgres' not found - Check database name in connection string")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if you have internet connection")
        print("   2. Verify Supabase project is active at https://supabase.com/dashboard")
        print("   3. Test with: Test-NetConnection aws-1-ap-northeast-2.pooler.supabase.com -Port 5432")
        print("   4. Check firewall/VPN settings")
        print("   5. Try the direct connection URL instead of pooler URL")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
