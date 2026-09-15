interface Props {
  label: string;
  value: number;
  weight?: number;
  color?: string;
}

export default function ScoreBar({ label, value, weight, color = "#1f90df" }: Props) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-[var(--text-secondary)]">
          {label}
          {weight !== undefined && <span className="text-[var(--text-muted)]"> ({weight}%)</span>}
        </span>
        <span className="text-[var(--text-primary)] font-mono">{pct.toFixed(1)}%</span>
      </div>
      <div className="h-1.5 bg-[var(--bg-card)] rounded overflow-hidden">
        <div className="h-full rounded transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}