import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, AlertTriangle, RefreshCw } from "lucide-react";
import { useSpills } from "../hooks/useSpills";
import type { Spill } from "../api/types";
import MapView from "../components/MapView";

const INDIA_REGIONS = ["india_west", "india_east", "india_south"];

export default function Dashboard() {
  const navigate = useNavigate();
  const [regionFilter, setRegionFilter] = useState<string>("");

  // Uses app-level cache — instant render on navigation back
  const { data: spills, regions, loading, error, lastFetch } = useSpills();

  const refresh = () => {
    window.location.reload();
  };

  // -------- India-specific subset --------
  const indiaSpills = spills.filter((s) =>
    INDIA_REGIONS.includes(s.region || "")
  );

  const indiaRegionCounts: Record<string, number> = {};
  for (const s of indiaSpills) {
    const r = s.region || "unknown";
    indiaRegionCounts[r] = (indiaRegionCounts[r] || 0) + 1;
  }

  // -------- All-region filtered set --------
  const filtered = regionFilter
    ? spills.filter((s) => s.region === regionFilter)
    : spills;

  // -------- Map data builders --------
  const buildMapData = (list: Spill[], maxPolys = 60) => {
    const usable = list
      .filter((s) => s.geometry?.coordinates)
      .slice(0, maxPolys);

    const polygons = usable.map((s) => {
      const isArchive = s.source === "historical";
      const isAisMatched =
        s.max_source_collated_score && s.max_source_collated_score > 0;
      const color = isArchive
        ? "#f59e0b"
        : isAisMatched
        ? "#ef4444"
        : "#1f90df";
      return {
        positions: (s.geometry.coordinates[0][0] || []).map(
          ([lon, lat]: [number, number]) => [lat, lon] as [number, number]
        ),
        color,
        fillOpacity: 0.35,
        label: `${s.region_label || s.region || "Spill"} · #${s.id} · ${(
          (s.area_m2 || 0) / 1e6
        ).toFixed(2)} km²`,
      };
    });

    const markers = usable.map((s) => {
      const coords = s.geometry.coordinates[0][0] || [];
      const avgLon =
        coords.reduce((a: number, c: any) => a + c[0], 0) / coords.length;
      const avgLat =
        coords.reduce((a: number, c: any) => a + c[1], 0) / coords.length;
      const isArchive = s.source === "historical";
      const isAisMatched =
        s.max_source_collated_score && s.max_source_collated_score > 0;
      const color = isArchive
        ? "#f59e0b"
        : isAisMatched
        ? "#ef4444"
        : "#1f90df";
      return {
        position: [avgLat, avgLon] as [number, number],
        label: `Slick #${s.id} — click to investigate`,
        color,
        radius: 5,
      };
    });

    return { polygons, markers };
  };

  const legend = [
    { color: "#ef4444", label: "Live · AIS-matched", shape: "dot" as const },
    { color: "#1f90df", label: "Live · unmatched", shape: "dot" as const },
    { color: "#f59e0b", label: "Historical archive", shape: "dot" as const },
  ];

  const indiaMap = buildMapData(indiaSpills, 80);
  const allMap = buildMapData(filtered, 60);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Mission Dashboard</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Oil spill detections from Cerulean · click any spill to investigate
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
          <span>
            Updated{" "}
            {lastFetch ? new Date(lastFetch).toLocaleTimeString() : "—"}
          </span>
          <button
            onClick={refresh}
            className="p-1.5 rounded hover:bg-[var(--bg-card)]"
            title="Force refresh"
          >
            <RefreshCw size={12} />
          </button>
        </div>
      </div>

      {/* Loading — only show when nothing is cached yet */}
      {loading && spills.length === 0 && (
        <div className="flex flex-col items-center justify-center p-12 gap-3 bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
          <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
          <p className="text-sm text-[var(--text-secondary)]">
            Warming up spill cache… (first load ~30-45s)
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <AlertTriangle className="text-red-400 mt-0.5" size={18} />
          <div>
            <div className="text-sm font-semibold text-red-300">
              Failed to load spills
            </div>
            <div className="text-xs text-red-200/70 mt-1">{error}</div>
          </div>
        </div>
      )}

      {/* Data loaded */}
      {spills.length > 0 && (
        <>
          {/* ============ INDIA SECTION ============ */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🇮🇳</span>
              <div>
                <h2 className="text-xl font-bold">Spills Detected Near India</h2>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  Arabian Sea · Bay of Bengal · Southern Indian Ocean
                </p>
              </div>
              <div className="flex-1 h-px bg-[var(--border)] ml-2" />
            </div>

            {indiaSpills.length === 0 ? (
              <div className="p-8 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg text-center">
                <p className="text-sm text-[var(--text-secondary)]">
                  No Indian spills in cache right now.
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  Load the historical archive or wait for the next Sentinel-1
                  pass.
                </p>
              </div>
            ) : (
              <>
                {/* Stat cards */}
                <div className="grid grid-cols-4 gap-4">
                  <StatCard
                    label="Arabian Sea"
                    value={indiaRegionCounts["india_west"] || 0}
                    accent="#1f90df"
                  />
                  <StatCard
                    label="Bay of Bengal"
                    value={indiaRegionCounts["india_east"] || 0}
                    accent="#10b981"
                  />
                  <StatCard
                    label="Southern Indian Ocean"
                    value={indiaRegionCounts["india_south"] || 0}
                    accent="#a855f7"
                  />
                  <StatCard
                    label="Total Indian Spills"
                    value={indiaSpills.length}
                    accent="#f59e0b"
                  />
                </div>

                {/* India map */}
                <MapView
                  polygons={indiaMap.polygons}
                  markers={indiaMap.markers}
                  legend={legend}
                  center={[15.0, 78.0]}
                  zoom={4}
                  height="440px"
                />

                {/* Recent Indian detections */}
                <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg overflow-hidden">
                  <div className="px-4 py-3 border-b border-[var(--border)] font-semibold text-sm flex items-center justify-between flex-wrap gap-2">
                    <span>
                      Recent Indian Detections · click any row to investigate
                    </span>
                    <span className="text-xs font-normal text-[var(--text-muted)]">
                      Showing top 15 of {indiaSpills.length}
                    </span>
                  </div>
                  <table className="w-full text-sm">
                    <thead className="text-xs text-[var(--text-muted)] uppercase">
                      <tr className="border-b border-[var(--border)]">
                        <th className="text-left px-4 py-2">ID</th>
                        <th className="text-left px-4 py-2">Region</th>
                        <th className="text-left px-4 py-2">Time</th>
                        <th className="text-right px-4 py-2">Area (km²)</th>
                        <th className="text-right px-4 py-2">Confidence</th>
                        <th className="text-left px-4 py-2">Source</th>
                        <th className="text-right px-4 py-2">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {indiaSpills.slice(0, 15).map((s) => (
                        <tr
                          key={s.id}
                          onClick={() => navigate(`/drift?spill=${s.id}`)}
                          className="border-b border-[var(--border)] hover:bg-[var(--bg-secondary)] cursor-pointer transition-colors"
                        >
                          <td className="px-4 py-2 font-mono text-xs">
                            #{s.id}
                          </td>
                          <td className="px-4 py-2 text-xs text-[var(--text-secondary)]">
                            {s.region_label || s.region || "—"}
                          </td>
                          <td className="px-4 py-2 text-xs text-[var(--text-secondary)]">
                            {s.timestamp
                              ? new Date(s.timestamp).toLocaleString()
                              : "—"}
                          </td>
                          <td className="px-4 py-2 text-right font-mono text-xs">
                            {((s.area_m2 || 0) / 1e6).toFixed(2)}
                          </td>
                          <td className="px-4 py-2 text-right font-mono text-xs">
                            {s.slick_confidence
                              ? (s.slick_confidence * 100).toFixed(0) + "%"
                              : "—"}
                          </td>
                          <td className="px-4 py-2 text-xs">
                            <span
                              className={
                                s.source === "historical"
                                  ? "text-amber-400"
                                  : "text-green-400"
                              }
                            >
                              {s.source === "historical" ? "Archive" : "Live"}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/drift?spill=${s.id}`);
                              }}
                              className="text-xs bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-2 py-1 rounded"
                            >
                              Investigate →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>

          {/* ============ ALL REGIONS SECTION ============ */}
          <div className="space-y-4 pt-4 border-t border-[var(--border)]">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-2xl">🌍</span>
              <div>
                <h2 className="text-xl font-bold">All Monitored Regions</h2>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  {spills.length} total spills across all monitored ocean areas
                </p>
              </div>
              <div className="flex-1 h-px bg-[var(--border)] ml-2" />
              {Object.keys(regions).length > 0 && (
                <div className="flex items-center gap-2">
                  <label className="text-xs text-[var(--text-muted)] uppercase">
                    Filter:
                  </label>
                  <select
                    value={regionFilter}
                    onChange={(e) => setRegionFilter(e.target.value)}
                    className="bg-[var(--bg-card)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                  >
                    <option value="">All regions ({spills.length})</option>
                    {Object.entries(regions).map(
                      ([slug, r]: [string, any]) => (
                        <option key={slug} value={slug}>
                          {r.label} ({r.count})
                        </option>
                      )
                    )}
                  </select>
                </div>
              )}
            </div>

            <div className="grid grid-cols-4 gap-4">
              <StatCard label="Detected Slicks" value={filtered.length} />
              <StatCard
                label="Live (72h)"
                value={filtered.filter((s) => s.source === "live").length}
              />
              <StatCard
                label="Archive"
                value={filtered.filter((s) => s.source === "historical").length}
              />
              <StatCard
                label="Total Area (km²)"
                value={(
                  filtered.reduce((a, s) => a + (s.area_m2 || 0), 0) / 1e6
                ).toFixed(1)}
              />
            </div>

            <MapView
              polygons={allMap.polygons}
              markers={allMap.markers}
              legend={legend}
              height="440px"
            />

            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-[var(--border)] font-semibold text-sm">
                All Recent Detections · click any row to investigate
              </div>
              <table className="w-full text-sm">
                <thead className="text-xs text-[var(--text-muted)] uppercase">
                  <tr className="border-b border-[var(--border)]">
                    <th className="text-left px-4 py-2">ID</th>
                    <th className="text-left px-4 py-2">Region</th>
                    <th className="text-left px-4 py-2">Time</th>
                    <th className="text-right px-4 py-2">Area (km²)</th>
                    <th className="text-right px-4 py-2">Confidence</th>
                    <th className="text-left px-4 py-2">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(0, 25).map((s) => (
                    <tr
                      key={s.id}
                      onClick={() => navigate(`/drift?spill=${s.id}`)}
                      className="border-b border-[var(--border)] hover:bg-[var(--bg-secondary)] cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-2 font-mono text-xs">#{s.id}</td>
                      <td className="px-4 py-2 text-xs text-[var(--text-secondary)]">
                        {s.region_label || s.region || "—"}
                      </td>
                      <td className="px-4 py-2 text-xs text-[var(--text-secondary)]">
                        {s.timestamp
                          ? new Date(s.timestamp).toLocaleString()
                          : "—"}
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-xs">
                        {((s.area_m2 || 0) / 1e6).toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-xs">
                        {s.slick_confidence
                          ? (s.slick_confidence * 100).toFixed(0) + "%"
                          : "—"}
                      </td>
                      <td className="px-4 py-2 text-xs">
                        <span
                          className={
                            s.source === "historical"
                              ? "text-amber-400"
                              : "text-green-400"
                          }
                        >
                          {s.source === "historical" ? "Archive" : "Live"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: any;
  accent?: string;
}) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4">
      <div className="text-xs text-[var(--text-muted)] uppercase tracking-wider">
        {label}
      </div>
      <div
        className="text-2xl font-bold mt-1"
        style={{ color: accent || "var(--accent-hover)" }}
      >
        {value}
      </div>
    </div>
  );
}