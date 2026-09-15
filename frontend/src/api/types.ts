export interface Spill {
  id: number;
  timestamp: string;
  geometry: any;
  area_m2: number | null;
  length_m: number | null;
  perimeter_m: number | null;
  linearity: number | null;
  fill_factor: number | null;
  polsby_popper: number | null;
  slick_confidence: number | null;
  max_source_collated_score: number | null;
  hitl_cls_name: string | null;
  s1_scene_id: string | null;
  slick_url: string | null;
  region?: string;
  region_label?: string;
  source?: "live" | "historical";
}

export interface Vessel {
  mmsi: number;
  name: string;
  ship_type: number | null;
  lon: number;
  lat: number;
  sog: number | null;
  cog: number | null;
  heading: number | null;
  last_ts: string | null;
}

export interface Candidate {
  mmsi: number;
  name?: string;
  type?: number | string | null;
  flag?: string;
  synthetic?: boolean;
  rank: number;
  total_score: number;
  spatial_score: number;
  temporal_score: number;
  trajectory_score: number;
  drift_score: number;
  anomaly_score: number;
  min_distance_km: number | null;
  closest_ts: string | null;
}

export interface Investigation {
  case_number: string;
  slick_id: number;
  origin: { lon: number; lat: number; time: string };
  candidates: Candidate[];
  created_at?: string;
}

export interface HindcastResult {
  slick_id: number;
  origin_lon: number;
  origin_lat: number;
  origin_time: string;
  cone_wkt: string | null;
  ensemble_count: number;
}