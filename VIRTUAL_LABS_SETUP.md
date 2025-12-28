# Virtual Labs Database Setup Guide

## 🚨 Quick Fix for the 500 Error

The 500 error you're seeing is because the Virtual Labs database tables don't exist yet. Here's how to fix it:

## Step 1: Access Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor** in the left sidebar

## Step 2: Run the Migration

1. Copy the entire contents of `supabase_migration_virtual_labs.sql`
2. Paste it into the SQL Editor
3. Click **Run** to execute the migration

## Step 3: Verify Setup

After running the migration, check the health endpoint:
```
GET http://localhost:8000/api/virtual-labs/health
```

You should see:
```json
{
  "status": "healthy",
  "service": "Virtual Labs",
  "database_status": "connected",
  "tables_status": "ready",
  "stats": {
    "total_labs": 2,
    "total_sessions": 0
  }
}
```

## What the Migration Creates

### Tables Created:
- ✅ `virtual_labs` - Lab definitions with HTML/CSS/JS content
- ✅ `virtual_lab_sessions` - User session tracking
- ✅ `virtual_lab_interactions` - Detailed interaction logging
- ✅ `virtual_lab_ai_assistance` - AI help requests and responses

### Sample Data:
- 🧪 Simple Pendulum Motion (Physics, Grade 11)
- 🧪 Acid-Base Titration (Chemistry, Grade 12)

### Security Features:
- 🔒 Row Level Security (RLS) policies
- 🔒 Proper foreign key constraints
- 🔒 Data validation checks

## After Setup

Once the tables are created, your Virtual Labs endpoints will work:

- ✅ `GET /api/virtual-labs/sessions?user_id=...` (the one that was failing)
- ✅ `GET /api/virtual-labs` - List all labs
- ✅ `POST /api/virtual-labs/sessions` - Start new sessions
- ✅ All other Virtual Labs endpoints

## Troubleshooting

### If you still get errors after migration:

1. **Check table creation:**
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name LIKE 'virtual_lab%';
   ```

2. **Check RLS policies:**
   ```sql
   SELECT schemaname, tablename, policyname 
   FROM pg_policies 
   WHERE tablename LIKE 'virtual_lab%';
   ```

3. **Test basic query:**
   ```sql
   SELECT COUNT(*) FROM virtual_labs;
   ```

### Common Issues:

- **Permission errors**: Make sure you're using the service key, not anon key
- **RLS blocking queries**: The migration includes proper RLS policies
- **Foreign key errors**: Tables are created in the correct order

## Next Steps

After the database is set up:

1. **Test the endpoints** using the API documentation at `/docs`
2. **Create your first virtual lab** using the POST endpoint
3. **Start a session** and test interaction tracking
4. **Try the AI assistance** feature

The Virtual Labs feature is now ready for frontend integration! 🎉