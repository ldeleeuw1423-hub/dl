import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import Cookies from "js-cookie";
import {
  AuthToken,
  Estimation,
  EstimationGenerateRequest,
  GISLayer,
  HistoricalProject,
  InviteRequest,
  Organization,
  OrganizationUpdate,
  OrgStats,
  PDOKAnalysisResult,
  Permit,
  PermitCreate,
  Project,
  ProjectCreate,
  ProjectListItem,
  Risk,
  RiskCreate,
  User,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${BASE_URL}${API_PREFIX}`,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      const token = Cookies.get("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          Cookies.remove("access_token");
          Cookies.remove("user");
          if (typeof window !== "undefined") {
            window.location.href = "/login";
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth
  async login(email: string, password: string): Promise<AuthToken> {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const { data } = await this.client.post<AuthToken>("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return data;
  }

  async register(payload: {
    email: string;
    password: string;
    name: string;
    role: string;
    organization?: string;
  }): Promise<User> {
    const { data } = await this.client.post<User>("/auth/register", payload);
    return data;
  }

  async getMe(): Promise<User> {
    const { data } = await this.client.get<User>("/auth/me");
    return data;
  }

  // Projects
  async getProjects(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    discipline?: string;
    phase?: string;
    search?: string;
  }): Promise<ProjectListItem[]> {
    const { data } = await this.client.get<ProjectListItem[]>("/projects", { params });
    return data;
  }

  async createProject(payload: ProjectCreate): Promise<Project> {
    const { data } = await this.client.post<Project>("/projects", payload);
    return data;
  }

  async getProject(id: string): Promise<Project> {
    const { data } = await this.client.get<Project>(`/projects/${id}`);
    return data;
  }

  async updateProject(id: string, payload: Partial<ProjectCreate>): Promise<Project> {
    const { data } = await this.client.put<Project>(`/projects/${id}`, payload);
    return data;
  }

  async deleteProject(id: string): Promise<void> {
    await this.client.delete(`/projects/${id}`);
  }

  // Estimations
  async getEstimations(projectId: string): Promise<Estimation[]> {
    const { data } = await this.client.get<Estimation[]>(`/projects/${projectId}/estimation`);
    return data;
  }

  async generateEstimation(
    projectId: string,
    payload: EstimationGenerateRequest
  ): Promise<Estimation> {
    const { data } = await this.client.post<Estimation>(
      `/projects/${projectId}/estimation/generate`,
      payload
    );
    return data;
  }

  // Risks
  async getRisks(projectId: string): Promise<Risk[]> {
    const { data } = await this.client.get<Risk[]>(`/projects/${projectId}/risks`);
    return data;
  }

  async createRisk(projectId: string, payload: RiskCreate): Promise<Risk> {
    const { data } = await this.client.post<Risk>(`/projects/${projectId}/risks`, payload);
    return data;
  }

  async updateRisk(projectId: string, riskId: string, payload: Partial<RiskCreate>): Promise<Risk> {
    const { data } = await this.client.put<Risk>(
      `/projects/${projectId}/risks/${riskId}`,
      payload
    );
    return data;
  }

  async deleteRisk(projectId: string, riskId: string): Promise<void> {
    await this.client.delete(`/projects/${projectId}/risks/${riskId}`);
  }

  async autoDetectRisks(projectId: string): Promise<Risk[]> {
    const { data } = await this.client.post<Risk[]>(
      `/projects/${projectId}/risks/auto-detect`
    );
    return data;
  }

  // Permits
  async getPermits(projectId: string): Promise<Permit[]> {
    const { data } = await this.client.get<Permit[]>(`/projects/${projectId}/permits`);
    return data;
  }

  async createPermit(projectId: string, payload: PermitCreate): Promise<Permit> {
    const { data } = await this.client.post<Permit>(`/projects/${projectId}/permits`, payload);
    return data;
  }

  async updatePermit(
    projectId: string,
    permitId: string,
    payload: Partial<PermitCreate>
  ): Promise<Permit> {
    const { data } = await this.client.put<Permit>(
      `/projects/${projectId}/permits/${permitId}`,
      payload
    );
    return data;
  }

  async deletePermit(projectId: string, permitId: string): Promise<void> {
    await this.client.delete(`/projects/${projectId}/permits/${permitId}`);
  }

  async autoDetectPermits(projectId: string): Promise<Permit[]> {
    const { data } = await this.client.post<Permit[]>(
      `/projects/${projectId}/permits/auto-detect`
    );
    return data;
  }

  // GIS
  async getGISLayers(): Promise<{ layers: GISLayer[] }> {
    const { data } = await this.client.get<{ layers: GISLayer[] }>("/gis/layers");
    return data;
  }

  async analyzeGeometry(geometry: object): Promise<object> {
    const { data } = await this.client.post("/gis/analyze", { geometry });
    return data;
  }

  async analyzeGeometryPDOK(geometry: object): Promise<PDOKAnalysisResult> {
    const { data } = await this.client.post<PDOKAnalysisResult>("/gis/analyze-pdok", { geometry });
    return data;
  }

  // Historical
  async getHistoricalProjects(params?: {
    discipline?: string;
    location_type?: string;
    limit?: number;
  }): Promise<HistoricalProject[]> {
    const { data } = await this.client.get<HistoricalProject[]>("/historical", { params });
    return data;
  }

  async getSimilarProjects(params: {
    project_id?: string;
    discipline?: string;
    location_type?: string;
    trace_length_m?: number;
    top_k?: number;
  }): Promise<HistoricalProject[]> {
    const { data } = await this.client.get<HistoricalProject[]>("/historical/similar", { params });
    return data;
  }

  // Export
  getExportExcelUrl(projectId: string): string {
    return `${BASE_URL}${API_PREFIX}/projects/${projectId}/export/excel`;
  }

  getExportPdfUrl(projectId: string): string {
    return `${BASE_URL}${API_PREFIX}/projects/${projectId}/export/pdf`;
  }

  async downloadExcel(projectId: string): Promise<Blob> {
    const token = Cookies.get("access_token");
    const { data } = await this.client.get(`/projects/${projectId}/export/excel`, {
      responseType: "blob",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return data;
  }

  async downloadPdf(projectId: string): Promise<Blob> {
    const token = Cookies.get("access_token");
    const { data } = await this.client.get(`/projects/${projectId}/export/pdf`, {
      responseType: "blob",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return data;
  }

  // Organizations
  async getMyOrganization(): Promise<Organization> {
    const { data } = await this.client.get<Organization>("/organizations/me");
    return data;
  }

  async updateMyOrganization(payload: OrganizationUpdate): Promise<Organization> {
    const { data } = await this.client.put<Organization>("/organizations/me", payload);
    return data;
  }

  async getOrgUsers(): Promise<User[]> {
    const { data } = await this.client.get<User[]>("/organizations/me/users");
    return data;
  }

  async inviteUser(payload: InviteRequest): Promise<User> {
    const { data } = await this.client.post<User>("/organizations/invite", payload);
    return data;
  }

  async getOrgStats(): Promise<OrgStats> {
    const { data } = await this.client.get<OrgStats>("/organizations/me/stats");
    return data;
  }

  // File upload
  async uploadFile(projectId: string, file: File): Promise<{ filename: string; saved_path: string }> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await this.client.post(
      `/projects/${projectId}/files/upload`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return data;
  }

  async getProjectFiles(projectId: string): Promise<{ files: Array<{ filename: string; size_bytes: number; url: string }> }> {
    const { data } = await this.client.get(`/projects/${projectId}/files`);
    return data;
  }
}

export const api = new APIClient();

export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg: string }) => d.msg).join(", ");
    }
  }
  if (error instanceof Error) return error.message;
  return "Er is een onbekende fout opgetreden";
}
