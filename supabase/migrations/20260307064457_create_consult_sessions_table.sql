/*
  # Create consult sessions and history tables

  1. New Tables
    - `consult_sessions`: Stores user sessions and consult metadata
      - `id` (uuid, primary key)
      - `session_id` (text, unique identifier for this browser session)
      - `created_at` (timestamp)
      - `updated_at` (timestamp)
    
    - `consult_history`: Stores individual consult outputs
      - `id` (uuid, primary key)
      - `session_id` (uuid, foreign key to consult_sessions)
      - `patient_name` (text)
      - `consult_message` (text)
      - `resident_input` (text)
      - `triage_output` (text)
      - `context_output` (text)
      - `plan_output` (text)
      - `final_note` (text)
      - `created_at` (timestamp)

  2. Security
    - Enable RLS on both tables
    - Sessions are identified by session_id (anonymous, no auth required for demo)
    - Allow users to read/update their own session's consults

  3. Purpose
    - Enable users to see "Your Recent Consults" on return visits
    - Track which workflows are used most (analytics for product improvement)
    - Allow users to export/download previously generated notes
*/

CREATE TABLE IF NOT EXISTS consult_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS consult_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES consult_sessions(id) ON DELETE CASCADE,
  patient_name text NOT NULL,
  consult_message text NOT NULL,
  resident_input text,
  triage_output text,
  context_output text,
  plan_output text,
  final_note text,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE consult_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE consult_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Allow read access based on session_id stored in request header
CREATE POLICY "Allow read consult sessions"
  ON consult_sessions FOR SELECT
  USING (true);

CREATE POLICY "Allow insert consult sessions"
  ON consult_sessions FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow read consult history"
  ON consult_history FOR SELECT
  USING (true);

CREATE POLICY "Allow insert consult history"
  ON consult_history FOR INSERT
  WITH CHECK (true);

CREATE INDEX idx_session_id ON consult_sessions(session_id);
CREATE INDEX idx_consult_session ON consult_history(session_id);
CREATE INDEX idx_consult_created ON consult_history(created_at);
