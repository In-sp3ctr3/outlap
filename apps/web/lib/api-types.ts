export type DataMode = "unset" | "demo" | "real";

export type DataModeResponse = {
  mode: DataMode;
  allowDemoFallback: boolean;
};

export type OnboardingStatus = {
  firstRunCompleted: boolean;
  mode: DataMode;
  nextRoute: string;
  setupComplete?: boolean;
  needsRealData?: boolean;
};

export type FantasyAsset = {
  assetId: string;
  assetType: "driver" | "constructor";
  displayName: string;
  shortName?: string | null;
  abbreviation?: string | null;
  constructorName?: string | null;
  teamColor?: string | null;
  teamColour?: string | null;
  constructorColor?: string | null;
  constructorColour?: string | null;
  colorHex?: string | null;
  priceMillions: number;
  fantasyPoints?: number | null;
  ownershipPct?: number | null;
  selectedByPct?: number | null;
  riskScore?: number | null;
  sourceSnapshotId?: string | null;
};

export type TeamSnapshot = {
  teamSnapshotId: string;
  teamName: string;
  eventId: string;
  budgetUsedMillions: number;
  budgetRemainingMillions: number;
  costCapMillions: number;
  freeTransfers: number;
  slot?: number | null;
  assets: Array<{ assetId: string; assetType: string; boostMultiplier?: number }>;
  chips: Array<{ chipName: string; status: string }>;
};

export type FreshnessStatus =
  | "real_current"
  | "real_stale"
  | "demo"
  | "missing"
  | "partial"
  | "error"
  | "unknown";

export type DataFreshness = {
  key: string;
  label: string;
  status: FreshnessStatus;
  sourceKey?: string | null;
  sourceMode: string;
  lastSuccessAt?: string | null;
  lastAttemptAt?: string | null;
  ageSeconds?: number | null;
  staleAfterSeconds: number;
  recordCount: number;
  isDemo: boolean;
  isBlocking: boolean;
  message: string;
  remediation?: {
    label: string;
    action: string;
    templateType?: ImportTemplateType | null;
  } | null;
};

export type ImportTemplateType =
  | "team_state"
  | "team_slots"
  | "market_prices"
  | "fantasy_scores"
  | "league_table"
  | "chips_state"
  | "season_totals"
  | "transfer_history_optional"
  | "rival_team_slots";

export type ImportValidationMessage = {
  rowNumber?: number | null;
  column?: string | null;
  severity: "error" | "warning" | "info";
  message: string;
  suggestedFix?: string | null;
};

export type ImportPreview = {
  templateType: ImportTemplateType;
  inferredDelimiter: string;
  detectedHeaders: string[];
  mappedHeaders: Record<string, string>;
  rows: Array<Record<string, unknown>>;
  messages: ImportValidationMessage[];
  importable: boolean;
  contentHash: string;
  rowCount: number;
};

export type RaceMeeting = {
  meetingKey: string;
  eventId?: string;
  meetingName: string;
  circuitName?: string | null;
  countryName?: string | null;
  location?: string | null;
  locksAt?: string;
  status?: string;
};

export type RecommendationTransfer = {
  assetOutId?: string | null;
  assetInId?: string | null;
  reason?: string | null;
};

export type RecommendationOption = {
  optionId: string;
  rank: number;
  strategyMode: string;
  chipAction?: string | null;
  expectedGrossPoints: number;
  transferPenaltyPoints: number;
  expectedNetPoints: number;
  budgetUsedMillions: number;
  budgetRemainingMillions: number;
  expectedBudgetDeltaMillions?: number | null;
  riskScore: number;
  confidence: number;
  summary: string;
  transfers: RecommendationTransfer[];
  rationale: string[];
  assumptions: string[];
  warnings: string[];
  sourceSnapshotIds: string[];
  projectionRunId: string;
  rulesetVersion: string;
  optimizerVersion: string;
};

export type RecommendationRun = {
  recommendationRunId: string;
  teamSnapshotId: string;
  eventId: string;
  projectionRunId: string;
  strategyMode: string;
  generatedAt: string;
  status: string;
  warnings: string[];
  requestFingerprint: string;
  requestContext: {
    teamSnapshotId: string;
    eventId: string;
    projectionRunId: string;
    strategyMode: string;
    lockedAssetIds: string[];
    bannedAssetIds: string[];
    allowedChips: string[];
    customWeights: Record<string, number>;
    maxOptions: number;
    idempotencyKeyHash?: string | null;
  };
  options: RecommendationOption[];
};

export type DashboardData = {
  appStatus: { version: string; currentEventId?: string };
  freshness: DataFreshness[];
  overallStatus: string;
  providers: Array<{
    providerName: string;
    displayName: string;
    enabled: boolean;
    keyConfigured: boolean;
    baseUrl?: string | null;
    defaultModel?: string | null;
    apiKeyEnvVar?: string | null;
  }>;
  race: RaceMeeting | null;
  teams: TeamSnapshot[];
  assets: FantasyAsset[];
};

export type ProviderTestResult = {
  ok: boolean;
  providerName: string;
  message: string;
  latencyMs?: number | null;
};

export type DataInputPath = {
  label: string;
  endpoint: string;
  method: "GET" | "POST";
  contentType?: string | null;
  primary: boolean;
};

export type FantasyReadOnlyStatus = {
  source: string;
  status: string;
  message: string;
  baseUrlConfigured: boolean;
  gameVersionConfigured: boolean;
  sessionTokenConfigured: boolean;
  requiredEnvVars: string[];
  documentedEndpoints: string[];
  structuredJsonImport: DataInputPath;
  csvFallback: DataInputPath;
  canMutateFantasyAccount: boolean;
};

export type FantasySyncResponse = {
  status: "ok" | "degraded";
  assetCount: number;
  scoreCount: number;
  teamCount: number;
  sourceSnapshotId: string;
  message: string;
};

export type ReadinessIssue = {
  key: string;
  label: string;
  message: string;
  recommendedAction: string;
};

export type OptimizerReadiness = {
  ready: boolean;
  blockingReasons: ReadinessIssue[];
  warnings: ReadinessIssue[];
  canRunWithWarnings: boolean;
};
