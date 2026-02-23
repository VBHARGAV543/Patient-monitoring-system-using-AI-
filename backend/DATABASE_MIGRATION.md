# Database Migration Guide

## Overview
This guide explains how to update your existing database to support the new mock data features.

## What's New
- **Medical fields**: gender, blood_type, weight, height, medical_history, allergies, current_medications, emergency_contact, emergency_phone
- **Vital logs table**: Stores patient vital signs history over time

## Migration Steps

### Option 1: Fresh Database (Recommended for Development)
If you want to start fresh:

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Copy and paste the entire content of `database_schema.sql`
4. Click "Run"

This will create all tables with the new structure.

### Option 2: Update Existing Database (Preserve Data)
If you have existing patient data to keep:

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Copy and paste the entire content of `migration_add_medical_fields.sql`
4. Click "Run"

This will:
- Add new medical columns to the `patients` table
- Create the `vital_logs` table
- Create necessary indexes
- Keep all existing patient data intact

## Verification

After running the migration, verify it worked:

1. In Supabase SQL Editor, run:
```sql
-- Check patients table columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'patients'
ORDER BY ordinal_position;

-- Check vital_logs table exists
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name = 'vital_logs';
```

2. You should see:
   - All medical fields in the `patients` table
   - The `vital_logs` table exists

## Testing the System

After migration:

1. **Start Backend**:
   ```bash
   cd backend
   python main.py
   ```

2. **Start Frontend**:
   ```bash
   cd frontend_new
   npm run dev
   ```

3. **Admit a Patient**:
   - Go to http://localhost:5173/admit
   - Fill in patient details
   - **Enable "Demo Mode"** checkbox
   - Submit

4. **View Dashboard**:
   - You should see the patient with:
     - Medical history
     - Allergies
     - Current medications
     - Vital signs updating every 8 seconds
     - Real-time ML predictions

## Troubleshooting

### Error: "column p.gender does not exist"
**Solution**: Run the migration script (`migration_add_medical_fields.sql`)

### Error: "relation vital_logs does not exist"
**Solution**: Run the migration script to create the table

### No vital signs appearing
**Check**:
1. Backend console for errors
2. Make sure demo_mode is enabled when admitting patient
3. Wait 8 seconds for first vital signs to generate
4. Check WebSocket connection in browser console

### Medical data not showing
**Check**:
1. Patient was admitted with demo_mode=true
2. Database has the new medical columns
3. Frontend Dashboard.jsx has been updated
4. Browser cache cleared (Ctrl+Shift+R)

## Rolling Back (If Needed)

If you need to revert the changes:

```sql
-- Remove medical fields from patients
ALTER TABLE patients
DROP COLUMN IF EXISTS gender,
DROP COLUMN IF EXISTS blood_type,
DROP COLUMN IF EXISTS weight,
DROP COLUMN IF EXISTS height,
DROP COLUMN IF EXISTS medical_history,
DROP COLUMN IF EXISTS allergies,
DROP COLUMN IF EXISTS current_medications,
DROP COLUMN IF EXISTS emergency_contact,
DROP COLUMN IF EXISTS emergency_phone;

-- Remove vital_logs table
DROP TABLE IF EXISTS vital_logs;
```

## Next Steps

After successful migration:

1. ✅ Admit test patients with demo mode
2. ✅ Observe vital signs generation
3. ✅ Check medical history display
4. ✅ Test alarm triggering with different scenarios
5. ✅ Review vital history via API: `GET /api/patient/{id}/vitals`

## Support

For issues or questions:
- Check `MOCK_DATA_IMPLEMENTATION.md` for complete feature documentation
- Review backend console logs for detailed error messages
- Verify Supabase connection in `backend/database.py`
