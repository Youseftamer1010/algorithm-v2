const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000');

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

async function postAPI<T>(path: string, body: unknown): Promise<T> {
  return fetchAPI<T>(path, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface GraphNode {
  id: number; name: string; lat: number; lon: number;
  population: number; type: string; importance: number;
  icon: string; color: string;
}

export interface GraphEdge {
  u: number; v: number; distance: number; capacity: number;
  condition: number; cost: number; base_time: number;
  road_type: string; is_potential: boolean; color: string;
}

export interface RouteResult {
  found: boolean; algorithm: string; nodes: number[];
  path: string[]; edges: GraphEdge[];
  distance: number; time: number; congestion: number;
}

export interface RaceStep {
  visited: number[]; current: number;
  dist_snapshot?: Record<string, number>;
  f_score_snapshot?: Record<string, number>;
}

export interface RaceResult {
  dijkstra: { steps: RaceStep[]; path: number[]; total_time: number | null; nodes_explored: number };
  astar: { steps: RaceStep[]; path: number[]; total_time: number | null; nodes_explored: number };
  source: number; target: number;
}

export interface MSTResult {
  algorithm: string; mst_edges: GraphEdge[];
  total_cost: number; total_distance: number; total_time: number;
  edge_count: number; connected: boolean; nodes_covered: number;
}

export interface MetricData {
  avg_congestion: number; network_score: number;
  total_roads: number; free_flow: number; gridlock: number;
}

export interface MLPrediction {
  congestion: number; level: string; input: Record<string, number>;
}

export interface TransitRoute {
  route_id: string
  route_name: string
  mode: 'bus' | 'metro'
  stops: string[]
  total_distance_km: number
  estimated_time_minutes: number
  frequency_minutes: number
  status: string
}

// ── API Functions ─────────────────────────────────────────────────────────────

export const api = {
  // Graph
  graphSummary: () => fetchAPI<Record<string, unknown>>('/api/graph/summary'),
  graphNodes: () => fetchAPI<GraphNode[]>('/api/graph/nodes'),
  graphEdges: (includePotential = false) =>
    fetchAPI<GraphEdge[]>(`/api/graph/edges?include_potential=${includePotential}`),
  trafficPatterns: () => fetchAPI<Record<string, Record<string, number>>>('/api/traffic-patterns'),
  busRoutes: () => fetchAPI<Record<string, { name: string; nodes: number[] }>>('/api/bus-routes'),
  metroLines: () => fetchAPI<Record<string, unknown>>('/api/metro-lines'),

  // Routes
  routeDijkstra: (source: number, target: number, timeIndex = 0, mode = 'car') =>
    postAPI<RouteResult>('/api/route/dijkstra', { source, target, time_index: timeIndex, mode }),
  routeAstar: (source: number, target: number, timeIndex = 0, mode = 'emergency') =>
    postAPI<RouteResult>('/api/route/astar', { source, target, time_index: timeIndex, mode }),
  routeTimeDep: (source: number, target: number, timeIndex = 0, mode = 'car') =>
    postAPI<RouteResult>('/api/route/time-dependent', { source, target, time_index: timeIndex, mode }),
  routeKShortest: (source: number, target: number, k = 3, timeIndex = 0, mode = 'car') =>
    postAPI<RouteResult[]>('/api/route/k-shortest', { source, target, k, time_index: timeIndex, mode }),
  routeRace: (source: number, target: number, timeIndex = 0, mode = 'car') =>
    postAPI<RaceResult>('/api/route/race', { source, target, time_index: timeIndex, mode }),
  routeMLAware: (source: number, target: number, timeIndex = 0, mode = 'car', hour?: number, day?: number) =>
    postAPI<RouteResult & { ml_adjusted: boolean; ml_predictions: Array<{ u: number; v: number; ml_time: number; predicted_congestion: number }>; ml_hour: number; ml_day: number }>(
      '/api/route/ml-aware', { source, target, time_index: timeIndex, mode, hour_of_day: hour, day_of_week: day }),

  // MST
  mstKruskal: (includePotential = false, prioritize = true) =>
    fetchAPI<MSTResult>(`/api/mst/kruskal?include_potential=${includePotential}&prioritize_facilities=${prioritize}`),
  mstPrim: (includePotential = false, prioritize = true) =>
    fetchAPI<MSTResult>(`/api/mst/prim?include_potential=${includePotential}&prioritize_facilities=${prioritize}`),
  mstCompare: (includePotential = false, prioritize = true) =>
    fetchAPI<{ kruskal: MSTResult; prim: MSTResult; cost_diff: number; distance_diff: number }>(
      `/api/mst/compare?include_potential=${includePotential}&prioritize_facilities=${prioritize}`),

  // Optimization
  signals: (timeIndex = 0) => fetchAPI<Record<string, unknown>>(`/api/optimization/signals?time_index=${timeIndex}`),
  busSchedule: (routeKey = 'B1', numBuses = 5, timeIndex = 0) =>
    postAPI<Record<string, unknown>>('/api/optimization/bus', { route_key: routeKey, num_buses: numBuses, time_index: timeIndex }),
  maintenance: (budget = 500, timeIndex = 0) =>
    postAPI<Record<string, unknown>>('/api/optimization/maintenance', { budget_m_egp: budget, time_index: timeIndex }),
  emergency: (incidents: { location: number; severity: number }[]) =>
    postAPI<Record<string, unknown>>('/api/optimization/emergency', { incidents }),
  greedyAnalysis: (timeIndex = 0) => fetchAPI<Record<string, unknown>>(`/api/optimization/greedy-analysis?time_index=${timeIndex}`),

  // Simulation
  simMetrics: (timeIndex = 0, scenario = 'normal') =>
    fetchAPI<MetricData>(`/api/simulation/metrics?time_index=${timeIndex}&scenario=${scenario}`),
  simHeatmap: (timeIndex = 0, scenario = 'normal') =>
    fetchAPI<Record<string, unknown>[]>(`/api/simulation/heatmap?time_index=${timeIndex}&scenario=${scenario}`),
  simCompareRoutes: (source = 0, target = 3, timeIndex = 0, scenario = 'normal') =>
    fetchAPI<Record<string, unknown>>(`/api/simulation/compare-routes?source=${source}&target=${target}&time_index=${timeIndex}&scenario=${scenario}`),

  // Transit
  transitRoutes: () => fetchAPI<{ routes: TransitRoute[] }>('/api/transit/routes'),

  // ML
  mlPredict: (features: Record<string, number>) => postAPI<MLPrediction>('/api/ml/predict', features),
  mlFeatureImportance: () => fetchAPI<Record<string, number>>('/api/ml/feature-importance'),
  mlMetrics: () => fetchAPI<Record<string, unknown>>('/api/ml/metrics'),
};
