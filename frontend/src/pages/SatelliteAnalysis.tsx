import { useState } from "react";
import { Upload, Play, Loader2 } from "lucide-react";

export default function SatelliteAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!file) return;
    setAnalyzing(true);
    await new Promise((r) => setTimeout(r, 1500));
    setResult({
      confidence: 0.87,
      area_km2: 12.4,
      classification: { oil: 0.62, "look-alike": 0.31, clean: 0.07 },
    });
    setAnalyzing(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">SAR Analysis</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Upload Sentinel-1 imagery to detect oil slicks
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-6">
          <div className="text-xs uppercase text-[var(--text-muted)] mb-3">Input</div>
          <label className="border-2 border-dashed border-[var(--border)] rounded-lg p-8 flex flex-col items-center cursor-pointer hover:border-[var(--accent)] transition-colors">
            <Upload className="text-[var(--accent)] mb-3" />
            <span className="text-sm text-[var(--text-secondary)]">
              {file ? file.name : "Drop SAR image or click to browse"}
            </span>
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
          <button
            onClick={handleAnalyze}
            disabled={!file || analyzing}
            className="w-full mt-4 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 text-white py-2 rounded-md text-sm font-medium flex items-center justify-center gap-2"
          >
            {analyzing ? (
              <><Loader2 className="animate-spin" size={16} /> Analyzing…</>
            ) : (
              <><Play size={16} /> Analyze</>
            )}
          </button>
        </div>

        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-6">
          <div className="text-xs uppercase text-[var(--text-muted)] mb-3">Results</div>
          {!result ? (
            <div className="text-sm text-[var(--text-muted)] text-center py-12">No analysis yet</div>
          ) : (
            <div className="space-y-4">
              <Row label="Confidence" value={(result.confidence * 100).toFixed(1) + "%"} />
              <Row label="Area" value={result.area_km2 + " km²"} />
              <div>
                <div className="text-xs text-[var(--text-muted)] mb-2">Classification</div>
                {Object.entries(result.classification).map(([k, v]: any) => (
                  <div key={k} className="flex items-center gap-3 mb-1">
                    <span className="w-24 text-xs capitalize">{k}</span>
                    <div className="flex-1 h-2 bg-[var(--bg-secondary)] rounded">
                      <div className="h-full rounded bg-[var(--accent)]" style={{ width: `${v * 100}%` }} />
                    </div>
                    <span className="text-xs font-mono w-12 text-right">{(v * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex justify-between border-b border-[var(--border)] pb-2">
      <span className="text-xs text-[var(--text-muted)]">{label}</span>
      <span className="text-sm font-mono text-[var(--accent-hover)]">{value}</span>
    </div>
  );
}