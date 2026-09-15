import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { ArrowRight, Loader2 } from "lucide-react";
import { api } from "../api/client";
import type { Spill, HindcastResult } from "../api/types";
import MapView from "../components/MapView";

export default function DriftAnalysis() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const autoSpillId = searchParams.get("spill");

  const [spills, setSpills] = useState<Spill[]>([]);
  const [selected, setSelected] = useState<Spill | null>(null);
  const [hindcast, setHindcast] = useState<HindcastResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.recentSpills().then((r: any) => {
      const loaded = r.spills || [];
      setSpills(loaded);
      if (autoSpillId) {
        const target = loaded.find(
          (s: Spill) => String(s.id) === String(autoSpillId)
        );
        if (target) runHindcast(target);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoSpillId]);

  const runHindcast = async (spill: Spill) => {
    setSelected(spill);
    setHindcast(null);
    setLoading(true);
    try {
      const res: any = await api.hindcast(spill.id);
      setHindcast(res);
    } catch (e: any) {
      alert("Hindcast failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const slickCoords: [number, number][] =
    selected?.geometry?.coordinates?.[0]?.[0]?.map(
      ([lon, lat]: [number, number]) => [lat, lon] as [number, number]
    ) || [];

  // Compute slick center for annotation
  const slickCenter: [number, number] | null = slickCoords.length
    ? [
        slickCoords.reduce((a, c) => a + c[0], 0) / slickCoords.length,
        slickCoords.reduce((a, c) => a + c[1], 0) / slickCoords.length,
      ]
    : null;

  // Build drift rays — lines + arrowheads
  const driftLines: [number, number][][] = [];
  const arrowHeads: [number, number][][] = [];
  if (hindcast && slickCenter) {
    const origin: [number, number] = [hindcast.origin_lat, hindcast.origin_lon];

    // Main line: slick center → origin
    driftLines.push([slickCenter, origin]);
    arrowHeads.push(_arrowHead(slickCenter, origin));

    // Fan of rays to visualize ensemble spread
    const dx = origin[0] - slickCenter[0];
    const dy = origin[1] - slickCenter[1];
    for (const deg of [-25, -15, -5, 5, 15, 25]) {
      const rad = (deg * Math.PI) / 180;
      const rx = dx * Math.cos(rad) - dy * Math.sin(rad);
      const ry = dx * Math.sin(rad) + dy * Math.cos(rad);
      const tip: [number, number] = [slickCenter[0] + rx, slickCenter[1] + ry];
      driftLines.push([slickCenter, tip]);
      arrowHeads.push(_arrowHead(slickCenter, tip));
    }
  }

  const markers: any[] = [];
  if (hindcast && slickCenter) {
    markers.push({
      position: [hindcast.origin_lat, hindcast.origin_lon],
      label: `🎯 Origin (spill started here ~${new Date(
        hindcast.origin_time
      ).toLocaleString()})`,
      color: "#ef4444",
      radius: 9,
    });
    markers.push({
      position: slickCenter,
      label: `📍 Detected here on ${
        selected ? new Date(selected.timestamp).toLocaleString() : ""
      }`,
      color: "#f59e0b",
      radius: 7,
    });
  }

  const legend: any[] = [];
  if (hindcast) {
    legend.push(
      { color: "#f59e0b", label: "Detected slick", shape: "fill" as const },
      { color: "#1f90df", label: "Drift trajectory + arrowhead", shape: "line" as const },
      { color: "#ef4444", label: "Probable origin", shape: "dot" as const }
    );
  }

  const goToAis = () => {
    if (!hindcast) return;
    navigate(
      `/ais?origin=${hindcast.origin_lat.toFixed(4)},${hindcast.origin_lon.toFixed(
        4
      )}&spill=${selected?.id}&radius=150`
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Drift Analysis</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Traces the slick backward in time to find where the spill started
          </p>
        </div>
        {hindcast && (
          <button
            onClick={goToAis}
            className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2"
          >
            Continue to AIS Vessels <ArrowRight size={14} />
          </button>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4 max-h-[600px] overflow-auto">
          <div className="text-xs uppercase text-[var(--text-muted)] mb-3">
            Select a slick
          </div>
          <div className="space-y-2">
            {spills.slice(0, 40).map((s) => (
              <button
                key={s.id}
                onClick={() => runHindcast(s)}
                className={`w-full text-left p-3 rounded border transition-colors ${
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
        </div>

        <div className="col-span-2 space-y-4">
          {hindcast && (
            <>
              <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4 grid grid-cols-4 gap-4">
                <Info label="Origin Lat" value={hindcast.origin_lat.toFixed(4)} />
                <Info label="Origin Lon" value={hindcast.origin_lon.toFixed(4)} />
                <Info
                  label="Origin Time"
                  value={new Date(hindcast.origin_time).toLocaleString()}
                />
                <Info label="Ensembles" value={String(hindcast.ensemble_count)} />
              </div>

              <div className="p-3 bg-[var(--bg-secondary)] border-l-4 border-[var(--accent)] rounded text-sm text-[var(--text-secondary)]">
                <strong className="text-[var(--text-primary)]">
                  How to read this map:
                </strong>{" "}
                The <span className="text-amber-400">orange polygon</span> is
                where the oil was detected. The{" "}
                <span className="text-[#5fa8d3]">blue rays with arrowheads</span>{" "}
                show the drift path calculated backward in time. The{" "}
                <span className="text-red-400">red dot</span> is the probable
                origin — where the spill likely started.
              </div>
            </>
          )}

          {loading ? (
            <div className="flex items-center justify-center gap-3 p-12 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg">
              <Loader2 className="animate-spin text-[var(--accent)]" />
              Computing hindcast…
            </div>
          ) : (
            <MapView
              polygons={[
                ...(slickCoords.length
                  ? [
                      {
                        positions: slickCoords,
                        color: "#f59e0b",
                        fillOpacity: 0.4,
                        label: `Slick #${selected?.id}`,
                      },
                    ]
                  : []),
                ...arrowHeads.map((head) => ({
                  positions: head,
                  color: "#1f90df",
                  fillOpacity: 1,
                })),
              ]}
              polylines={driftLines.map((line) => ({
                positions: line,
                color: "#1f90df",
                weight: 2,
              }))}
              markers={markers}
              circles={
                hindcast
                  ? [
                      {
                        center: [hindcast.origin_lat, hindcast.origin_lon],
                        radiusKm: 5,
                        color: "#ef4444",
                        label: "Probable origin zone",
                      },
                    ]
                  : []
              }
              legend={legend}
              center={
                hindcast
                  ? [hindcast.origin_lat, hindcast.origin_lon]
                  : undefined
              }
              zoom={7}
              height="560px"
            />
          )}
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-[var(--text-muted)] uppercase">{label}</div>
      <div className="text-sm font-mono text-[var(--accent-hover)] mt-1">
        {value}
      </div>
    </div>
  );
}

/**
 * Build a triangular arrowhead polygon pointing from `from` toward `to`.
 * Placed at ~95% of the way along the line so it doesn't overlap the origin dot.
 */
function _arrowHead(
  from: [number, number],
  to: [number, number]
): [number, number][] {
  const HEAD_LEN = 0.35; // arrowhead length in degrees
  const HALF_WIDTH = 0.15; // arrowhead half-width in degrees

  const dLat = to[0] - from[0];
  const dLon = to[1] - from[1];
  const len = Math.sqrt(dLat * dLat + dLon * dLon) || 1e-6;

  // Unit vector
  const ux = dLon / len;
  const uy = dLat / len;

  // Perpendicular
  const px = -uy;
  const py = ux;

  const tipT = 0.95;
  const baseT = Math.max(0, tipT - HEAD_LEN / len);

  const tipLat = from[0] + dLat * tipT;
  const tipLon = from[1] + dLon * tipT;

  const baseLat = from[0] + dLat * baseT;
  const baseLon = from[1] + dLon * baseT;

  const leftLat = baseLat + py * HALF_WIDTH;
  const leftLon = baseLon + px * HALF_WIDTH;

  const rightLat = baseLat - py * HALF_WIDTH;
  const rightLon = baseLon - px * HALF_WIDTH;

  return [
    [tipLat, tipLon],
    [leftLat, leftLon],
    [rightLat, rightLon],
    [tipLat, tipLon],
  ];
}