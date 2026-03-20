import type {
  DashboardSummary,
  DistrictProfile,
  PublicReport,
  TrendData,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new APIError(res.status, `API error ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

// ── GeoJSON type for map endpoints ─────────────────────────────

interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    geometry: Record<string, unknown>;
    properties: Record<string, unknown>;
  }>;
}

// ── Map layers ─────────────────────────────────────────────────

export function fetchBoundaries(level?: number): Promise<GeoJSONFeatureCollection> {
  const query = level != null ? `?level=${level}` : '';
  return apiFetch(`/map/boundaries${query}`);
}

export function fetchIncidents(): Promise<GeoJSONFeatureCollection> {
  return apiFetch('/map/incidents');
}

export function fetchBrickKilns(): Promise<GeoJSONFeatureCollection> {
  return apiFetch('/map/kilns');
}

export interface BorderCrossingPoint {
  id: number;
  name: string;
  borderCountry: string;
  lat: number;
  lon: number;
  vulnerabilityScore: number | null;
}

export function fetchBorderCrossings(): Promise<BorderCrossingPoint[]> {
  return apiFetch('/map/borders');
}

export function fetchTraffickingRoutes(): Promise<GeoJSONFeatureCollection> {
  return apiFetch('/map/routes');
}

// ── Legal ──────────────────────────────────────────────────────

export interface JudgmentResponse {
  id: number;
  courtName: string;
  caseNumber: string;
  judgmentDate: string;
  ppcSections: string[];
  verdict: string;
  sentenceYears: number | null;
}

export function fetchCourtJudgments(params?: {
  court?: string;
  year?: number;
  ppcSection?: string;
  verdict?: string;
  page?: number;
  limit?: number;
}): Promise<JudgmentResponse[]> {
  const search = new URLSearchParams();
  if (params?.court) search.set('court', params.court);
  if (params?.year) search.set('year', String(params.year));
  if (params?.ppcSection) search.set('ppc_section', params.ppcSection);
  if (params?.verdict) search.set('verdict', params.verdict);
  if (params?.page) search.set('page', String(params.page));
  if (params?.limit) search.set('limit', String(params.limit));
  const qs = search.toString();
  return apiFetch(`/legal/search${qs ? `?${qs}` : ''}`);
}

// ── Districts ──────────────────────────────────────────────────

export interface DistrictListItem {
  pcode: string;
  nameEn: string;
  nameUr: string;
  province: string;
}

export function fetchDistrictList(): Promise<DistrictListItem[]> {
  return apiFetch('/districts/');
}

export interface DistrictProfileResponse {
  pcode: string;
  nameEn: string;
  nameUr: string;
  province: string;
  population: number | null;
  incidents: number;
  kilnCount: number;
  vulnerability: number | null;
  convictionRate: number | null;
  recentReports: number;
  centroidLat: number | null;
  centroidLon: number | null;
}

export function fetchDistrictProfile(pcode: string): Promise<DistrictProfileResponse> {
  return apiFetch(`/districts/${pcode}`);
}

export interface DistrictIncident {
  year: number;
  count: number;
}

export function fetchDistrictIncidents(pcode: string, years?: number): Promise<DistrictIncident[]> {
  const query = years ? `?years=${years}` : '';
  return apiFetch(`/districts/${pcode}/incidents${query}`);
}

export function fetchVulnerability(pcode: string): Promise<Record<string, unknown>> {
  return apiFetch(`/districts/${pcode}/vulnerability`);
}

// ── Dashboard ──────────────────────────────────────────────────

export interface DashboardSummaryResponse {
  totalIncidents: number;
  districtsWithData: number;
  dataSourcesActive: number;
  avgConvictionRate: number;
}

export function fetchDashboardSummary(): Promise<DashboardSummaryResponse> {
  return apiFetch('/dashboard/summary');
}

export interface TrendDataResponse {
  year: number;
  count: number;
  source: string;
}

export function fetchTrendData(params?: {
  province?: string;
  incidentType?: string;
}): Promise<TrendDataResponse[]> {
  const search = new URLSearchParams();
  if (params?.province) search.set('province', params.province);
  if (params?.incidentType) search.set('incident_type', params.incidentType);
  const qs = search.toString();
  return apiFetch(`/dashboard/trends${qs ? `?${qs}` : ''}`);
}

export interface ProvinceComparisonItem {
  province: string;
  pcode: string;
  count: number;
  perCapita: number | null;
}

export function fetchProvinceComparison(year?: number): Promise<ProvinceComparisonItem[]> {
  const query = year ? `?year=${year}` : '';
  return apiFetch(`/dashboard/province-comparison${query}`);
}

export interface CaseTypeItem {
  type: string;
  count: number;
  percentage: number;
}

export function fetchCaseTypes(province?: string): Promise<CaseTypeItem[]> {
  const query = province ? `?province=${province}` : '';
  return apiFetch(`/dashboard/case-types${query}`);
}

export interface ConvictionRateItem {
  year: number;
  investigations: number;
  prosecutions: number;
  convictions: number;
  rate: number;
}

export function fetchConvictionRates(years?: number): Promise<ConvictionRateItem[]> {
  const query = years ? `?years=${years}` : '';
  return apiFetch(`/dashboard/conviction-rates${query}`);
}

// ── Scrapers ──────────────────────────────────────────────────

export interface ScraperStatusResponse {
  id: number;
  name: string;
  scraperName: string | null;
  sourceType: string | null;
  url: string | null;
  isActive: boolean;
  lastScraped: string | null;
  lastUpdated: string | null;
  recordCount: number;
  articlesLast24h: number;
  status: 'healthy' | 'warning' | 'error' | 'inactive';
  schedule: string | null;
  notes: string | null;
}

export interface ScrapersSummaryResponse {
  totalScrapers: number;
  activeScrapers: number;
  healthyScrapers: number;
  warningScrapers: number;
  errorScrapers: number;
  totalArticles: number;
  articlesLast24h: number;
  lastActivity: string | null;
}

export function fetchScrapers(): Promise<ScraperStatusResponse[]> {
  return apiFetch('/scrapers/');
}

export function fetchScrapersSummary(): Promise<ScrapersSummaryResponse> {
  return apiFetch('/scrapers/summary');
}

// ── Admin / Reports ────────────────────────────────────────────

export interface PendingReportItem {
  id: number;
  reportType: string;
  status: string;
  districtPcode: string | null;
  createdAt: string;
}

export function fetchPendingReports(params?: {
  status?: string;
  page?: number;
  limit?: number;
}): Promise<PendingReportItem[]> {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.page) search.set('page', String(params.page));
  if (params?.limit) search.set('limit', String(params.limit));
  const qs = search.toString();
  return apiFetch(`/reports/${qs ? `?${qs}` : ''}`);
}

// ── Public Reports ─────────────────────────────────────────────

export function submitPublicReport(report: {
  reportType: string;
  description: string;
  latitude?: number;
  longitude?: number;
  reporterName?: string;
  reporterContact?: string;
  isAnonymous: boolean;
}): Promise<Record<string, unknown>> {
  return apiFetch('/reports/', {
    method: 'POST',
    body: JSON.stringify(report),
  });
}

export { APIError };
