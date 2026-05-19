import { projects as fallbackProjects, records as fallbackRecords } from "./data";

const API_BASE = import.meta.env.VITE_CMF_API_URL ?? "http://localhost:8001/api";

export type ApiProject = {
  id: number;
  code: string;
  name: string;
  project: string;
  part_of_project: string;
  capacity_manager_name: string;
  buyer_assigned_name: string | null;
  sqd_assigned_name: string | null;
  supplier_name: string | null;
  cmf_status: string;
  records_count: number;
  completion: number;
  updated_at: string;
};

export type ApiRecord = {
  id: number;
  project_id: number;
  apqp_grid: string;
  part_number: string;
  values: Record<string, unknown>;
  flat: Record<string, unknown>;
};

export type ApiFullData = {
  columns: string[];
  default_visible: string[];
  records: Array<Record<string, unknown>>;
};

export type ApiCrossProject = {
  projects: string[];
  records: Array<Record<string, unknown>>;
};

export type ParsedImportFile = {
  columns: string[];
  rows: Array<Record<string, string>>;
  total_rows: number;
};

export type ApiProjectColumn = {
  id: number | null;
  project_id: number;
  column_name: string;
  owner_role: string;
  is_auto: number;
  display_order: number;
  section: string;
  roles: string[];
};

export type ApiUser = {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  created_at: string | null;
};

export type ApiAuditLog = {
  id: number;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  user_name: string | null;
  old_value: string | null;
  new_value: string | null;
  timestamp: string;
  project_id: number | null;
};

export async function loginUser(payload: { email: string; password: string }): Promise<ApiUser> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { user: ApiUser };
  return data.user;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchProjects(): Promise<ApiProject[]> {
  const data = await getJson<{ projects: ApiProject[] }>("/projects");
  return data.projects;
}

export async function fetchRecords(projectId: number): Promise<ApiRecord[]> {
  const data = await getJson<{ records: ApiRecord[] }>(`/projects/${projectId}/records`);
  return data.records;
}

export async function fetchSchema(): Promise<string[]> {
  const data = await getJson<{ columns: Array<{ name: string }> }>("/schema");
  return data.columns.map((column) => column.name);
}

export async function fetchProjectColumns(projectId: number): Promise<ApiProjectColumn[]> {
  const data = await getJson<{ columns: ApiProjectColumn[] }>(`/projects/${projectId}/columns`);
  return data.columns;
}

export async function fetchProjectFullData(projectId: number): Promise<ApiFullData> {
  return getJson<ApiFullData>(`/projects/${projectId}/full-data`);
}

export async function fetchCrossProject(): Promise<ApiCrossProject> {
  return getJson<ApiCrossProject>("/cross-project");
}

export async function downloadProjectCmfExport(projectId: number): Promise<Blob> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/cmf-export`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  return response.blob();
}

export async function parseImportFile(payload: { filename: string; content_base64: string }): Promise<ParsedImportFile> {
  const response = await fetch(`${API_BASE}/import/parse-file`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<ParsedImportFile>;
}

export async function fetchEditableColumns(projectId: number, role: string, section?: string): Promise<string[]> {
  const params = new URLSearchParams({ role });
  if (section) params.set("section", section);
  const data = await getJson<{ columns: Array<{ name: string }> }>(`/projects/${projectId}/editable-columns?${params.toString()}`);
  return data.columns.map((column) => column.name);
}

export async function createProject(payload: {
  project: string;
  part_of_project: string;
  capacity_manager_name: string;
  buyer_assigned_name?: string;
  sqd_assigned_name?: string;
  cmf_status?: string;
  created_by?: string;
  custom_columns?: Array<{ column_name: string; owner_role: string }>;
}): Promise<ApiProject> {
  const response = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { project: ApiProject };
  return data.project;
}

export async function addCustomColumn(projectId: number, payload: { column_name: string; owner_role: string; actor_email?: string }): Promise<ApiProjectColumn> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/custom-columns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { column: ApiProjectColumn };
  return data.column;
}

export async function updateProject(projectId: number, payload: {
  name?: string;
  capacity_manager_name?: string;
  buyer_assigned_name?: string;
  sqd_assigned_name?: string;
  supplier_name?: string;
  cmf_status?: string;
  description?: string;
  actor_email?: string;
}): Promise<ApiProject> {
  const response = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { project: ApiProject };
  return data.project;
}

export async function deleteProject(projectId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/projects/${projectId}`, { method: "DELETE" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
}

export async function upsertRecord(projectId: number, payload: {
  part_number: string;
  apqp_grid?: string;
  values: Record<string, unknown>;
  updated_by?: string;
  actor_email?: string;
}): Promise<ApiRecord> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/records`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { record: ApiRecord };
  return data.record;
}

export async function fetchAuditLogs(): Promise<ApiAuditLog[]> {
  const data = await getJson<{ logs: ApiAuditLog[] }>("/admin/audit-logs");
  return data.logs;
}

export async function adminUpsertRecord(projectId: number, payload: {
  part_number: string;
  apqp_grid?: string;
  values: Record<string, unknown>;
  updated_by?: string;
}): Promise<ApiRecord> {
  const response = await fetch(`${API_BASE}/admin/projects/${projectId}/records`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { record: ApiRecord };
  return data.record;
}

export async function adminUpdateRecord(recordId: number, payload: {
  part_number: string;
  apqp_grid?: string;
  values: Record<string, unknown>;
  updated_by?: string;
}): Promise<ApiRecord> {
  const response = await fetch(`${API_BASE}/admin/records/${recordId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { record: ApiRecord };
  return data.record;
}

export async function adminDeleteRecord(recordId: number, updatedBy: string): Promise<void> {
  const response = await fetch(`${API_BASE}/admin/records/${recordId}?updated_by=${encodeURIComponent(updatedBy)}`, { method: "DELETE" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
}

export async function adminResetProjectRecords(projectId: number, updatedBy: string): Promise<number> {
  const response = await fetch(`${API_BASE}/admin/projects/${projectId}/records?updated_by=${encodeURIComponent(updatedBy)}`, { method: "DELETE" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { deleted_records: number };
  return data.deleted_records;
}

export async function saveRoleRecord(projectId: number, payload: {
  part_number: string;
  apqp_grid?: string;
  values: Record<string, unknown>;
  role: string;
  section?: string;
  updated_by?: string;
  actor_email?: string;
  create_if_missing?: boolean;
}): Promise<ApiRecord> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/role-record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { record: ApiRecord };
  return data.record;
}

export async function fetchUsers(): Promise<ApiUser[]> {
  const data = await getJson<{ users: ApiUser[] }>("/users");
  return data.users;
}

export async function createUser(payload: {
  email: string;
  full_name?: string;
  role: string;
  password: string;
}): Promise<ApiUser> {
  const response = await fetch(`${API_BASE}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { user: ApiUser };
  return data.user;
}

export async function updateUserRole(userId: number, role: string): Promise<ApiUser> {
  const response = await fetch(`${API_BASE}/users/${userId}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { user: ApiUser };
  return data.user;
}

export async function updateUserPassword(userId: number, password: string): Promise<ApiUser> {
  const response = await fetch(`${API_BASE}/users/${userId}/password`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
  const data = (await response.json()) as { user: ApiUser };
  return data.user;
}

export async function deleteUser(userId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/users/${userId}`, { method: "DELETE" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `${response.status} ${response.statusText}`);
  }
}

export const fallback = {
  projects: fallbackProjects,
  records: fallbackRecords,
};
