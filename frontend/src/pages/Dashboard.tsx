import React, { useState, useEffect } from 'react';
import {
  Satellite,
  FileSearch,
  ShieldAlert,
  Compass,
  Layers,
  Ship,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { IncidentData, VesselData, PageId } from '../types';
import { StatCard } from '../components/StatCard';
import { MapView } from '../components/MapView';
import { VesselTable } from '../components/VesselTable';
import { EvidencePanel } from '../components/EvidencePanel';
import { ClassificationPieChart, SpillGrowthAreaChart } from '../components/Charts';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../services/api';
import { coastalLocations } from '../data/locations';

interface DashboardProps {
  incident: IncidentData;
  vessels: VesselData[];
  selectedVessel: VesselData | null;
  onSelectVessel: (vessel: VesselData) => void;
  onNavigate: (page: PageId) => void;
  onLocationChange: (incident: IncidentData) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  incident: initialIncident,
  vessels: initialVessels,
  selectedVessel,
  onSelectVessel,
  onNavigate,
  onLocationChange,
}) => {
  const [incident, setIncident] = useState<IncidentData>(initialIncident);
  const [vessels, setVessels] = useState<VesselData[]>(initialVessels);
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [alerts, setAlerts] = useState<Array<{ id: string; message: string; time: string }>>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const topCandidate = vessels[0];

  // WebSocket for live updates
 const WS_URL = (import.meta.env.VITE_WS_URL as string) || 'wss://maritrace.onrender.com/ws';
const { isConnected, lastMessage } = useWebSocket(WS_URL);
  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const msg = JSON.parse(lastMessage);
        if (msg.type === 'new_spill') {
          setAlerts(prev => [
            { id: msg.incident.id, message: `New spill detected at ${msg.incident.location}`, time: new Date().toLocaleTimeString() },
            ...prev.slice(0, 4),
          ]);
          fetchIncidentData(msg.incident.id);
        } else if (msg.type === 'vessel_update') {
          setVessels(prev =>
            prev.map(v =>
              v.mmsi === msg.mmsi
                ? { ...v, currentLat: msg.lat, currentLon: msg.lon, speedKnots: msg.speed }
                : v
            )
          );
        }
      } catch (e) {
        console.warn('Invalid WebSocket message', e);
      }
    }
  }, [lastMessage]);

  const fetchIncidentData = async (id: string) => {
    try {
      const data = await api.getIncident(id);
      setIncident(data);
      onLocationChange(data);
      setLastUpdate(new Date());
    } catch (e) {
      console.error('Failed to fetch incident:', e);
    }
  };

  const refreshVessels = async () => {
    setIsRefreshing(true);
    try {
      const data = await api.getVessels(incident.id);
      setVessels(data);
      setLastUpdate(new Date());
    } catch (e) {
      console.error('Failed to fetch vessels:', e);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Handle location/incident selection from dropdown
  const handleIncidentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedId = e.target.value;
    const location = coastalLocations.find(loc => loc.id === selectedId);
    if (location) {
      // Convert to full IncidentData
      const fullIncident: IncidentData = {
        id: location.id,
        name: location.name || location.locationName,
        status: location.status as any,
        severity: location.severity as any,
        detectionTime: location.detectionTime,
        satellitePlatform: location.satellitePlatform || 'Sentinel-1B',
        sensor: location.sensor || 'C-Band IW',
        resolutionMeters: location.resolutionMeters || 10,
        latitude: location.latitude,
        longitude: location.longitude,
        locationName: location.locationName,
        spillAreaKm2: location.spillAreaKm2,
        spillLengthKm: location.spillLengthKm || 0,
        spillMaxWidthKm: location.spillMaxWidthKm || 0,
        orientation: location.orientation || '',
        confidence: location.confidence,
        oilProbability: location.oilProbability || location.confidence,
        lookalikeProbability: location.lookalikeProbability || 0,
        noOilProbability: location.noOilProbability || 0,
        probableOriginLat: location.probableOriginLat,
        probableOriginLon: location.probableOriginLon,
        originConfidence: location.originConfidence || 0,
        estimatedSpillTime: location.estimatedSpillTime,
        candidateVesselsCount: 7,
      };
      setIncident(fullIncident);
      onLocationChange(fullIncident);
      // Refresh vessels for the new incident
      setTimeout(() => refreshVessels(), 100);
    }
  };

  return (
    <div className="p-4 sm:p-6 space-y-4 max-w-7xl mx-auto bg-[#EBE0DC] text-[#1A3A5C] min-h-screen">
      {/* Header with Incident Selector */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#1F90DF]/30">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-xl sm:text-2xl font-bold text-[#1A3A5C] tracking-tight">
            Command Center
          </h1>
          {/* Incident Dropdown – Switch between historical spills */}
          <select
            value={incident.id}
            onChange={handleIncidentChange}
            className="bg-white border border-[#1F90DF]/30 rounded-lg px-3 py-1.5 text-sm text-[#1A3A5C] focus:outline-none focus:border-[#1F90DF] cursor-pointer shadow-sm"
          >
            <option value="MR-2010-MUMBAI">🌊 Mumbai Oil Spill 2010</option>
            <option value="MR-2017-ENNORE">🌊 Ennore Oil Spill 2017</option>
            <option value="MR-2025-KERALA">🌊 Kerala Oil Spill 2025</option>
            <option value="MR-2026-0147">📍 Mumbai (Demo)</option>
            <option value="MR-2026-0189">📍 Goa (Demo)</option>
            <option value="MR-2026-0213">📍 Kochi (Demo)</option>
            <option value="MR-2026-0220">📍 Chennai (Demo)</option>
            <option value="MR-2026-0235">📍 Visakhapatnam (Demo)</option>
            <option value="MR-2026-0248">📍 Puri (Demo)</option>
            <option value="MR-2026-0255">📍 Digha (Demo)</option>
            <option value="MR-2026-0262">📍 Andaman (Demo)</option>
            <option value="MR-2026-0275">📍 Lakshadweep (Demo)</option>
          </select>

          {/* Live status indicator */}
          <div className={`flex items-center gap-1.5 text-xs font-mono ${isConnected ? 'text-emerald-600' : 'text-rose-600'}`}>
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></span>
            {isConnected ? 'Live' : 'Offline'}
          </div>

          {/* Refresh button */}
          <button
            onClick={refreshVessels}
            disabled={isRefreshing}
            className="p-1.5 rounded-lg bg-white/80 hover:bg-[#1F90DF]/10 text-[#1A3A5C] border border-[#1F90DF]/20 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 text-[#1F90DF] ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onNavigate('satellite')}
            className="px-3 py-1.5 rounded bg-white/80 hover:bg-[#1F90DF]/10 text-[#1A3A5C] text-xs font-medium border border-[#1F90DF]/20 transition"
          >
            <Satellite className="w-3.5 h-3.5 inline mr-1" /> SAR
          </button>
          <button
            onClick={() => onNavigate('investigation')}
            className="px-4 py-1.5 rounded bg-[#1F90DF] hover:bg-[#1879C4] text-white text-xs font-medium transition flex items-center gap-1.5"
          >
            <FileSearch className="w-3.5 h-3.5" /> Investigation
          </button>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="p-2 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-500" />
          <span className="font-semibold">Alert:</span>
          <span>{alerts[0].message}</span>
          <span className="ml-auto text-rose-400/80">{alerts[0].time}</span>
        </div>
      )}

      {/* Incident Banner */}
      <div className="p-3 rounded-xl bg-white/90 border border-[#1F90DF]/30 shadow-sm flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-[#1F90DF]" />
          <span className="font-semibold">{incident.id}</span>
          <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-700 text-[10px] font-medium border border-amber-200">
            {incident.status}
          </span>
          <span className="text-[#1A3A5C]/60">{incident.locationName}</span>
        </div>
        <span className="text-[#1A3A5C]/60 font-mono text-[10px]">
          {incident.detectionTime ? new Date(incident.detectionTime).toLocaleDateString() : ''}
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          label="Spill Area"
          value={`${incident.spillAreaKm2} km²`}
          icon={Layers}
          color="blue"
        />
        <StatCard
          label="Confidence"
          value={`${incident.confidence}%`}
          icon={Satellite}
          color="blue"
        />
        <StatCard
          label="Origin"
          value={`${incident.probableOriginLat}°N`}
          subValue={`${incident.probableOriginLon}°E`}
          icon={Compass}
          color="blue"
        />
        <StatCard
          label="Candidates"
          value={vessels.filter(v => v.isCandidate).length}
          icon={Ship}
          color="blue"
        />
      </div>

      {/* Map */}
      <div>
        <div className="flex justify-between text-xs text-[#1A3A5C]/60 mb-1">
          <span>Geospatial canvas (live)</span>
          <span>Vessel positions update every 2 min</span>
        </div>
        <MapView
          key={incident.id + vessels.length}
          incident={incident}
          vessels={vessels}
          selectedVessel={selectedVessel}
          onSelectVessel={(v) => { onSelectVessel(v); setEvidenceModalOpen(true); }}
          heightClass="h-[420px]"
          mapType="satellite"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-3 rounded-xl bg-white/90 border border-[#1F90DF]/30 shadow-sm">
          <div className="text-xs font-semibold text-[#1A3A5C] uppercase tracking-wider">Detection</div>
          <ClassificationPieChart
            oilProb={incident.oilProbability}
            lookalikeProb={incident.lookalikeProbability}
            noOilProb={incident.noOilProbability}
          />
        </div>
        <div className="p-3 rounded-xl bg-white/90 border border-[#1F90DF]/30 shadow-sm">
          <div className="text-xs font-semibold text-[#1A3A5C] uppercase tracking-wider">Spill Growth</div>
          <SpillGrowthAreaChart />
        </div>
        <div className="p-3 rounded-xl bg-white/90 border border-[#1F90DF]/30 shadow-sm">
          <div className="text-xs font-semibold text-[#1A3A5C] uppercase tracking-wider">Top Candidate</div>
          {topCandidate && (
            <div className="mt-2">
              <div className="font-bold text-[#1F90DF]">{topCandidate.name}</div>
              <div className="text-xs text-[#1A3A5C]/70">Score: {topCandidate.totalAssociationScore}%</div>
              <div className="w-full h-2 bg-[#EBE0DC] rounded mt-1">
                <div
                  className="h-full bg-[#1F90DF] rounded"
                  style={{ width: `${topCandidate.totalAssociationScore}%` }}
                />
              </div>
              <button
                onClick={() => { onSelectVessel(topCandidate); setEvidenceModalOpen(true); }}
                className="mt-2 text-xs text-[#1F90DF] hover:underline"
              >
                View evidence →
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Vessel Table */}
      <VesselTable
        vessels={vessels}
        selectedVessel={selectedVessel}
        onSelectVessel={onSelectVessel}
        onInspectEvidence={(v) => { onSelectVessel(v); setEvidenceModalOpen(true); }}
      />

      {/* Evidence Modal */}
      {evidenceModalOpen && selectedVessel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="w-full max-w-2xl">
            <EvidencePanel
              vessel={selectedVessel}
              onClose={() => setEvidenceModalOpen(false)}
              onNavigateToInvestigation={() => {
                setEvidenceModalOpen(false);
                onNavigate('investigation');
              }}
              isModal
            />
          </div>
        </div>
      )}
    </div>
  );
};