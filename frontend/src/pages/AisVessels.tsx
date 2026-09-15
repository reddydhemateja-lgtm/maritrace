import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { api } from "../api/client";
import type { Vessel } from "../api/types";
import MapView from "../components/MapView";

export default function AisVessels() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const originParam = searchParams.get("origin");
  const spillId = searchParams.get("spill");
  const radiusKm = Number(searchParams.get("radius") || 150);

  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const origin: [number, number] | undefined = originParam
    ? (() => {
        const [lat, lon] = originParam.split(",").map(Number);
        return [lat, lon];
      })()
    : undefined;

  const load = async () => {
    try {
      const r: any = await api.aisVessels();
      setVessels(r.vessels || []);
      setLastUpdate(new Date());
    } catch {}
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  const distKm = (
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ) => {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  };

  const markers = vessels.slice(0, 300).map((v) => {
    let inRadius = false;
    let dist: number | null = null;
    if (origin) {
      dist = distKm(origin[0], origin[1], v.lat, v.lon);
      inRadius = dist <= radiusKm;
    }
    return {
      position: [v.lat, v.lon] as [number, number],
      label: `${v.name || "Unknown"} · MMSI ${v.mmsi}${
        dist != null ? ` · ${dist.toFixed(1)} km from origin` : ""
      }`,
      color: inRadius ? "#ef4444" : "#1f90df",
      radius: inRadius ? 6 : 3,
    };
  });

  if (origin) {
    markers.push({
      position: origin,
      label: `🎯 Spill origin (${radiusKm} km search radius)`,
      color: "#f59e0b",
      radius: 9,
    });
  }

  const suspects = origin
    ? vessels.filter(
        (v) => distKm(origin[0], origin[1], v.lat, v.lon) <= radiusKm
      )
    : [];

  const goToInvestigation = () => {
    if (spillId) navigate(`/investigation?spill=${spillId}`);
  };

  const legend: any[] = [];
  if (origin) {
    legend.push(
      { color: "#f59e0b", label: "Spill origin", shape: "dot" as const },
      {
        color: "#ef4444",
        label: `Suspects (<${radiusKm} km) — ${suspects.length}`,
        shape: "dot" as const,
      },
      { color: "#1f90df", label: "Other vessels", shape: "dot" as const }
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">AIS Vessel Intelligence</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            {origin
              ? `Showing vessels around hindcast origin: ${origin[0].toFixed(
                  4
                )}, ${origin[1].toFixed(4)} · ${radiusKm} km radius`
              : "Live vessel positions from AISStream · refreshes every 10s"}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right text-xs text-[var(--text-muted)]">
            <div>{vessels.length} vessels</div>
            {lastUpdate && <div>Updated {lastUpdate.toLocaleTimeString()}</div>}
          </div>
          {spillId && (
            <button
              onClick={goToInvestigation}
              className="bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2"
            >
              Continue to Investigation <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>

      {origin && (
        <div className="p-3 bg-[var(--bg-secondary)] border-l-4 border-red-500 rounded text-sm text-[var(--text-secondary)]">
          <strong className="text-[var(--text-primary)]">
            How to read this map:
          </strong>{" "}
          The <span className="text-amber-400">orange dot</span> is the spill
          origin. The{" "}
          <span className="text-red-400">red dashed circle</span> is our{" "}
          {radiusKm} km search radius.{" "}
          <span className="text-red-400">Red dots</span> inside the circle are{" "}
          <strong>suspect vessels</strong> — these are the candidates the
          attribution model will score next.
        </div>
      )}

      <MapView
        markers={markers}
        center={origin}
        zoom={origin ? 6 : 5}
        circles={
          origin
            ? [
                {
                  center: origin,
                  radiusKm: radiusKm,
                  color: "#ef4444",
                  label: `${radiusKm} km search radius`,
                },
              ]
            : []
        }
        legend={legend}
        height="520px"
      />

      <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--border)] font-semibold text-sm">
          {origin
            ? `Suspects within ${radiusKm} km (${suspects.length})`
            : "Live Vessel Roster"}
        </div>
        <table className="w-full text-sm">
          <thead className="text-xs text-[var(--text-muted)] uppercase">
            <tr className="border-b border-[var(--border)]">
              <th className="text-left px-4 py-2">MMSI</th>
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-right px-4 py-2">Distance</th>
              <th className="text-right px-4 py-2">SOG</th>
              <th className="text-right px-4 py-2">COG</th>
            </tr>
          </thead>
          <tbody>
            {(origin ? suspects : vessels).slice(0, 50).map((v) => {
              const d = origin
                ? distKm(origin[0], origin[1], v.lat, v.lon)
                : null;
              return (
                <tr
                  key={v.mmsi}
                  className="border-b border-[var(--border)] hover:bg-[var(--bg-secondary)]"
                >
                  <td className="px-4 py-2 font-mono text-xs">{v.mmsi}</td>
                  <td className="px-4 py-2 text-xs">{v.name || "—"}</td>
                  <td className="px-4 py-2 text-right font-mono text-xs">
                    {d != null ? `${d.toFixed(1)} km` : "—"}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-xs">
                    {v.sog?.toFixed(1) ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-xs">
                    {v.cog?.toFixed(0) ?? "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}