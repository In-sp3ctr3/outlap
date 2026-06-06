CREATE TABLE IF NOT EXISTS import_jobs (
  job_id TEXT PRIMARY KEY,
  template_type TEXT NOT NULL,
  source_mode TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  row_count INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL,
  summary TEXT NOT NULL,
  payload_json JSON NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS import_jobs_template_hash_idx
ON import_jobs(template_type, content_hash);

CREATE TABLE IF NOT EXISTS import_errors (
  error_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  row_number INTEGER,
  column_name TEXT,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  suggested_fix TEXT,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS race_context_meetings (
  meeting_key TEXT PRIMARY KEY,
  season INTEGER,
  round_number INTEGER,
  meeting_name TEXT NOT NULL,
  source_key TEXT NOT NULL,
  source_mode TEXT NOT NULL,
  source_snapshot_id TEXT,
  updated_at TIMESTAMP NOT NULL,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS race_context_sessions (
  session_key TEXT PRIMARY KEY,
  meeting_key TEXT NOT NULL,
  session_name TEXT NOT NULL,
  session_type TEXT,
  source_key TEXT NOT NULL,
  source_mode TEXT NOT NULL,
  source_snapshot_id TEXT,
  updated_at TIMESTAMP NOT NULL,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS race_context_events (
  event_key TEXT PRIMARY KEY,
  domain_key TEXT NOT NULL,
  meeting_key TEXT,
  session_key TEXT,
  source_key TEXT NOT NULL,
  source_mode TEXT NOT NULL,
  source_snapshot_id TEXT,
  updated_at TIMESTAMP NOT NULL,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_runs (
  sync_run_id TEXT PRIMARY KEY,
  source_key TEXT NOT NULL,
  source_domain TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TIMESTAMP NOT NULL,
  finished_at TIMESTAMP NOT NULL,
  request_path TEXT,
  response_hash TEXT,
  row_count INTEGER NOT NULL DEFAULT 0,
  error_class TEXT,
  error_message TEXT,
  payload_json JSON NOT NULL
);
