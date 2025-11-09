# Meet2Action MVP

Transform Google Meet transcripts into actionable Kanban boards using AI.

## 🎯 Overview

Meet2Action is a Streamlit-based application that:
- Authenticates users via Supabase
- Connects to Google Drive to fetch Google Meet transcripts
- Processes transcripts with Google Gemini LLM to extract action items & owners
- Displays tasks in a Kanban board view grouped by assignee
- Persists user & task data in Supabase

## 📋 Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher
- A Supabase account and project
- A Google Cloud project with:
  - Google Drive API enabled
  - OAuth 2.0 credentials configured
  - Gemini API access (via Google AI Studio)

## 🚀 Setup Guide

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd meet2action

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GEMINI_API_KEY=your_gemini_api_key
```

### Step 3: Set Up Supabase

1. **Create Supabase Tables**

   Run these SQL commands in your Supabase SQL Editor:

   ```sql
   -- Users table (usually auto-created by Supabase Auth, but ensure it exists)
   CREATE TABLE IF NOT EXISTS users (
     id UUID PRIMARY KEY REFERENCES auth.users(id),
     email TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Tasks table
   CREATE TABLE IF NOT EXISTS tasks (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
     assignee TEXT NOT NULL,
     task TEXT NOT NULL,
     priority TEXT DEFAULT 'Medium',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- Enable Row Level Security (RLS)
   ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

   -- Create policy for users to manage their own tasks
   CREATE POLICY "Users can manage their own tasks"
     ON tasks
     FOR ALL
     USING (auth.uid() = user_id);
   ```

2. **Enable Supabase Auth**
   - Go to Authentication → Settings in your Supabase dashboard
   - Enable Email authentication
   - Configure email templates if needed

### Step 4: Set Up Google Cloud Project

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable APIs**
   - Enable **Google Drive API**
   - Enable **Google Generative AI API** (for Gemini)

3. **Create OAuth 2.0 Credentials**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URI: `http://localhost:8501`
   - Copy the Client ID and Client Secret to your `.env` file

4. **Get Gemini API Key**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy it to your `.env` file

### Step 5: Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage Flow

1. **Login/Sign Up**
   - Use the sidebar to log in or create an account
   - Supabase will handle email verification

2. **Connect Google Drive**
   - Click "Connect Google Drive" button
   - Authorize the application to access your Google Drive
   - You'll be redirected back to the app

3. **Fetch Transcripts**
   - Click "Fetch Transcripts" to load Google Meet transcripts
   - Select a transcript from the dropdown

4. **Process Transcript**
   - Click "Load Transcript" to view the content
   - Click "Process with Gemini" to extract action items
   - The AI will identify tasks, assignees, and priorities

5. **View Kanban Board**
   - Action items are automatically displayed in a Kanban board
   - Tasks are grouped by assignee
   - Priority levels are color-coded

6. **Save Tasks**
   - Click "Save to Supabase" to persist tasks to your database
   - Use "Load Saved Tasks" in the sidebar to retrieve previously saved tasks

## 🗂 Project Structure

```
meet2action/
├── app.py                 # Main Streamlit application
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
├── README.md            # This file
│
├── components/          # UI components
│   ├── auth.py         # Authentication (login/logout)
│   ├── drive_connector.py  # Google Drive integration
│   ├── transcript_parser.py  # Transcript parsing
│   ├── gemini_processor.py   # Gemini LLM processing
│   └── kanban_board.py      # Kanban board display
│
├── utils/               # Utility modules
│   ├── supabase_client.py   # Supabase database operations
│   ├── google_auth.py       # Google OAuth helper
│   └── env_loader.py        # Environment variable loader
│
└── assets/              # Static assets (optional)
    └── logo.png
```

## 🔧 Troubleshooting

### Google OAuth Issues
- Ensure redirect URI matches exactly: `http://localhost:8501`
- Check that OAuth consent screen is configured
- Verify client ID and secret are correct

### Supabase Connection Issues
- Verify your Supabase URL and anon key
- Check that RLS policies are set up correctly
- Ensure tables exist and have correct schema

### Gemini API Issues
- Verify API key is valid
- Check API quota/limits in Google AI Studio
- Ensure Generative AI API is enabled

### Transcript Not Found
- Ensure transcripts are saved as Google Docs
- Check that file names contain "Meet Transcript"
- Verify Google Drive API access permissions

## 🎨 Features

- ✅ User authentication via Supabase
- ✅ Google Drive OAuth integration
- ✅ Automatic transcript fetching
- ✅ AI-powered action item extraction
- ✅ Kanban board visualization
- ✅ Task persistence in Supabase
- ✅ Priority-based task organization

## 📝 Notes

- This is an MVP version focused on core functionality
- For production use, consider adding:
  - Refresh token persistence for Google OAuth
  - Task editing and deletion
  - Export functionality
  - Email notifications
  - Team collaboration features

## 📄 License

MIT License - feel free to use and modify as needed.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
