import React, { useState, useEffect } from 'react';
import { Ship, SlidersHorizontal, Play, ArrowRight, ChevronRight, MapPin, RefreshCw } from 'lucide-react';
import { IncidentData, VesselData, PageId } from '../types';
import { MapView } from '../components/MapView';
import { VesselTable } from '../components/VesselTable';
import { EvidencePanel } from '../components/EvidencePanel';
import { coastalLocations } from '../data/locations';
import { api } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';

interface AISIntelligenceProps {
  incident: IncidentData;
  vessels: VesselData[];
  selectedVessel: VesselData | null;
  onSelectVessel: (vessel: VesselData) => void;
  onNavigate: (page: PageId) => void;
  onLocationChange: (incident: IncidentData) => void;
}

export const AISIntelligence: React.FC<AISIntelligenceProps> = ({
  incident: initialIncident,
  vessels: initialVessels,
  selectedVessel,
  onSelectVessel,
  onNavigate,
  onLocationChange,
}) => {
  const [incident, setIncident] = useState<IncidentData>(initialIncident);
  const [vessels, setVessels] = useState<VesselData[]>(initialVessels);
  const [timeWindow, setTimeWindow] = useState('24h');
  const [radius, setRadius] = useState('50km');
  const [vesselType, setVesselType] = useState('All');
  const [speedFilter, setSpeedFilter] = useState('Any');
  const [isFiltering, setIsFiltering] = useState(false);
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const currentVessel = selectedVessel || vessels[0];

 const WS_URL = (import.meta.env.VITE_WS_URL as string) || 'wss://maritrace.onrender.com/ws';
const { isConnected, lastMessage } = useWebSocket(WS_URL);
  useEffect(() => {
    if (lastMessage) {
      try {
        const msg = JSON.parse(lastMessage);
        if (msg.type === 'vessel_update') {
          setVessels(prev =>
            prev.map(v =>
              v.mmsi === msg.mmsi
                ? { ...v, currentLat: msg.lat, currentLon: msg.lon, speedKnots: msg.speed }
                : v
            )
          );
        }
      } catch (e) { /* ignore */ }
    }
  }, [lastMessage]);

  const fetchRankedVessels = async (incidentId: string) => {
    try {
      const data = await api.getVessels(incidentId);
      setVessels(data);
    } catch (e) {
      console.error('Failed to fetch ranked vessels:', e);
    }
  };

  const handleApplyFilter = () => {
    setIsFiltering(true);
    setTimeout(() => setIsFiltering(false), 400);
  };

  const handleLocationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = coastalLocations.find(loc => loc.id === e.target.value);
    if (selected) {
      const fullIncident: IncidentData = {
        ...selected,
        candidateVesselsCount: 7,
      };
      setIncident(fullIncident);
      onLocationChange(fullIncident);
      fetchRankedVessels(fullIncident.id);
    }
  };

  // Real incident note
  const isMSCELSA = incident.id === 'MR-2025-027';
  const realIncidentNote = isMSCELSA
    ? 'AIS investigation based on MSC ELSA 3 incident (25 May 2025). Vessel capsized off Kerala coast, AIS signal lost at 14:00 UTC.'
    : '';

  return (
    <div className="p-4 sm:p-6 space-y-4 max-w-7xl mx-auto bg-[#EBE0DC] text-[#1A3A5C] min-h-screen">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#1F90DF]/30">
        <div className="flex items-center gap-3">
          <h1 className="text-xl sm:text-2xl font-bold text-[#1A3A5C] tracking-tight flex items-center gap-2">
            <Ship className="w-5 h-5 text-[#1F90DF]" />
            AIS Vessel Intelligence
          </h1>
          <div className="relative">
            <select
              value={incident.id}
              onChange={handleLocationChange}
              className="bg-white border border-[#1F90DF]/30 rounded-lg px-3 py-1.5 text-sm text-[#1A3A5C] focus:outline-none focus:border-[#1F90DF] cursor-pointer shadow-sm"
            >
              {coastalLocations.map(loc => (
                <option key={loc.id} value={loc.id}>{loc.locationName}</option>
              ))}
            </select>
          </div>
          <div className={`flex items-center gap-1.5 text-xs font-mono ${isConnected ? 'text-emerald-600' : 'text-rose-600'}`}>
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            {isConnected ? 'Live' : 'Offline'}
          </div>
        </div>
        <button
          onClick={() => onNavigate('investigation')}
          className="px-4 py-2 rounded-lg bg-[#1F90DF] hover:bg-[#1879C4] text-white text-xs font-medium shadow transition flex items-center gap-2"
        >
          <span>Investigate</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {realIncidentNote && (
        <div className="p-2 rounded-lg bg-[#1F90DF]/5 border border-[#1F90DF]/20 text-xs text-[#1A3A5C]/80 flex items-start gap-2">
          <Ship className="w-4 h-4 text-[#1F90DF] flex-shrink-0" />
          <span>{realIncidentNote}</span>
        </div>
      )}

      {/* Filters */}
      <div className="p-3 rounded-xl bg-white/90 border border-[#1F90DF]/30 shadow-sm flex flex-wrap items-center gap-2 text-xs font-mono">
        <div className="flex items-center gap-1 text-[#1A3A5C] font-semibold">
          <SlidersHorizontal className="w-3.5 h-3.5 text-[#1F90DF]" />
          <span>FILTERS</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            value={timeWindow}
            onChange={e => setTimeWindow(e.target.value)}
            className="bg-white border border-[#1F90DF]/30 rounded px-2 py-1 text-xs text-[#1A3A5C] focus:outline-none focus:border-[#1F90DF]"
          >
            <option>12h</option><option>24h</option><option>48h</option>
          </select>
          <select
            value={radius}
            onChange={e => setRadius(e.target.value)}
            className="bg-white border border-[#1F90DF]/30 rounded px-2 py-1 text-xs text-[#1A3A5C]"
          >
            <option>25km</option><option>50km</option><option>100km</option>
          </select>
          <select
            value={vesselType}
            onChange={e => setVesselType(e.target.value)}
            className="bg-white border border-[#1F90DF]/30 rounded px-2 py-1 text-xs text-[#1A3A5C]"
          >
            <option>All</option><option>Tankers</option><option>Cargo</option>
          </select>
          <select
            value={speedFilter}
            onChange={e => setSpeedFilter(e.target.value)}
            className="bg-white border border-[#1F90DF]/30 rounded px-2 py-1 text-xs text-[#1A3A5C]"
          >
            <option>Any speed</option><option>Slow ({'<'}10kt)</option><option>Transit (10‑16kt)</option>
          </select>
        </div>
        <button
          onClick={handleApplyFilter}
          disabled={isFiltering}
          className="px-3 py-1 rounded bg-[#1F90DF] hover:bg-[#1879C4] text-white text-xs font-medium shadow transition"
        >
          {isFiltering ? '…' : 'Apply'}
        </button>
        <button
          onClick={() => fetchRankedVessels(incident.id)}
          className="p-1 rounded bg-white/80 hover:bg-[#1F90DF]/10 text-[#1A3A5C] border border-[#1F90DF]/20 transition"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#1F90DF]" />
        </button>
      </div>

      {/* Map */}
      <div>
        <div className="text-xs text-[#1A3A5C]/70 mb-1 flex justify-between">
          <span className="font-medium">Vessel tracks & origin zone</span>
          <span>Click marker or table row to view details</span>
        </div>
        <MapView
          key={incident.id + vessels.length}
          incident={incident}
          vessels={vessels}
          selectedVessel={currentVessel}
          onSelectVessel={(v) => { onSelectVessel(v); setEvidenceModalOpen(true); }}
          heightClass="h-[460px]"
          mapType="satellite"
        />
      </div>

      {/* Vessel Table */}
      <VesselTable
        vessels={vessels}
        selectedVessel={currentVessel}
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

      {/* Bottom CTA */}
      <div className="p-3 rounded-xl bg-white/90 border border-[#1F90DF]/30 shadow-sm flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="text-[#1A3A5C]/80">
          Top candidate: <span className="font-bold text-[#1F90DF]">{vessels[0]?.name || 'None'}</span> (Score: {vessels[0]?.totalAssociationScore || 0}%)
        </span>
        <button
          onClick={() => onNavigate('investigation')}
          className="px-4 py-1.5 rounded bg-[#1F90DF] hover:bg-[#1879C4] text-white font-medium text-xs transition flex items-center gap-1.5"
        >
          <span>Full investigation</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};