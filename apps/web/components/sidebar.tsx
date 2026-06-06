import { Activity, Bot, BrainCircuit, Gauge, HeartPulse, Home, Settings, Table2, Trophy, Users } from "lucide-react";
import Link from "next/link";

export type View =
  | "setup"
  | "dashboard"
  | "race-week"
  | "optimizer"
  | "market"
  | "my-teams"
  | "league"
  | "ai-strategist"
  | "data-health"
  | "settings";

const navItems: Array<{ view: View; href: string; label: string; icon: typeof Home }> = [
  { view: "dashboard", href: "/dashboard", label: "Dashboard", icon: Home },
  { view: "race-week", href: "/race-week", label: "Race Week", icon: Activity },
  { view: "optimizer", href: "/optimizer", label: "Optimizer", icon: BrainCircuit },
  { view: "market", href: "/market", label: "Market", icon: Table2 },
  { view: "my-teams", href: "/my-teams", label: "My Teams", icon: Users },
  { view: "league", href: "/league", label: "League", icon: Trophy },
  { view: "ai-strategist", href: "/ai-strategist", label: "AI Strategist", icon: Bot },
  { view: "data-health", href: "/data-health", label: "Data Health", icon: HeartPulse },
  { view: "settings", href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar({ active }: { active: View }) {
  return (
    <aside className="sidebar">
      <Link className="brand" href="/dashboard">
        <span className="brand-mark">
          <Gauge size={20} aria-hidden="true" />
        </span>
        <span>
          <span className="brand-title">Outlap</span>
          <span className="brand-subtitle">Unofficial local cockpit</span>
        </span>
      </Link>
      <nav className="nav" aria-label="Primary navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link className={active === item.view ? "active" : ""} href={item.href} key={item.view}>
              <Icon size={16} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
