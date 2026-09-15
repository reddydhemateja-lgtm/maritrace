import { MapContainer, TileLayer, Polygon, Marker, Popup, Circle, Polyline, CircleMarker } from "react-leaflet";
import L from "leaflet";

// Fix default marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

export interface MapPolygon {
  positions: [number, number][];
  color?: string;
  fillOpacity?: number;
  label?: string;
}

export interface MapMarker {
  position: [number, number];
  label: string;
  color?: string;
  radius?: number;
}

export interface MapPolyline {
  positions: [number, number][];
  color?: string;
  weight?: number;
  dashed?: boolean;
}

export interface MapCircle {
  center: [number, number];
  radiusKm: number;
  color?: string;
  label?: string;
}

export interface LegendItem {
  color: string;
  label: string;
  shape?: "line" | "fill" | "dot";
}

interface Props {
  center?: [number, number];
  zoom?: number;
  polygons?: MapPolygon[];
  markers?: MapMarker[];
  circles?: MapCircle[];
  polylines?: MapPolyline[];
  legend?: LegendItem[];
  height?: string;
}

export default function MapView({
  center = [19.5, 72.0],
  zoom = 6,
  polygons = [],
  markers = [],
  circles = [],
  polylines = [],
  legend = [],
  height = "500px",
}: Props) {
  return (
    <div
      style={{ height, position: "relative" }}
      className="rounded-lg overflow-hidden border border-[var(--border)]"
    >
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: "100%", width: "100%" }}
      >
        {/* Esri World Imagery — satellite tiles, no API key, no watermark */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics"
          maxZoom={19}
        />

        {polygons.map((p, i) => (
          <Polygon
            key={`poly-${i}`}
            positions={p.positions}
            pathOptions={{
              color: p.color || "#c97b3f",
              fillOpacity: p.fillOpacity ?? 0.35,
              weight: 2,
            }}
          >
            {p.label && <Popup>{p.label}</Popup>}
          </Polygon>
        ))}

        {polylines.map((l, i) => (
          <Polyline
            key={`line-${i}`}
            positions={l.positions}
            pathOptions={{
              color: l.color || "#c97b3f",
              weight: l.weight ?? 2,
              opacity: 0.9,
              dashArray: l.dashed ? "6 6" : undefined,
            }}
          />
        ))}

        {circles.map((c, i) => (
          <Circle
            key={`circle-${i}`}
            center={c.center}
            radius={c.radiusKm * 1000}
            pathOptions={{
              color: c.color || "#c97b3f",
              fillOpacity: 0.08,
              weight: 1.5,
              dashArray: "6 6",
            }}
          >
            {c.label && <Popup>{c.label}</Popup>}
          </Circle>
        ))}

        {markers.map((m, i) =>
          m.radius ? (
            <CircleMarker
              key={`dot-${i}`}
              center={m.position}
              radius={m.radius}
              pathOptions={{
                color: "#fff",
                fillColor: m.color || "#c97b3f",
                fillOpacity: 1,
                weight: 2,
              }}
            >
              <Popup>{m.label}</Popup>
            </CircleMarker>
          ) : (
            <Marker key={`marker-${i}`} position={m.position}>
              <Popup>{m.label}</Popup>
            </Marker>
          )
        )}
      </MapContainer>

      {/* Legend overlay — warm cream card matching the palette */}
      {legend.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: "12px",
            right: "12px",
            zIndex: 1000,
            background: "rgba(245, 235, 224, 0.96)",
            border: "1px solid #d6ccc2",
            borderRadius: "8px",
            padding: "10px 14px",
            fontSize: "11px",
            color: "#3d2f24",
            boxShadow: "0 4px 12px rgba(61, 47, 36, 0.25)",
            pointerEvents: "none",
            minWidth: "160px",
          }}
        >
          <div
            style={{
              fontWeight: 600,
              fontSize: "10px",
              letterSpacing: "0.05em",
              marginBottom: "6px",
              color: "#6b5a4a",
              textTransform: "uppercase",
            }}
          >
            Legend
          </div>
          {legend.map((item, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "5px",
              }}
            >
              <span
                style={{
                  display: "inline-block",
                  width: item.shape === "line" ? 18 : item.shape === "dot" ? 10 : 12,
                  height: item.shape === "line" ? 3 : item.shape === "dot" ? 10 : 12,
                  background: item.color,
                  borderRadius: item.shape === "dot" ? "50%" : "2px",
                  border: item.shape === "fill" ? `2px solid ${item.color}` : "none",
                  opacity: item.shape === "fill" ? 0.7 : 1,
                  flexShrink: 0,
                }}
              />
              <span style={{ color: "#6b5a4a", whiteSpace: "nowrap" }}>
                {item.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}