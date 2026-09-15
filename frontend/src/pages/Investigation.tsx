import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, Search, FileText, Download } from "lucide-react";
import { api } from "../api/client";
import type { Spill, Investigation as Inv } from "../api/types";
import ScoreBar from "../components/ScoreBar";
import MapView from "../components/MapView";

export default function Investigation() {
  const [searchParams] = useSearchParams();
  const autoSpillId = searchParams.get("spill");

  const [spills, setSpills] = useState<Spill[]>([]);
  const [selected, setSelected] = useState<Spill | null>(null);
  const [result, setResult] = useState<Inv | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.recentSpills().then((r: any) => {
      const loaded = r.spills || [];
      setSpills(loaded);
      if (autoSpillId) {
        const target = loaded.find(
          (s: Spill) => String(s.id) === String(autoSpillId)
        );
        if (target) runInvestigation(target);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoSpillId]);

  const runInvestigation = async (spill: Spill) => {
    setSelected(spill);
    setLoading(true);
    setResult(null);
    try {
      const res: any = await api.investigate(spill.id);
      setResult(res);
    } catch (e: any) {
      alert("Investigation failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const slickPolygon: [number, number][] =
    selected?.geometry?.coordinates?.[0]?.[0]?.map(
      ([lon, lat]: [number, number]) => [lat, lon] as [number, number]
    ) || [];

  const downloadReport = () => {
    if (!result) return;
    const url = api.reportUrl(result.case_number);
    window.open(url, "_blank");
  };

  // Sort spills: Indian regions first, then Persian Gulf, then everything else
  const sortedSpills = [...spills].sort((a, b) => {
    const priority = (s: Spill) => {
      const r = (s.region || "").toLowerCase();
      if (r.startsWith("india")) return 0;
      if (r === "persian_gulf") return 1;
      return 2;
    };
    const pa = priority(a);
    const pb = priority(b);
    if (pa !== pb) return pa - pb;
    return (b.timestamp || "").localeCompare(a.timestamp || "");
  });

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Investigation</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Slick → hindcast origin → AIS correlation → 5-factor ranking
          </p>
        </div>
        {result && (
          <button
            onClick={downloadReport}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2"
          >
            <Download size={14} /> Download Evidence PDF
          </button>
        )}
      </div>

      <div className="grid grid-cols-4 gap-6">
        <div className="col-span-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4 max-h-[700px] overflow-auto">
          <div className="text-xs uppercase text-[var(--text-muted)] mb-3">
            Select a slick ({spills.length}) · Indian spills first
          </div>
          {sortedSpills.slice(0, 40).map((s) => (
            <button
              key={s.id}
              onClick={() => runInvestigation(s)}
              className={`w-full text-left p-3 rounded mb-1 border transition-colors ${
                selected?.id === s.id
                  ? "border-[var(--accent)] bg-[var(--accent)]/10"
                  : "border-[var(--border)] hover:bg-[var(--bg-secondary)]"
              }`}
            >
              <div className="text-xs font-mono">#{s.id}</div>
              <div className="text-[10px] text-[var(--text-muted)]">
                {s.region_label || s.region || "—"}
              </div>
            </button>
          ))}
        </div>

        <div className="col-span-3 space-y-4">
          {loading && (
            <div className="flex items-center justify-center gap-3 p-12 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg">
              <Loader2 className="animate-spin text-[var(--accent)]" />
              Running attribution pipeline…
            </div>
          )}

          {!loading && !result && (
            <div className="flex flex-col items-center justify-center gap-2 p-16 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg text-center">
              <Search className="text-[var(--text-muted)]" size={28} />
              <p className="text-sm text-[var(--text-secondary)]">
                Select a slick on the left to run the attribution pipeline.
              </p>
            </div>
          )}

          {result && (
            <>
              <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-3">
                    <FileText className="text-[var(--accent)]" size={22} />
                    <div>
                      <div className="text-xs text-[var(--text-muted)] uppercase">
                        Case ·{" "}
                        {selected?.region_label ||
                          selected?.region ||
                          "Unknown Region"}
                      </div>
                      <div className="text-lg font-bold font-mono">
                        {result.case_number}
                      </div>
                      <div className="text-xs text-[var(--text-muted)] mt-0.5">
                        Slick #{selected?.id}
                        {selected?.slick_url && (
                          <>
                            {" · "}
                            <a
                              href={selected.slick_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[var(--accent-hover)] hover:underline"
                            >
                              View in Cerulean
                            </a>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-xs text-[var(--text-muted)]">
                    <div>
                      Origin: {result.origin.lat.toFixed(4)},{" "}
                      {result.origin.lon.toFixed(4)}
                    </div>
                    <div>
                      Time: {new Date(result.origin.time).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-[var(--border)] flex items-center justify-between flex-wrap gap-3">
                  <div className="text-xs text-[var(--text-muted)]">
                    Report will be filed under case{" "}
                    <span className="font-mono text-[var(--text-primary)]">
                      {result.case_number}
                    </span>{" "}
                    for{" "}
                    <span className="text-[var(--text-primary)]">
                      {selected?.region_label || selected?.region}
                    </span>
                  </div>
                  <button
                    onClick={downloadReport}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2"
                  >
                    <Download size={14} />
                    Download Report · Slick #{selected?.id}
                  </button>
                </div>
              </div>

              <MapView
                polygons={
                  slickPolygon.length
                    ? [
                        {
                          positions: slickPolygon,
                          color: "#f59e0b",
                          fillOpacity: 0.35,
                          label: `Slick #${selected?.id}`,
                        },
                      ]
                    : []
                }
                circles={[
                  {
                    center: [result.origin.lat, result.origin.lon],
                    radiusKm: 50,
                    color: "#ef4444",
                    label: "50 km search radius",
                  },
                ]}
                markers={[
                  {
                    position: [result.origin.lat, result.origin.lon],
                    label: "🎯 Probable origin",
                    color: "#ef4444",
                    radius: 8,
                  },
                ]}
                legend={[
                  {
                    color: "#f59e0b",
                    label: "Detected slick",
                    shape: "fill" as const,
                  },
                  {
                    color: "#ef4444",
                    label: "Search radius / origin",
                    shape: "dot" as const,
                  },
                ]}
                center={[result.origin.lat, result.origin.lon]}
                zoom={7}
                height="380px"
              />

              <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-[var(--border)] font-semibold text-sm flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <Search size={14} /> Vessel Candidates
                    <span className="text-xs font-normal text-[var(--text-muted)]">
                      ({result.candidates.length})
                    </span>
                  </div>
                  <button
                    onClick={downloadReport}
                    className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded flex items-center gap-1.5"
                  >
                    <Download size={12} /> Download Report
                  </button>
                </div>
                <table className="w-full text-sm">
                  <thead className="text-xs text-[var(--text-muted)] uppercase">
                    <tr className="border-b border-[var(--border)]">
                      <th className="text-left px-4 py-2">Rank</th>
                      <th className="text-left px-4 py-2">Vessel</th>
                      <th className="text-left px-4 py-2">MMSI</th>
                      <th className="text-right px-4 py-2">Distance</th>
                      <th className="text-left px-4 py-2">Score Breakdown</th>
                      <th className="text-right px-4 py-2">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.candidates.map((c) => (
                      <tr
                        key={c.mmsi}
                        className="border-b border-[var(--border)] hover:bg-[var(--bg-secondary)]"
                      >
                        <td className="px-4 py-3 font-bold text-[var(--accent-hover)]">
                          #{c.rank}
                        </td>
                        <td className="px-4 py-3 text-xs">
                          <div className="font-medium">
                            {c.name || "Unknown"}
                            {c.synthetic && (
                              <span className="ml-1 text-[10px] text-amber-400">
                                (demo)
                              </span>
                            )}
                          </div>
                          {c.flag && (
                            <div className="text-[10px] text-[var(--text-muted)]">
                              {c.flag}
                              {c.type && ` · ${c.type}`}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs">{c.mmsi}</td>
                        <td className="px-4 py-3 text-right font-mono text-xs">
                          {c.min_distance_km != null
                            ? `${c.min_distance_km.toFixed(2)} km`
                            : "—"}
                        </td>
                        <td className="px-4 py-3">
                          <div className="grid grid-cols-1 gap-1 max-w-xs">
                            <ScoreBar
                              label="Spatial"
                              value={c.spatial_score}
                              weight={30}
                            />
                            <ScoreBar
                              label="Temporal"
                              value={c.temporal_score}
                              weight={25}
                              color="#f59e0b"
                            />
                            <ScoreBar
                              label="Trajectory"
                              value={c.trajectory_score}
                              weight={25}
                              color="#10b981"
                            />
                            <ScoreBar
                              label="Drift"
                              value={c.drift_score}
                              weight={10}
                              color="#a855f7"
                            />
                            <ScoreBar
                              label="Anomaly"
                              value={c.anomaly_score}
                              weight={10}
                              color="#ec4899"
                            />
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="text-lg font-bold text-[var(--accent-hover)]">
                            {c.total_score.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}