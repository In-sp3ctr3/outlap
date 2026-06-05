CREATE TABLE IF NOT EXISTS source_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_version TEXT NOT NULL,
  connector_version TEXT NOT NULL,
  request_method TEXT NOT NULL,
  request_url_template TEXT NOT NULL,
  request_params_json JSON,
  fetched_at TIMESTAMP NOT NULL,
  http_status INTEGER,
  content_hash TEXT NOT NULL,
  raw_storage_path TEXT,
  raw_json JSON,
  license_note TEXT,
  normalization_version TEXT NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS recommendation_runs (
  recommendation_run_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  team_snapshot_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  projection_run_id TEXT NOT NULL,
  ruleset_version TEXT NOT NULL,
  optimizer_version TEXT NOT NULL,
  strategy_mode TEXT NOT NULL,
  request_json JSON NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT
);
