/* ------------------------------------------------------------------
 * Nigehbaan — Core TypeScript Interfaces
 * ----------------------------------------------------------------*/

// ── GeoJSON primitives ──────────────────────────────────────────

export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [number, number]; // [lng, lat]
}

export interface GeoJSONLineString {
  type: 'LineString';
  coordinates: [number, number][];
}

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: [number, number][][];
}

export interface GeoJSONMultiPolygon {
  type: 'MultiPolygon';
  coordinates: [number, number][][][];
}

export type GeoJSONGeometry =
  | GeoJSONPoint
  | GeoJSONLineString
  | GeoJSONPolygon
  | GeoJSONMultiPolygon;

export interface GeoJSONFeature<G extends GeoJSONGeometry = GeoJSONGeometry, P = Record<string, unknown>> {
  type: 'Feature';
  id?: string | number;
  geometry: G;
  properties: P;
}

export interface GeoJSONFeatureCollection<G extends GeoJSONGeometry = GeoJSONGeometry, P = Record<string, unknown>> {
  type: 'FeatureCollection';
  features: GeoJSONFeature<G, P>[];
}

// ── Domain entities ─────────────────────────────────────────────

export interface Boundary {
  id: string;
  adminLevel: number;
  nameEn: string;
  nameUr: string;
  pcode: string;
  parentPcode: string | null;
  geometry: GeoJSONPolygon | GeoJSONMultiPolygon;
  population: number | null;
}

export type IncidentType =
  | 'kidnapping'
  | 'child_trafficking'
  | 'sexual_abuse'
  | 'sexual_exploitation'
  | 'online_exploitation'
  | 'child_labor'
  | 'bonded_labor'
  | 'child_marriage'
  | 'child_murder'
  | 'honor_killing'
  | 'begging_ring'
  | 'organ_trafficking'
  | 'missing'
  | 'physical_abuse'
  | 'child_pornography'
  | 'abandonment'
  | 'medical_negligence'
  | 'other';

export type VictimGender = 'male' | 'female' | 'unknown';

export type SourceType = 'media' | 'ngo' | 'court' | 'government' | 'public_report';

export interface Incident {
  id: string;
  sourceType: SourceType;
  year: number;
  districtPcode: string;
  incidentType: IncidentType;
  victimCount: number;
  victimGender: VictimGender;
  geometry: GeoJSONPoint | null;
}

export type KilnType = 'active' | 'inactive' | 'unknown';

export interface BrickKiln {
  id: string;
  geometry: GeoJSONPoint;
  kilnType: KilnType;
  nearestSchoolM: number | null;
  nearestHospitalM: number | null;
  population1km: number | null;
  districtPcode: string;
}

export type CrossingType = 'formal' | 'informal';

export interface BorderCrossing {
  id: string;
  name: string;
  borderCountry: string;
  crossingType: CrossingType;
  geometry: GeoJSONPoint;
  vulnerabilityScore: number;
}

export type TraffickingType = 'internal' | 'cross_border';

export interface TraffickingRoute {
  id: string;
  routeName: string;
  originPcode: string;
  destinationPcode: string;
  routeGeometry: GeoJSONLineString;
  traffickingType: TraffickingType;
}

export type Verdict = 'convicted' | 'acquitted' | 'pending' | 'dismissed';

export interface CourtJudgment {
  id: string;
  courtName: string;
  caseNumber: string;
  judgmentDate: string;
  ppcSections: string[];
  verdict: Verdict;
  sentenceYears: number | null;
}

export interface VulnerabilityIndicator {
  districtPcode: string;
  year: number;
  povertyRate: number;
  dropoutRate: number;
  kilnCount: number;
  riskScore: number;
}

export type ReportStatus = 'submitted' | 'under_review' | 'verified' | 'rejected';

export type ReportType =
  | 'suspicious_activity'
  | 'missing_child'
  | 'bonded_labor'
  | 'begging_ring'
  | 'child_marriage'
  | 'other';

export interface PublicReport {
  id: string;
  reportType: ReportType;
  description: string;
  geometry: GeoJSONPoint | null;
  status: ReportStatus;
  createdAt: string;
}

// ── Composite / View models ─────────────────────────────────────

export interface DistrictProfile {
  boundary: Boundary;
  incidents: Incident[];
  kilns: BrickKiln[];
  vulnerability: VulnerabilityIndicator | null;
  convictionRate: number | null;
}

export interface DashboardSummary {
  totalIncidents: number;
  districtsWithData: number;
  dataSources: number;
  avgConvictionRate: number;
}

export interface TrendData {
  year: number;
  count: number;
  source: SourceType;
}

// ── API helpers ─────────────────────────────────────────────────

export interface APIResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  meta?: PaginationMeta;
}

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// ── Map layer identifiers ───────────────────────────────────────

export type MapLayerId =
  | 'incidents'
  | 'kilns'
  | 'routes'
  | 'borders'
  | 'poverty'
  | 'flood';
