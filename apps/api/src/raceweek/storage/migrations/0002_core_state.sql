CREATE TABLE IF NOT EXISTS fantasy_assets (
  asset_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  asset_type TEXT NOT NULL,
  display_name TEXT NOT NULL,
  price_millions DOUBLE NOT NULL,
  source_snapshot_id TEXT,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS user_fantasy_teams (
  team_snapshot_id TEXT PRIMARY KEY,
  team_name TEXT NOT NULL,
  event_id TEXT NOT NULL,
  cost_cap_millions DOUBLE NOT NULL,
  budget_used_millions DOUBLE NOT NULL,
  budget_remaining_millions DOUBLE NOT NULL,
  free_transfers INTEGER NOT NULL,
  transfer_penalty_points DOUBLE NOT NULL,
  captured_at TIMESTAMP NOT NULL,
  source_snapshot_id TEXT,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS user_team_assets (
  team_snapshot_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  asset_type TEXT NOT NULL,
  boost_multiplier DOUBLE DEFAULT 1,
  PRIMARY KEY (team_snapshot_id, asset_id)
);

CREATE TABLE IF NOT EXISTS chip_states (
  chip_state_id TEXT PRIMARY KEY,
  team_snapshot_id TEXT NOT NULL,
  chip_name TEXT NOT NULL,
  status TEXT NOT NULL,
  used_event_id TEXT,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS projection_runs (
  projection_run_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  source_snapshot_ids_json JSON NOT NULL,
  config_json JSON NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT,
  payload_json JSON
);

CREATE TABLE IF NOT EXISTS projections (
  projection_id TEXT PRIMARY KEY,
  projection_run_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  expected_points DOUBLE NOT NULL,
  floor_points DOUBLE,
  ceiling_points DOUBLE,
  confidence DOUBLE NOT NULL,
  risk_score DOUBLE NOT NULL,
  projected_price_delta_millions DOUBLE,
  contribution_breakdown_json JSON,
  assumptions_json JSON,
  payload_json JSON
);

CREATE TABLE IF NOT EXISTS recommendation_options (
  option_id TEXT PRIMARY KEY,
  recommendation_run_id TEXT NOT NULL,
  rank INTEGER NOT NULL,
  strategy_mode TEXT NOT NULL,
  chip_action TEXT,
  expected_gross_points DOUBLE NOT NULL,
  transfer_penalty_points DOUBLE NOT NULL,
  expected_net_points DOUBLE NOT NULL,
  budget_used_millions DOUBLE NOT NULL,
  budget_remaining_millions DOUBLE NOT NULL,
  expected_budget_delta_millions DOUBLE,
  risk_score DOUBLE NOT NULL,
  confidence DOUBLE NOT NULL,
  summary TEXT NOT NULL,
  rationale_json JSON NOT NULL,
  assumptions_json JSON NOT NULL,
  warnings_json JSON,
  payload_json JSON
);

CREATE TABLE IF NOT EXISTS provider_configs (
  provider_config_id TEXT PRIMARY KEY,
  provider_name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  default_model TEXT,
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  supports_streaming BOOLEAN NOT NULL DEFAULT TRUE,
  supports_tools BOOLEAN NOT NULL DEFAULT FALSE,
  key_configured BOOLEAN NOT NULL DEFAULT FALSE,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS data_source_statuses (
  source TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  last_successful_sync_at TIMESTAMP,
  freshness TEXT NOT NULL,
  connector_version TEXT NOT NULL,
  license_note TEXT NOT NULL,
  action_required TEXT,
  payload_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
  setting_key TEXT PRIMARY KEY,
  setting_value_json JSON NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

ALTER TABLE recommendation_runs ADD COLUMN IF NOT EXISTS payload_json JSON;
