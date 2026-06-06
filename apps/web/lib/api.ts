import type {
  DashboardData,
  DataFreshness,
  DataModeResponse,
  FantasyAsset,
  FantasyReadOnlyStatus,
  FantasySyncResponse,
  FreshnessStatus,
  ImportPreview,
  ImportTemplateType,
  OnboardingStatus,
  OptimizerReadiness,
  ProviderTestResult,
  RaceMeeting,
  RecommendationRun,
  TeamSnapshot,
} from "./api-types";

export type {
  DashboardData,
  DataFreshness,
  DataMode,
  DataModeResponse,
  FantasyAsset,
  FantasyReadOnlyStatus,
  FantasySyncResponse,
  ImportPreview,
  ImportTemplateType,
  ImportValidationMessage,
  OnboardingStatus,
  OptimizerReadiness,
  ProviderTestResult,
  RaceMeeting,
  ReadinessIssue,
  RecommendationOption,
  RecommendationRun,
  TeamSnapshot,
} from "./api-types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        detail = payload.detail;
      }
    } catch {
      detail = response.statusText;
    }
    throw new Error(`${response.status} ${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function resetRealData(): Promise<void> {
  await request("/api/v1/data/reset", {
    method: "POST",
    body: JSON.stringify({ scope: "all" }),
  });
}

export async function loadOnboardingStatus(): Promise<OnboardingStatus> {
  return request<OnboardingStatus>("/api/v1/onboarding/status");
}

export async function setDataMode(mode: "demo" | "real"): Promise<DataModeResponse> {
  return request<DataModeResponse>("/api/v1/onboarding/mode", {
    method: "POST",
    body: JSON.stringify({ mode, allowDemoFallback: mode === "demo" }),
  });
}

export async function loadOptimizerReadiness(): Promise<OptimizerReadiness> {
  return request<OptimizerReadiness>("/api/v1/readiness/optimizer");
}

export async function testProvider(providerName: string): Promise<ProviderTestResult> {
  return request<ProviderTestResult>("/api/v1/providers/test", {
    method: "POST",
    body: JSON.stringify({ providerName }),
  });
}

export async function loadFantasyReadOnlyStatus(): Promise<FantasyReadOnlyStatus> {
  return request<FantasyReadOnlyStatus>("/api/v1/fantasy/read-only/status");
}

export async function syncFantasyGame(params: {
  gamePeriodId: string;
  season?: number;
  leagueId?: string;
  userGlobalId?: string;
  slot?: number;
}): Promise<FantasySyncResponse> {
  return request<FantasySyncResponse>("/api/v1/sync/fantasy-game", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function loadDashboard(): Promise<DashboardData> {
  const [appStatus, freshness, providers, race, teams, market] = await Promise.all([
    request<{ version: string; currentEventId?: string }>("/api/v1/app/status"),
    request<{ items: DataFreshness[]; overallStatus: string }>("/api/v1/data-freshness").catch(() => null),
    request<{ items: DashboardData["providers"] }>("/api/v1/providers"),
    request<{ item: RaceMeeting | null }>("/api/v1/race-context/current"),
    request<{ items: TeamSnapshot[]; freshness?: DataFreshness }>("/api/v1/fantasy/team/current"),
    request<{ items: FantasyAsset[]; freshness?: DataFreshness }>("/api/v1/fantasy/market"),
  ]);
  const freshnessItems =
    freshness?.items ??
    fallbackFreshness({
      race: race.item,
      market: market.freshness,
      team: teams.freshness,
    });
  return {
    appStatus,
    freshness: freshnessItems,
    overallStatus: freshness?.overallStatus ?? fallbackOverallStatus(freshnessItems),
    providers: providers.items,
    race: race.item,
    teams: teams.items,
    assets: market.items,
  };
}

function fallbackFreshness({
  race,
  market,
  team,
}: {
  race: RaceMeeting | null;
  market?: DataFreshness;
  team?: DataFreshness;
}): DataFreshness[] {
  return [
    fallbackFreshnessItem({
      key: "race.calendar",
      label: "Race calendar / schedule",
      status: race ? "real_current" : "missing",
      recordCount: race ? 1 : 0,
      isBlocking: false,
      message: race
        ? "Race calendar has a current meeting available."
        : "No race calendar is loaded. Sync public race context to populate schedule data.",
    }),
    fallbackFreshnessItem({
      key: "race.current_meeting",
      label: "Current or next race meeting",
      status: race ? "real_current" : "missing",
      recordCount: race ? 1 : 0,
      isBlocking: false,
      message: race
        ? `Race context loaded for ${race.meetingName}.`
        : "No current race context is loaded. Sync public race context to show sessions and weather.",
    }),
    market ??
      fallbackFreshnessItem({
        key: "fantasy.market",
        label: "Fantasy market prices",
        status: "missing",
        recordCount: 0,
        isBlocking: true,
        message: "No fantasy market prices have been loaded. Sync the Fantasy catalog or provide market data to load selectable assets.",
        templateType: "market_prices",
      }),
    team ??
      fallbackFreshnessItem({
        key: "fantasy.user_team",
        label: "User fantasy team",
        status: "missing",
        recordCount: 0,
        isBlocking: true,
        message: "No user fantasy team has been selected. Choose Teams 1-3 from the loaded market catalog.",
        templateType: "team_state",
      }),
    fallbackFreshnessItem({
      key: "fantasy.scores",
      label: "Fantasy scores",
      status: "missing",
      recordCount: 0,
      isBlocking: false,
      message: "No fantasy score snapshot is loaded. Import fantasy_scores when available.",
      templateType: "fantasy_scores",
    }),
    fallbackFreshnessItem({
      key: "fantasy.league",
      label: "League table",
      status: "missing",
      recordCount: 0,
      isBlocking: false,
      message: "No league table is loaded. Import league_table to enable rival analysis.",
      templateType: "league_table",
    }),
  ];
}

function fallbackFreshnessItem({
  key,
  label,
  status,
  recordCount,
  isBlocking,
  message,
  templateType,
}: {
  key: string;
  label: string;
  status: FreshnessStatus;
  recordCount: number;
  isBlocking: boolean;
  message: string;
  templateType?: ImportTemplateType;
}): DataFreshness {
  return {
    key,
    label,
    status,
    sourceMode: "endpoint_fallback",
    staleAfterSeconds: 86_400,
    recordCount,
    isDemo: false,
    isBlocking,
    message,
    remediation: templateType
      ? {
          label: `Import ${templateType}`,
          action: "open_import_wizard",
          templateType,
        }
      : null,
  };
}

function fallbackOverallStatus(items: DataFreshness[]): string {
  return items.some((item) => item.isBlocking && item.status !== "real_current") ? "blocked" : "ready";
}

export async function saveOnboardingTeams(params: {
  eventId: string;
  teams: Array<{
    slot: number;
    teamName: string;
    assetIds: string[];
    costCapMillions: number;
    freeTransfers: number;
    transferPenaltyPoints?: number;
  }>;
}) {
  return request<{ items: TeamSnapshot[]; freshness: DataFreshness }>("/api/v1/onboarding/teams/select", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function runRecommendation(params: {
  eventId: string;
  teamSnapshotId: string;
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
    body: JSON.stringify({ eventId: params.eventId }),
  });
  return request<RecommendationRun>("/api/v1/optimizer/recommendations", {
    method: "POST",
    body: JSON.stringify({
      teamSnapshotId: params.teamSnapshotId,
      eventId: params.eventId,
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

export async function previewImport(params: {
  templateType: ImportTemplateType;
  rawText: string;
}): Promise<ImportPreview> {
  return request<ImportPreview>("/api/v1/imports/preview", {
    method: "POST",
    body: JSON.stringify({
      templateType: params.templateType,
      contentType: "text/csv",
      rawText: params.rawText,
    }),
  });
}

export async function confirmImport(preview: ImportPreview, rawText: string) {
  return request<{ status: string; itemCount: number; message: string }>("/api/v1/imports/confirm", {
    method: "POST",
    body: JSON.stringify({
      templateType: preview.templateType,
      contentType: "text/csv",
      rawText,
      contentHash: preview.contentHash,
    }),
  });
}

export async function syncRaceContext(params: { season?: number; meetingKey?: string }) {
  return request<{ status: string; rowCount: number }>("/api/v1/sync/race-context", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function backfillFantasyScores(params: { season: number; throughRound?: number; eventId?: string }) {
  return request<{ status: string; featureCount: number; message: string }>("/api/v1/fantasy/public-form/backfill", {
    method: "POST",
    body: JSON.stringify({
      season: params.season,
      throughRound: params.throughRound,
      eventId: params.eventId,
    }),
  });
}

export async function loadRaceSessions(meetingKey: string) {
  return request<{
    items: Array<{
      sessionKey: string;
      meetingKey: string;
      sessionName: string;
      sessionType?: string | null;
      startsAt?: string | null;
      endsAt?: string | null;
    }>;
  }>(`/api/v1/race-context/meetings/${meetingKey}/sessions`);
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

export async function loadLeagueTable() {
  return request<{
    items: Array<{
      leagueId: string;
      eventId: string;
      rivals: Array<{ rank?: number; teamName: string; points: number; assetIds?: string[] }>;
    }>;
  }>("/api/v1/fantasy/league");
}
