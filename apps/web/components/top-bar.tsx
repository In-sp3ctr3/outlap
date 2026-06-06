import { ChevronDown, Flag, RadioTower } from "lucide-react";
import Link from "next/link";

import type { DashboardData } from "@/lib/api";

export function TopBar({ data }: { data: DashboardData }) {
  const demo = data.freshness.some((item) => item.isDemo || item.status === "demo");
  const statusText = data.overallStatus.replace("_", " ");
  const statusTone = demo ? "demo" : data.overallStatus === "real_current" ? "ready" : "missing";

  return (
    <header className="top-bar" aria-label="Race week controls">
      <div className="top-bar-status">
        <span className={`live-dot ${statusTone}`} />
        {demo ? "Using Demo Data" : statusText}
      </div>
      <div className="race-selector" aria-label="Current race week">
        <Flag size={15} aria-hidden="true" />
        <span>
          <strong>{data.race?.meetingName ?? "Race Week"}</strong>
          <small>{data.race?.countryName ?? "No race context loaded"}</small>
        </span>
        <ChevronDown size={15} aria-hidden="true" />
      </div>
      <Link className="icon-button" href="/data-health" aria-label="Data sync status">
        <RadioTower size={16} aria-hidden="true" />
      </Link>
    </header>
  );
}
