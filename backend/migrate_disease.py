import asyncio
import asyncpg

async def migrate():
    conn = await asyncpg.connect("postgresql://postgres.bsxnzptrlwydtyvyzvdc:BHARGAV%40543n@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres")
    try:
        await conn.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS disease VARCHAR(255)")
        print(" Added disease column")
        await conn.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS body_strength VARCHAR(20)")
        print(" Added body_strength column")
        await conn.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS genetic_condition VARCHAR(50)")
        print(" Added genetic_condition column")
        print(" Migration completed successfully!")
    except Exception as e:
        print(f" Migration error: {e}")
    finally:
        await conn.close()

asyncio.run(migrate())
