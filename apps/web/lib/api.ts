const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type FantasyAsset = {
  assetId: string;
  assetType: "driver" | "constructor";
  displayName: string;
  shortName?: string | null;
  constructorName?: string | null;
  priceMillions: number;
  fantasyPoints?: number | null;
  ownershipPct?: number | null;
  riskScore?: number | null;
};

export type TeamSnapshot = {
  teamSnapshotId: string;
  teamName: string;
  eventId: string;
  budgetUsedMillions: number;
  budgetRemainingMillions: number;
  costCapMillions: number;
  freeTransfers: number;
  assets: Array<{ assetId: string; assetType: string; boostMultiplier?: number }>;
  chips: Array<{ chipName: string; status: string }>;
};

export type DataSourceStatus = {
  source: string;
  status: string;
  severity: string;
  message: string;
  freshness: string;
  connectorVersion: string;
  licenseNote: string;
  actionRequired?: string | null;
};

export type RaceMeeting = {
  meetingKey: string;
  eventId: string;
  meetingName: string;
  circuitName: string;
  countryName: string;
  location: string;
  locksAt: string;
  status: string;
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
  appStatus: { version: string; currentEventId: string };
  dataSources: DataSourceStatus[];
  providers: Array<{
    providerName: string;
    displayName: string;
    enabled: boolean;
    keyConfigured: boolean;
    baseUrl?: string | null;
    defaultModel?: string | null;
    apiKeyEnvVar?: string | null;
  }>;
  race: RaceMeeting;
  teams: TeamSnapshot[];
  assets: FantasyAsset[];
};

export type ProviderTestResult = {
  ok: boolean;
  providerName: string;
  message: string;
  latencyMs?: number | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export async function resetDemo(): Promise<void> {
  await request("/api/v1/demo/reset", { method: "POST", body: "{}" });
}

export async function importTeam(payload: unknown): Promise<void> {
  await request("/api/v1/fantasy/import/team", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function testProvider(providerName: string): Promise<ProviderTestResult> {
  return request<ProviderTestResult>("/api/v1/providers/test", {
    method: "POST",
    body: JSON.stringify({ providerName }),
  });
}

export async function loadDashboard(): Promise<DashboardData> {
  const [appStatus, sources, providers, race, teams, assets] = await Promise.all([
    request<{ version: string; currentEventId: string }>("/api/v1/app/status"),
    request<{ items: DataSourceStatus[] }>("/api/v1/data-sources/status"),
    request<{ items: DashboardData["providers"] }>("/api/v1/providers"),
    request<RaceMeeting>("/api/v1/races/current"),
    request<{ items: TeamSnapshot[] }>("/api/v1/fantasy/teams/current"),
    request<{ items: FantasyAsset[] }>("/api/v1/fantasy/assets"),
  ]);
  return {
    appStatus,
    dataSources: sources.items,
    providers: providers.items,
    race,
    teams: teams.items,
    assets: assets.items,
  };
}

export async function runRecommendation(params: {
  strategyMode: string;
  lockedAssetIds?: string[];
  bannedAssetIds?: string[];
  allowedChips?: string[];
  customWeights?: Record<string, number>;
  idempotencyKey?: string;
  maxOptions?: number;
}): Promise<RecommendationRun> {
  const projection = await request<{ projectionRunId: string }>("/api/v1/projections/run", {
    method: "POST",
    body: JSON.stringify({ eventId: "event_demo_01" }),
  });
  return request<RecommendationRun>("/api/v1/optimizer/recommendations", {
    method: "POST",
    body: JSON.stringify({
      teamSnapshotId: "team_demo_01",
      eventId: "event_demo_01",
      projectionRunId: projection.projectionRunId,
      strategyMode: params.strategyMode,
      lockedAssetIds: params.lockedAssetIds ?? [],
      bannedAssetIds: params.bannedAssetIds ?? [],
      allowedChips: params.allowedChips ?? [],
      customWeights: params.customWeights ?? {},
      idempotencyKey: params.idempotencyKey ?? null,
      maxOptions: params.maxOptions ?? 5,
    }),
  });
}

export async function simulateDataFailure(): Promise<void> {
  await request("/api/v1/fantasy/sync", {
    method: "POST",
    body: JSON.stringify({ simulateFailure: true }),
  });
}

export async function chat(providerName: string, message: string, recommendationRunId?: string) {
  return request<{ status: string; message: string; canMutateFantasyAccount: boolean }>(
    "/api/v1/agent/chat",
    {
      method: "POST",
      body: JSON.stringify({ providerName, message, recommendationRunId }),
    },
  );
}

export async function loadRaceIntelligence(meetingKey: string) {
  return request<{
    meeting: RaceMeeting;
    sessions: Array<{ sessionKey: string; sessionName: string; status: string; startsAt: string }>;
    weather: Array<{ summary: string; rainfallChancePct: number; riskScore: number }>;
    raceControl: Array<{ message: string; flag: string }>;
    news: Array<{ title: string; summary: string; riskFlags: string[] }>;
  }>(`/api/v1/races/${meetingKey}/intelligence`);
}

export async function loadLeagueAnalysis() {
  return request<{
    leagueId: string;
    summary: string;
    userRank: number;
    gapToLeader: number;
    commonAssetIds: string[];
    differentialAssetIds: string[];
    catchUpPlan: string[];
  }>("/api/v1/leagues/league_demo_01/analysis");
}
