import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Satellite,
  Waves,
  Ship,
  Search,
  FileText,
  Settings as Cog,
} from "lucide-react";

const items = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/satellite", label: "Satellite Analysis", icon: Satellite },
  { to: "/drift", label: "Drift Analysis", icon: Waves },
  { to: "/ais", label: "AIS Vessels", icon: Ship },
  { to: "/investigation", label: "Investigation", icon: Search },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Cog },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-[var(--bg-secondary)] border-r border-[var(--border)] flex flex-col">
      <div className="p-5 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-[var(--accent)] rounded flex items-center justify-center font-bold text-white">
            M
          </div>
          <div>
            <div className="font-bold text-sm tracking-wider text-[var(--text-primary)]">
              MARITRACE
            </div>
            <div className="text-[10px] text-[var(--text-muted)] uppercase">
              Marine Intelligence
            </div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-[var(--accent)]/15 text-[var(--accent)] border-l-2 border-[var(--accent)] font-medium"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-card)] hover:text-[var(--text-primary)]"
              }`
            }
          >
            <Icon size={16} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-[var(--border)] text-[10px] text-[var(--text-muted)]">
        SIH 2026 · PS 26143
        <br />
        Team AstraX-22
      </div>
    </aside>
  );
}