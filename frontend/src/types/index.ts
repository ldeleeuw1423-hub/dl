export type UserRole = "pm" | "engineer" | "om" | "admin" | "viewer";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  organization?: string;
  organization_id?: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

export type ProjectPhase = "VO" | "DO" | "UO" | "Realisatie";
export type ProjectDiscipline = "Gas" | "Elektra" | "LS_MS" | "Stations";
export type ProjectStatus = "active" | "on_hold" | "completed" | "cancelled";

export interface Project {
  id: string;
  project_number: string;
  name: string;
  client?: string;
  location?: string;
  phase: ProjectPhase;
  discipline: ProjectDiscipline;
  start_date?: string;
  end_date?: string;
  status: ProjectStatus;
  scope_description?: string;
  budget_estimated?: number;
  budget_actual?: number;
  hours_estimated?: number;
  hours_actual?: number;
  organization_id?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectListItem extends Project {
  risks_count: number;
  permits_count: number;
}

export interface ProjectCreate {
  project_number: string;
  name: string;
  client?: string;
  location?: string;
  phase: ProjectPhase;
  discipline: ProjectDiscipline;
  start_date?: string;
  end_date?: string;
  status?: ProjectStatus;
  scope_description?: string;
  budget_estimated?: number;
}

export type RiskCategory =
  | "Technisch"
  | "Planning"
  | "Financieel"
  | "Omgeving"
  | "Vergunning"
  | "Stakeholder"
  | "Overig";

export type RiskStatus = "open" | "mitigated" | "accepted" | "closed";
export type RiskSource = "gis" | "ai" | "manual";

export interface Risk {
  id: string;
  project_id: string;
  description: string;
  category: RiskCategory;
  probability: number;
  impact: number;
  score: number;
  owner?: string;
  mitigation_measure?: string;
  deadline?: string;
  status: RiskStatus;
  residual_risk?: number;
  auto_detected: boolean;
  source: RiskSource;
  created_at: string;
  updated_at: string;
}

export interface RiskCreate {
  description: string;
  category: RiskCategory;
  probability: number;
  impact: number;
  owner?: string;
  mitigation_measure?: string;
  deadline?: string;
  status?: RiskStatus;
  residual_risk?: number;
}

export interface Estimation {
  id: string;
  project_id: string;
  version: number;
  discipline?: string;
  hours_engineering?: number;
  hours_pm?: number;
  hours_om?: number;
  hours_workprep?: number;
  hours_execution?: number;
  cost_materials?: number;
  cost_total?: number;
  bandwidth_low?: number;
  bandwidth_high?: number;
  confidence_score?: number;
  methodology?: string;
  similar_projects?: SimilarProjectRef[];
  reasoning?: string;
  is_current: boolean;
  created_at: string;
}

export interface SimilarProjectRef {
  reference_number: string;
  name: string;
  similarity_score: number;
  hours_total?: number;
  cost_total?: number;
}

export interface EstimationGenerateRequest {
  discipline?: string;
  scope_description?: string;
  trace_length_m?: number;
  num_crossings?: number;
  num_permits?: number;
  num_stakeholders?: number;
  location_type?: string;
  phase?: string;
}

export type PermitAuthority = "gemeente" | "provincie" | "waterschap" | "prorail" | "rws" | "overig";
export type PermitStatus =
  | "required"
  | "in_preparation"
  | "submitted"
  | "approved"
  | "rejected"
  | "not_required";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface Permit {
  id: string;
  project_id: string;
  permit_type: string;
  description?: string;
  authority: PermitAuthority;
  status: PermitStatus;
  submission_date?: string;
  expected_approval?: string;
  actual_approval?: string;
  risk_level: RiskLevel;
  delay_probability?: number;
  owner?: string;
  notes?: string;
  auto_detected: boolean;
  created_at: string;
  updated_at: string;
}

export interface PermitCreate {
  permit_type: string;
  description?: string;
  authority: PermitAuthority;
  status?: PermitStatus;
  submission_date?: string;
  expected_approval?: string;
  risk_level?: RiskLevel;
  delay_probability?: number;
  owner?: string;
  notes?: string;
}

export interface HistoricalProject {
  id: string;
  reference_number: string;
  name: string;
  discipline: string;
  location_type: string;
  trace_length_m?: number;
  num_crossings?: number;
  num_permits?: number;
  num_stakeholders?: number;
  hours_engineering?: number;
  hours_pm?: number;
  hours_om?: number;
  hours_workprep?: number;
  cost_execution?: number;
  cost_total?: number;
  duration_days?: number;
  num_revisions?: number;
  risks_count?: number;
  issues_count?: number;
  created_at: string;
  similarity_score?: number;
}

export interface GISLayer {
  id: string;
  name: string;
  url: string;
  type: "WMS" | "WFS" | "WMTS";
  layers: string[];
}

export interface PDOKAnalysisResult {
  geometry_type: string;
  analysis: {
    estimated_length_m?: number;
    estimated_area_m2?: number;
    num_points?: number;
    location?: { longitude: number; latitude: number };
  };
  risks: Array<{
    description: string;
    category: string;
    probability: number;
    impact: number;
    source?: string;
  }>;
  permits_likely: string[];
  notes: string[];
  pdok?: {
    gemeente?: string;
    natura2000_proximity?: boolean;
    address_count?: number;
    urban_density?: "laag" | "gemiddeld" | "hoog";
    crossings?: {
      waterways: number;
      major_roads: number;
      railways: number;
      cycle_paths: number;
    };
    error?: string;
  };
}

export interface APIError {
  detail: string | { msg: string; type: string }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// ---------------------------------------------------------------------------
// Multi-tenant — Organization types
// ---------------------------------------------------------------------------

export type SubscriptionTier = "free" | "professional" | "enterprise";

export interface OrganizationSettings {
  hourly_rate_engineering?: number;
  hourly_rate_pm?: number;
  hourly_rate_om?: number;
  hourly_rate_workprep?: number;
  hourly_rate_execution?: number;
  risk_threshold_high?: number;
  risk_threshold_critical?: number;
  custom_disciplines?: string[];
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  subscription_tier: SubscriptionTier;
  max_projects: number;
  max_users: number;
  settings?: OrganizationSettings & Record<string, unknown>;
  created_at: string;
}

export interface OrganizationUpdate {
  name?: string;
  settings?: Partial<OrganizationSettings> & Record<string, unknown>;
}

export interface OrgStats {
  total_projects: number;
  active_projects: number;
  total_risks: number;
  open_risks: number;
  high_risk_projects: number;
  users_count: number;
}

export interface InviteRequest {
  email: string;
  name: string;
  role: UserRole;
}
