import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  ArrowRight,
  Check,
  ChevronDown,
  Database,
  Download,
  FileUp,
  Filter,
  Gauge,
  LayoutDashboard,
  PackagePlus,
  Plus,
  Settings,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Users,
} from "lucide-react";
import {
  addCustomColumn,
  adminDeleteRecord,
  adminResetProjectRecords,
  adminUpdateRecord,
  adminUpsertRecord,
  createActionPlan,
  createProject,
  createUser,
  deleteProjectRecord,
  deleteProject,
  deleteUser,
  downloadProjectCmfExport,
  fetchActionPlans,
  fetchProjectDashboard,
  fetchEditableColumns,
  fetchCrossProject,
  fetchProjectFullData,
  fetchProjectColumns,
  fetchAuditLogs,
  fetchProjects,
  fetchRecords,
  fetchSchema,
  fetchUsers,
  fallback,
  loginUser,
  parseImportFile,
  saveRoleRecord,
  upsertRecord,
  updateProjectRecord,
  updateProject,
  updateUserRole,
  updateUserPassword,
  type ApiProject,
  type ApiDashboard,
  type ApiDashboardFilters,
  type ApiRecord,
  type ApiCrossProject,
  type ApiProjectColumn,
  type ApiAuditLog,
  type ApiActionPlan,
  type ApiUser,
  type ParsedImportFile,
} from "./api";
import { cmfColumns, fileColumns, projects, records, sections, type Health } from "./data";

type AppRole = "Buyer" | "Capacity Manager" | "SQD" | "Admin";
type ViewId =
  | "command"
  | "cmf-dashboard"
  | "buyer-part-data"
  | "weekly-capacity"
  | "cross-project"
  | "manage-projects"
  | "create-project"
  | "capacity-sizing"
  | "capacity-workshop"
  | "sqd-part-data"
  | "supplier-information"
  | "cat"
  | "admin-users"
  | "data-manager";

const roleNavigation: Record<AppRole, Array<{ id: ViewId; label: string; icon: typeof LayoutDashboard }>> = {
  Buyer: [
    { id: "cmf-dashboard", label: "CMF Dashboard", icon: Gauge },
    { id: "command", label: "CMF Data", icon: LayoutDashboard },
    { id: "buyer-part-data", label: "Part Data", icon: PackagePlus },
    { id: "weekly-capacity", label: "Weekly Contracted Capacity", icon: Gauge },
    { id: "cross-project", label: "VEHICULES ROAD MAP", icon: ArrowRight },
  ],
  "Capacity Manager": [
    { id: "cmf-dashboard", label: "CMF Dashboard", icon: Gauge },
    { id: "command", label: "CMF Data", icon: LayoutDashboard },
    { id: "manage-projects", label: "Manage Projects", icon: Settings },
    { id: "create-project", label: "Create Project", icon: Plus },
    { id: "capacity-sizing", label: "CAPACITY SIZING", icon: Gauge },
    { id: "capacity-workshop", label: "CAPACITY WORKSHOP", icon: FileUp },
    { id: "cross-project", label: "VEHICULES ROAD MAP", icon: ArrowRight },
  ],
  SQD: [
    { id: "cmf-dashboard", label: "CMF Dashboard", icon: Gauge },
    { id: "command", label: "CMF Data", icon: LayoutDashboard },
    { id: "sqd-part-data", label: "PART DATA", icon: PackagePlus },
    { id: "supplier-information", label: "SUPPLIER INFORMATION", icon: Users },
    { id: "capacity-workshop", label: "CAPACITY WORKSHOP", icon: FileUp },
    { id: "cat", label: "CAT", icon: ShieldCheck },
    { id: "cross-project", label: "VEHICULES ROAD MAP", icon: ArrowRight },
  ],
  Admin: [
    { id: "cmf-dashboard", label: "CMF Dashboard", icon: Gauge },
    { id: "command", label: "CMF Data", icon: LayoutDashboard },
    { id: "manage-projects", label: "Manage Projects", icon: Settings },
    { id: "create-project", label: "Create Project", icon: Plus },
    { id: "buyer-part-data", label: "Buyer Page", icon: PackagePlus },
    { id: "capacity-sizing", label: "Capacity Page", icon: Gauge },
    { id: "sqd-part-data", label: "SQD Page", icon: ShieldCheck },
    { id: "cross-project", label: "VEHICULES ROAD MAP", icon: ArrowRight },
    { id: "admin-users", label: "Admin Users", icon: Users },
    { id: "data-manager", label: "Data Manager", icon: Database },
  ],
};

type UIProject = {
  id: string;
  apiId?: number;
  project: string;
  partOfProject: string;
  capacityManager: string;
  supplier: string;
  buyer: string;
  sqd: string;
  status: string;
  records: number;
  completion: number;
  capacityHealth: Health;
  catHealth: Health;
  updated: string;
};

type UIRecord = {
  id?: number;
  part: string;
  apqp: string;
  supplier: string;
  useCase: string;
  contracted: number;
  requested: number;
  measured: number;
  catType: string;
  cat: Health | "";
  gor: Health | "";
  owner: string;
};

type CustomColumnDraft = {
  name: string;
  ownerRole: string;
  section: string;
};

const customColumnRoles = ["BUYER", "SQD", "CAPACITY_MANAGER", "ADMIN"];
const customColumnSectionsByRole: Record<string, string[]> = {
  BUYER: ["PART DATA", "WEEKLY CONTRACTED CAPACITY", "CAPACITY SIZING"],
  CAPACITY_MANAGER: ["CAPACITY SIZING", "CAPACITY WORKSHOP (STEP 2)"],
  SQD: ["PART DATA", "SUPPLIER INFORMATION", "CAPACITY WORKSHOP (STEP 2)", "CAT"],
  ADMIN: ["PART DATA", "WEEKLY CONTRACTED CAPACITY", "CAPACITY SIZING", "CAPACITY WORKSHOP (STEP 2)", "SUPPLIER INFORMATION", "CAT"],
};

function defaultCustomSection(role: string): string {
  return customColumnSectionsByRole[role]?.[0] ?? "PART DATA";
}

function apiRoleToAppRole(role: string): AppRole {
  const normalized = role.trim().toUpperCase();
  if (normalized === "BUYER") return "Buyer";
  if (normalized === "SQD") return "SQD";
  if (normalized === "ADMIN" || normalized === "SUPER_ADMIN") return "Admin";
  return "Capacity Manager";
}

const healthMeta: Record<Health, { label: string; className: string }> = {
  G: { label: "Green", className: "green" },
  O: { label: "Orange", className: "orange" },
  R: { label: "Red", className: "red" },
};

function text(value: unknown, fallbackValue = ""): string {
  if (value === null || value === undefined) return fallbackValue;
  return String(value);
}

function number(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function health(value: unknown): Health {
  const normalized = text(value).trim().toUpperCase();
  return normalized === "R" || normalized === "O" || normalized === "G" ? normalized : "O";
}

function healthOrBlank(value: unknown): Health | "" {
  const normalized = text(value).trim().toUpperCase();
  return normalized === "R" || normalized === "O" || normalized === "G" ? normalized : "";
}

function normalizeColumnName(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function guessMappedColumn(cmfColumn: string, fileColumns: string[]): string {
  const normalizedCmf = normalizeColumnName(cmfColumn);
  const aliases: Record<string, string[]> = {
    partnumber: ["partnumber", "pn", "partno", "reference"],
    apqpgrid: ["apqpgrid", "apqp", "apqpcode"],
  };
  const candidates = aliases[normalizedCmf] ?? [normalizedCmf];
  return fileColumns.find((column) => candidates.includes(normalizeColumnName(column))) ?? "";
}

async function fileToBase64(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  return btoa(binary);
}

function partRisk(record: UIRecord): Health | "" {
  if (record.cat === "R" || record.gor === "R") return "R";
  if (record.cat === "O" || record.gor === "O") return "O";
  if (record.cat === "G" && record.gor === "G") return "G";
  return "";
}

function riskRank(record: UIRecord): number {
  const risk = partRisk(record);
  if (risk === "R") return 0;
  if (risk === "O") return 1;
  if (risk === "G") return 2;
  return 3;
}

function hasCapacityForGor(flat: Record<string, unknown>): boolean {
  return number(flat["WEEKLY CAPACITY CONTRACTED (Parts/Week)"]) > 0 && number(flat["LAST WEEKLY CAPACITY REQUESTED"]) > 0;
}

function hasCapacityForCat(flat: Record<string, unknown>): boolean {
  return hasCapacityForGor(flat) && number(flat["WEEKLY CAPACITY MEASURED"]) > 0;
}

function isAssignedToUser(user: ApiUser, assignedName?: string | null): boolean {
  const assigned = text(assignedName).trim().toLowerCase();
  if (!assigned || assigned.startsWith("unassigned")) return false;
  const email = user.email.trim().toLowerCase();
  const fullName = text(user.full_name).trim().toLowerCase();
  return assigned === email || assigned === fullName || assigned.includes(email) || (!!fullName && assigned.includes(fullName));
}

function canEditProject(user: ApiUser, role: AppRole, project: UIProject): boolean {
  if (role === "Admin") return true;
  if (role === "Buyer") return isAssignedToUser(user, project.buyer);
  if (role === "SQD") return isAssignedToUser(user, project.sqd);
  return isAssignedToUser(user, project.capacityManager);
}

function readinessPercent(records: UIRecord[], isFilled: (record: UIRecord) => boolean): number {
  if (!records.length) return 0;
  return Math.round((records.filter(isFilled).length / records.length) * 100);
}

async function copyCellValue(value: unknown): Promise<void> {
  const textValue = String(value ?? "");
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(textValue);
    return;
  }
  const input = document.createElement("textarea");
  input.value = textValue;
  input.style.position = "fixed";
  input.style.opacity = "0";
  document.body.appendChild(input);
  input.select();
  document.execCommand("copy");
  document.body.removeChild(input);
}

function mapApiProject(project: ApiProject): UIProject {
  return {
    id: String(project.id),
    apiId: project.id,
    project: project.project,
    partOfProject: project.part_of_project,
    capacityManager: project.capacity_manager_name || "Unassigned capacity manager",
    supplier: project.supplier_name || "Multiple suppliers",
    buyer: project.buyer_assigned_name || "Unassigned buyer",
    sqd: project.sqd_assigned_name || "Unassigned SQD",
    status: project.cmf_status || "ACTIVE",
    records: project.records_count,
    completion: project.completion,
    capacityHealth: project.completion > 75 ? "G" : project.completion > 45 ? "O" : "R",
    catHealth: project.completion > 70 ? "G" : "O",
    updated: project.updated_at ? new Date(project.updated_at).toLocaleDateString() : "N/A",
  };
}

function mapApiRecord(record: ApiRecord): UIRecord {
  const flat = record.flat;
  return {
    id: record.id,
    part: record.part_number,
    apqp: record.apqp_grid || text(flat["APQP GRID"], "N/A"),
    supplier: text(flat["SUPPLIER NAME"], "N/A"),
    useCase: text(flat["USE CASES"], "N/A"),
    contracted: number(flat["WEEKLY CAPACITY CONTRACTED (Parts/Week)"]),
    requested: number(flat["LAST WEEKLY CAPACITY REQUESTED"]),
    measured: number(flat["WEEKLY CAPACITY MEASURED"]),
    catType: text(flat["CAT1/2/3 TYPE"], "N/A"),
    cat: hasCapacityForCat(flat) ? healthOrBlank(flat["CAT1/2/3 VALUATION (G;O;R)"]) : "",
    gor: hasCapacityForGor(flat) ? healthOrBlank(flat["GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer"]) : "",
    owner: text(flat.updated_by, "CMF"),
  };
}

function App() {
  const [currentUser, setCurrentUser] = useState<ApiUser | null>(() => {
    const stored = localStorage.getItem("cmf_user");
    return stored ? JSON.parse(stored) as ApiUser : null;
  });
  const role = currentUser ? apiRoleToAppRole(currentUser.role) : "Buyer";
  const [activeView, setActiveView] = useState<ViewId>("cmf-dashboard");
  const [projectList, setProjectList] = useState<UIProject[]>(projects);
  const [recordList, setRecordList] = useState<UIRecord[]>(records);
  const [selectedProject, setSelectedProject] = useState(projects[0].id);
  const [apiStatus, setApiStatus] = useState<"live" | "fallback" | "loading">("loading");
  const project = useMemo(() => projectList.find((item) => item.id === selectedProject) ?? projectList[0], [projectList, selectedProject]);
  const currentCanEdit = currentUser && project ? canEditProject(currentUser, role, project) : false;
  const navItems = roleNavigation[role];

  function handleLogin(user: ApiUser) {
    localStorage.setItem("cmf_user", JSON.stringify(user));
    setCurrentUser(user);
  }

  function handleLogout() {
    localStorage.removeItem("cmf_user");
    setCurrentUser(null);
    setActiveView("cmf-dashboard");
  }

  useEffect(() => {
    setActiveView(roleNavigation[role][0].id);
  }, [role]);

  if (!currentUser) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  useEffect(() => {
    fetchProjects()
      .then((apiProjects) => {
        const mapped = apiProjects.map(mapApiProject);
        if (mapped.length) {
          setProjectList(mapped);
          setSelectedProject(mapped[0].id);
          setApiStatus("live");
        }
      })
      .catch(() => {
        setProjectList(fallback.projects);
        setRecordList(fallback.records);
        setApiStatus("fallback");
      });
  }, []);

  useEffect(() => {
    if (!project?.apiId) {
      return;
    }
    fetchRecords(project.apiId)
      .then((apiRecords) => setRecordList(apiRecords.map(mapApiRecord)))
      .catch(() => setRecordList(fallback.records));
  }, [project?.apiId]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">C</div>
          <div>
            <strong>CMF Command</strong>
            <span>Capacity orchestration</span>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                className={`nav-item ${activeView === item.id ? "active" : ""}`}
                key={item.id}
                onClick={() => setActiveView(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-panel">
          <div className="mini-eyebrow">Live workspace</div>
          <strong>{project.project}</strong>
          <span>{project.partOfProject}</span>
          <div className="progress">
            <span style={{ width: `${project.completion}%` }} />
          </div>
        </div>
      </aside>

      <main className="main">
        <Topbar
          apiStatus={apiStatus}
          role={role}
          user={currentUser}
          onLogout={handleLogout}
          projects={projectList}
          selectedProject={selectedProject}
          setSelectedProject={setSelectedProject}
        />
        {activeView === "command" && (
          <Dashboard
            project={project}
            records={recordList}
            role={role}
            user={currentUser}
            canEdit={Boolean(currentCanEdit)}
            onRecordsChanged={setRecordList}
          />
        )}
        {activeView === "cmf-dashboard" && (
          <CmfDashboard project={project} />
        )}
        {activeView === "manage-projects" && (
          <Projects
            projects={projectList}
            mode="manage"
            user={currentUser}
            role={role}
            onProjectUpdated={(updatedProject) => {
              setProjectList((current) => current.map((item) => (item.id === updatedProject.id ? updatedProject : item)));
              setSelectedProject(updatedProject.id);
            }}
            onProjectCreated={(createdProject) => {
              setProjectList((current) => [createdProject, ...current]);
              setSelectedProject(createdProject.id);
              setApiStatus("live");
            }}
          />
        )}
        {activeView === "create-project" && (
          <Projects
            projects={projectList}
            mode="create"
            user={currentUser}
            role={role}
            onProjectUpdated={(updatedProject) => {
              setProjectList((current) => current.map((item) => (item.id === updatedProject.id ? updatedProject : item)));
            }}
            onProjectCreated={(createdProject) => {
              setProjectList((current) => [createdProject, ...current]);
              setSelectedProject(createdProject.id);
              setApiStatus("live");
            }}
          />
        )}
        {activeView === "buyer-part-data" && <BuyerWorkspace project={project} records={recordList} onSaved={setRecordList} section="PART DATA" canEdit={currentCanEdit} user={currentUser} />}
        {activeView === "weekly-capacity" && <BuyerWorkspace project={project} records={recordList} onSaved={setRecordList} section="WEEKLY CONTRACTED CAPACITY" canEdit={currentCanEdit} user={currentUser} />}
        {activeView === "cross-project" && <CrossProjectView projects={projectList} />}
        {activeView === "capacity-sizing" && <CapacityWorkspace project={project} records={recordList} onSaved={setRecordList} section="CAPACITY SIZING" canEdit={currentCanEdit} user={currentUser} />}
        {activeView === "capacity-workshop" && (
          role === "SQD"
            ? <SqdCapacityWorkshop project={project} records={recordList} onSaved={setRecordList} canEdit={currentCanEdit} user={currentUser} />
            : <CapacityWorkspace project={project} records={recordList} onSaved={setRecordList} section="CAPACITY WORKSHOP (STEP 2)" canEdit={currentCanEdit} user={currentUser} />
        )}
        {activeView === "sqd-part-data" && <SqdWorkspace project={project} records={recordList} onSaved={setRecordList} section="PART DATA" canEdit={currentCanEdit} user={currentUser} />}
        {activeView === "supplier-information" && <SqdWorkspace project={project} records={recordList} onSaved={setRecordList} section="SUPPLIER INFORMATION" canEdit={currentCanEdit} user={currentUser} />}
        {activeView === "cat" && <CatWorkspace project={project} records={recordList} onSaved={setRecordList} canEdit={currentCanEdit} user={currentUser} />}
        {activeView === "admin-users" && <AdminUsers />}
        {activeView === "data-manager" && (
          <DataManager
            project={project}
            records={recordList}
            user={currentUser}
            onSaved={setRecordList}
            onProjectDeleted={(deletedId) => {
              setProjectList((current) => {
                const next = current.filter((item) => item.id !== deletedId);
                if (next.length) setSelectedProject(next[0].id);
                return next;
              });
              setRecordList([]);
            }}
          />
        )}
      </main>
    </div>
  );
}

function Topbar({
  apiStatus,
  role,
  user,
  onLogout,
  projects,
  selectedProject,
  setSelectedProject,
}: {
  apiStatus: "live" | "fallback" | "loading";
  role: AppRole;
  user: ApiUser;
  onLogout: () => void;
  projects: UIProject[];
  selectedProject: string;
  setSelectedProject: (value: string) => void;
}) {
  const activeProject = projects.find((project) => project.id === selectedProject);

  return (
    <header className="topbar">
      <div className="topbar-context">
        <span className="mini-eyebrow">Current workspace</span>
        <strong>{activeProject ? `${activeProject.project} / ${activeProject.partOfProject}` : "Select project"}</strong>
      </div>
      <div className="topbar-actions">
        <span className="user-chip">{user.email} · {role}</span>
        <select value={selectedProject} onChange={(event) => setSelectedProject(event.target.value)}>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.project} / {project.partOfProject}
            </option>
          ))}
        </select>
        <span className={`api-badge ${apiStatus}`}>{apiStatus === "live" ? "API live" : apiStatus === "loading" ? "Connecting" : "Demo data"}</span>
        <button className="secondary-button" onClick={onLogout}>Logout</button>
        <div className="avatar">{(user.full_name || user.email).slice(0, 2).toUpperCase()}</div>
      </div>
    </header>
  );
}

function LoginScreen({ onLogin }: { onLogin: (user: ApiUser) => void }) {
  const [email, setEmail] = useState("admin@cmf.local");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const user = await loginUser({ email, password });
      onLogin(user);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-shell">
      <form className="login-panel" onSubmit={submit}>
        <div className="brand login-brand">
          <div className="brand-mark">C</div>
          <div>
            <strong>CMF Command</strong>
            <span>Secure access</span>
          </div>
        </div>
        <label className="field">
          <span>Email</span>
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="user@company.com" />
        </label>
        <label className="field">
          <span>Password</span>
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Password" />
        </label>
        {error && <div className="form-error">{error}</div>}
        <button className="primary-button full" disabled={loading}>{loading ? "Signing in..." : "Login"}</button>
        <p className="login-hint">Default admin: admin@cmf.local / admin123</p>
      </form>
    </main>
  );
}

function Dashboard({
  project,
  records,
  role,
  user,
  canEdit,
  onRecordsChanged,
}: {
  project: UIProject;
  records: UIRecord[];
  role: AppRole;
  user: ApiUser;
  canEdit: boolean;
  onRecordsChanged: (records: UIRecord[]) => void;
}) {
  const redParts = records.filter((record) => partRisk(record) === "R").length;
  const orangeParts = records.filter((record) => partRisk(record) === "O").length;
  const greenParts = records.filter((record) => partRisk(record) === "G").length;
  const catEvalConfirmed = records.filter((record) => record.cat === "G").length;
  const catEvalOngoing = records.filter((record) => record.cat === "O").length;
  const catEvalCritical = records.filter((record) => record.cat === "R").length;
  const readiness = [
    { label: "Part number", value: readinessPercent(records, (record) => Boolean(record.part.trim())), icon: PackagePlus },
    { label: "Requested Capacity", value: readinessPercent(records, (record) => record.requested > 0), icon: Gauge },
    { label: "Contracted", value: readinessPercent(records, (record) => record.contracted > 0), icon: Database },
    { label: "Measured", value: readinessPercent(records, (record) => record.measured > 0), icon: ShieldCheck },
  ];

  return (
    <section className="page-grid">
      <div className="page-title">
        <div>
          <span className="eyebrow">{role} CMF data</span>
          <h1>CMF Data</h1>
          <p>{project.project} / {project.partOfProject} workspace with readiness metrics and the complete project CMF table.</p>
        </div>
      </div>

      <div className="metrics-grid">
        <Metric label="Number of Parts" value={String(records.length)} detail="All part numbers" />
        <Metric label="Number of Red Parts" value={String(redParts)} detail="CAT/GOR hierarchy" tone="R" />
        <Metric label="Number of Orange Parts" value={String(orangeParts)} detail="CAT/GOR hierarchy" tone="O" />
        <Metric label="Number of Green Parts" value={String(greenParts)} detail="CAT and GOR green" tone="G" />
        <Metric label="CAT Eval Green" value={String(catEvalConfirmed)} detail="CAT valuation Confirmed" tone="G" />
        <Metric label="CAT Eval Orange" value={String(catEvalOngoing)} detail="CAT valuation Ongoing" tone="O" />
        <Metric label="CAT Eval Red" value={String(catEvalCritical)} detail="CAT valuation Critical" tone="R" />
      </div>

      <div className="panel wide">
        <PanelHeader title="Workstream Readiness" action={`${records.length} parts`} />
        <div className="readiness-list">
          {readiness.map((section) => {
            const Icon = section.icon;
            return (
              <div className="readiness-row" key={section.label}>
                <div className="row-title">
                  <Icon size={18} />
                  <span>{section.label}</span>
                </div>
                <div className="row-meter">
                  <span style={{ width: `${section.value}%` }} />
                </div>
                <strong>{section.value}%</strong>
              </div>
            );
          })}
        </div>
      </div>

      <FullCmfGrid
        project={project}
        fallbackRecords={records}
        title="CMF Data"
        embedded
        canEdit={canEdit}
        role={role}
        user={user}
        onRecordsChanged={onRecordsChanged}
      />
    </section>
  );
}

const dashboardFilterLabels: Record<string, string> = {
  supplier: "Supplier Name",
  part_number: "Part Number",
  country: "Country",
  location: "Location",
  buyer: "Buyer",
  sqe: "SQE",
  gor: "GOR",
  apqp: "APQP Grid Project",
  use_cases: "Use Cases",
  year: "Year of Max Need",
  cat_status: "CAT Status",
  cat_evaluation_status: "CAT Evaluation",
  capacity_source: "Capacity Source",
};

function CmfDashboard({ project }: { project: UIProject }) {
  const [dashboard, setDashboard] = useState<ApiDashboard | null>(null);
  const [filters, setFilters] = useState<ApiDashboardFilters>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!project?.apiId) {
      setDashboard(null);
      setError("Dashboard data requires a SQLite project.");
      return;
    }
    setLoading(true);
    setError("");
    fetchProjectDashboard(project.apiId, filters)
      .then(setDashboard)
      .catch((event) => setError(event instanceof Error ? event.message : "Unable to load dashboard"))
      .finally(() => setLoading(false));
  }, [project?.apiId, filters]);

  const summary = dashboard?.summary;
  const resetFilters = () => setFilters({});

  return (
    <section className="page-grid cmf-dashboard">
      <div className="page-title">
        <div>
          <span className="eyebrow">Capacity performance</span>
          <h1>CMF Dashboard</h1>
          <p>{project.project} / {project.partOfProject} risk, capacity coverage, CAT progress, data quality, and priority actions.</p>
        </div>
        <button className="secondary-button" onClick={resetFilters} disabled={!Object.values(filters).some(Boolean)}>
          Reset filters
        </button>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="dashboard-filters panel">
        {Object.entries(dashboardFilterLabels).map(([key, label]) => (
          <label className="dashboard-filter" key={key}>
            <span>{label}</span>
            <select
              value={filters[key] ?? ""}
              onChange={(event) => setFilters((current) => ({ ...current, [key]: event.target.value }))}
              disabled={!dashboard}
            >
              <option value="">All</option>
              {(dashboard?.filters[key] ?? []).map((option) => (
                <option value={option} key={option}>{option}</option>
              ))}
            </select>
          </label>
        ))}
      </div>

      <div className="metrics-grid dashboard-kpis">
        <Metric label="Total CMF Lines" value={loading ? "..." : formatInteger(summary?.total_lines)} detail="Filtered records" />
        <Metric label="Suppliers" value={loading ? "..." : formatInteger(summary?.suppliers_count)} detail="Distinct supplier names" />
        <Metric label="Coverage Rate" value={formatPercentValue(summary?.coverage_rate)} detail="Contracted / requested" tone={coverageTone(summary?.coverage_rate)} />
        <Metric label="Red Lines" value={formatInteger(summary?.red_lines)} detail="Critical GOR status" tone="R" />
        <Metric label="CAT Late" value={formatInteger(summary?.late_cats)} detail="Forecast passed, not realised" tone={summary?.late_cats ? "O" : "G"} />
        <Metric label="Missing Capacity" value={formatCapacity(summary?.missing_capacity)} detail="Negative gaps only" tone={summary?.missing_capacity ? "R" : "G"} />
        <Metric label="Requested Capacity" value={formatCapacity(summary?.total_requested_capacity)} detail="Total weekly requested" />
        <Metric label="Contracted Capacity" value={formatCapacity(summary?.total_contracted_capacity)} detail="Total weekly contracted" />
        <Metric label="Measured Capacity" value={formatCapacity(summary?.total_measured_capacity)} detail="Total weekly measured" />
        <Metric label="Measured Coverage" value={formatPercentValue(summary?.measured_coverage_rate)} detail="Measured / requested" tone={coverageTone(summary?.measured_coverage_rate)} />
        <Metric label="Measured Missing" value={formatCapacity(summary?.missing_measured_capacity)} detail="Measured negative gaps" tone={summary?.missing_measured_capacity ? "R" : "G"} />
        <Metric label="Measured Insufficient" value={formatInteger(summary?.measured_insufficient_lines)} detail="Measured gap below zero" tone={summary?.measured_insufficient_lines ? "R" : "G"} />
        <Metric label="CAT Eval Green" value={formatInteger(summary?.cat_evaluation_green)} detail="CAT valuation Confirmed" tone="G" />
        <Metric label="CAT Eval Orange" value={formatInteger(summary?.cat_evaluation_orange)} detail="CAT valuation Ongoing" tone="O" />
        <Metric label="CAT Eval Red" value={formatInteger(summary?.cat_evaluation_red)} detail="CAT valuation Critical" tone="R" />
        <Metric label="CAT Eval Red Rate" value={formatPercentValue(summary?.cat_evaluation_red_rate)} detail="Red / known CAT eval" tone={riskRateTone(summary?.cat_evaluation_red_rate)} />
      </div>

      {dashboard && (
        <>
          <div className="dashboard-row two">
            <DonutPanel title="G/O/R Distribution" data={dashboard.gor_distribution} />
            <CapacityComparison requested={dashboard.capacity_comparison.requested} contracted={dashboard.capacity_comparison.contracted} />
          </div>

          <div className="dashboard-row two">
            <DonutPanel title="Measured Capacity Status" data={dashboard.measured_status_distribution} />
            <MeasuredComparison requested={dashboard.capacity_comparison.requested} measured={dashboard.capacity_comparison.measured} />
          </div>

          <div className="dashboard-row two">
            <BarPanel title="Top 10 Red Suppliers" data={dashboard.top_risk_suppliers} valueSuffix=" lines" />
            <BarPanel title="Top 10 Capacity Gaps" data={dashboard.top_capacity_gaps.map((item) => ({ label: `${item.label}${item.part_number ? ` / ${item.part_number}` : ""}`, value: item.value }))} valueSuffix=" parts/wk" negative />
          </div>

          <div className="dashboard-row two">
            <BarPanel title="Top 10 Measured Capacity Gaps" data={dashboard.top_measured_capacity_gaps.map((item) => ({ label: `${item.label}${item.part_number ? ` / ${item.part_number}` : ""}`, value: item.value }))} valueSuffix=" parts/wk" negative />
            <DonutPanel title="CAT Evaluation G/O/R" data={dashboard.cat_evaluation_distribution} />
          </div>

          <div className="dashboard-row two">
            <CatStatusPanel data={dashboard.cat_status} />
            <StackedRiskPanel title="CAT Evaluation by Supplier" data={dashboard.cat_evaluation_by_supplier} />
          </div>

          <div className="dashboard-row two">
            <BarPanel title="Red Risk by Buyer" data={dashboard.risk_by_buyer} valueSuffix=" lines" />
            <BarPanel title="Red Risk by Country" data={dashboard.risk_by_country} valueSuffix=" lines" />
          </div>

          <PriorityActionsTable rows={dashboard.priority_actions} />
        </>
      )}
    </section>
  );
}

function DonutPanel({ title, data }: { title: string; data: Record<string, number> }) {
  const order = ["Green", "Orange", "Red", "Unknown"];
  const colors: Record<string, string> = { Green: "#16a34a", Orange: "#f59e0b", Red: "#dc2626", Unknown: "#94a3b8" };
  const total = order.reduce((sum, key) => sum + (data[key] ?? 0), 0);
  let cursor = 0;
  const gradient = total
    ? order.map((key) => {
        const value = data[key] ?? 0;
        const start = cursor;
        const end = cursor + (value / total) * 100;
        cursor = end;
        return `${colors[key]} ${start}% ${end}%`;
      }).join(", ")
    : "#e2e8f0 0% 100%";

  return (
    <div className="panel chart-panel">
      <PanelHeader title={title} action={`${total} lines`} />
      <div className="donut-layout">
        <div className="donut" style={{ background: `conic-gradient(${gradient})` }}>
          <div><strong>{total}</strong><span>Total</span></div>
        </div>
        <div className="legend-list">
          {order.map((key) => (
            <div className="legend-item" key={key}>
              <span className="legend-dot" style={{ background: colors[key] }} />
              <span>{key}</span>
              <strong>{data[key] ?? 0}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CapacityComparison({ requested, contracted }: { requested: number; contracted: number }) {
  const maxValue = Math.max(requested, contracted, 1);
  return (
    <div className="panel chart-panel">
      <PanelHeader title="Requested vs Contracted Capacity" action={formatPercentValue(contracted / maxValue)} />
      <div className="comparison-bars">
        <ComparisonBar label="Requested" value={requested} maxValue={maxValue} color="#2563eb" />
        <ComparisonBar label="Contracted" value={contracted} maxValue={maxValue} color="#16a34a" />
      </div>
    </div>
  );
}

function MeasuredComparison({ requested, measured }: { requested: number; measured: number }) {
  const maxValue = Math.max(requested, measured, 1);
  return (
    <div className="panel chart-panel">
      <PanelHeader title="Requested vs Measured Capacity" action={formatPercentValue(measured / maxValue)} />
      <div className="comparison-bars">
        <ComparisonBar label="Requested" value={requested} maxValue={maxValue} color="#2563eb" />
        <ComparisonBar label="Measured" value={measured} maxValue={maxValue} color="#7c3aed" />
      </div>
    </div>
  );
}

function ComparisonBar({ label, value, maxValue, color }: { label: string; value: number; maxValue: number; color: string }) {
  return (
    <div className="comparison-row">
      <div>
        <strong>{label}</strong>
        <span>{formatCapacity(value)}</span>
      </div>
      <div className="comparison-track">
        <span style={{ width: `${Math.max(2, (value / maxValue) * 100)}%`, background: color }} />
      </div>
    </div>
  );
}

function StackedRiskPanel({ title, data }: { title: string; data: Array<Record<string, string | number>> }) {
  const statuses = [
    { key: "Red", color: "#dc2626" },
    { key: "Orange", color: "#f59e0b" },
    { key: "Green", color: "#16a34a" },
    { key: "Unknown", color: "#94a3b8" },
  ];
  return (
    <div className="panel chart-panel compact-chart">
      <PanelHeader title={title} action={`${data.length} groups`} />
      <div className="stacked-risk-list">
        {data.length === 0 && <div className="empty-state">No matching records.</div>}
        {data.map((item) => {
          const label = String(item.label ?? "Unknown");
          const total = statuses.reduce((sum, status) => sum + Number(item[status.key] ?? 0), 0) || 1;
          return (
            <div className="stacked-risk-row" key={label}>
              <span title={label}>{label}</span>
              <div className="stacked-risk-bar">
                {statuses.map((status) => (
                  <i
                    key={status.key}
                    title={`${status.key}: ${item[status.key] ?? 0}`}
                    style={{
                      width: `${(Number(item[status.key] ?? 0) / total) * 100}%`,
                      background: status.color,
                    }}
                  />
                ))}
              </div>
              <strong>{total}</strong>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function BarPanel({ title, data, valueSuffix = "", negative = false }: { title: string; data: Array<{ label: string; value: number }>; valueSuffix?: string; negative?: boolean }) {
  const maxValue = Math.max(...data.map((item) => Math.abs(item.value)), 1);
  return (
    <div className="panel chart-panel">
      <PanelHeader title={title} action={`${data.length} items`} />
      <div className="bar-list">
        {data.length === 0 && <div className="empty-state">No matching records.</div>}
        {data.map((item) => (
          <div className="bar-row" key={`${item.label}-${item.value}`}>
            <span title={item.label}>{item.label || "Unknown"}</span>
            <div className="bar-track">
              <i style={{ width: `${Math.max(3, (Math.abs(item.value) / maxValue) * 100)}%` }} className={negative ? "negative" : ""} />
            </div>
            <strong>{formatBarValue(item.value)}{valueSuffix}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function CatStatusPanel({ data }: { data: Record<string, Record<string, number>> }) {
  const statuses = ["Done", "Late", "Planned", "Not planned"];
  return (
    <div className="panel chart-panel">
      <PanelHeader title="CAT1 / CAT2 / CAT3 Follow-up" action="Status mix" />
      <div className="cat-status-grid">
        {Object.entries(data).map(([cat, values]) => {
          const total = statuses.reduce((sum, status) => sum + (values[status] ?? 0), 0) || 1;
          return (
            <div className="cat-card" key={cat}>
              <strong>{cat}</strong>
              <div className="stacked-bar">
                {statuses.map((status) => (
                  <span
                    className={`cat-${status.toLowerCase().replace(" ", "-")}`}
                    style={{ width: `${((values[status] ?? 0) / total) * 100}%` }}
                    key={status}
                    title={`${status}: ${values[status] ?? 0}`}
                  />
                ))}
              </div>
              <div className="cat-mini-grid">
                {statuses.map((status) => <span key={status}>{status}: <b>{values[status] ?? 0}</b></span>)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PriorityActionsTable({ rows }: { rows: Array<Record<string, unknown>> }) {
  const columns = [
    ["priority", "Priority"],
    ["supplier_name", "Supplier Name"],
    ["country", "Country"],
    ["location", "Location"],
    ["part_number", "Part Number"],
    ["part_name", "Part Name"],
    ["buyer", "Buyer"],
    ["sqe", "SQE"],
    ["last_weekly_capacity_requested", "Requested"],
    ["weekly_capacity_contracted", "Contracted"],
    ["weekly_capacity_measured", "Measured"],
    ["capacity_gap", "Capacity Gap"],
    ["coverage_rate", "Coverage Rate"],
    ["measured_capacity_gap", "Measured Gap"],
    ["measured_coverage_rate", "Measured Coverage"],
    ["measured_capacity_status", "Measured Status"],
    ["gor", "GOR"],
    ["cat_status", "CAT Status"],
    ["cat_evaluation_status", "CAT Evaluation"],
    ["capacity_workshop_done_date", "Workshop Done"],
    ["shared_folder_link", "Shared Folder"],
    ["comments", "Comments"],
  ];
  return (
    <div className="panel priority-panel">
      <PanelHeader title="Priority Actions" action={`${rows.length} rows`} />
      <div className="table-wrap priority-wrap">
        <table>
          <thead>
            <tr>
              {columns.map(([, label]) => <th key={label}>{label}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={`${row.record_id ?? index}-${index}`}>
                {columns.map(([key]) => (
                  <td key={key} className={["gor", "cat_evaluation_status", "measured_capacity_status"].includes(key) ? `risk-cell ${riskClass(row[key])}` : ""}>
                    {formatDashboardCell(key, row[key])}
                  </td>
                ))}
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={columns.length}>No priority action for the current filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Projects({
  projects,
  mode,
  user,
  role,
  onProjectUpdated,
  onProjectCreated,
}: {
  projects: UIProject[];
  mode: "manage" | "create";
  user: ApiUser;
  role: AppRole;
  onProjectUpdated: (project: UIProject) => void;
  onProjectCreated: (project: UIProject) => void;
}) {
  const [selectedManageProject, setSelectedManageProject] = useState(projects[0]?.id ?? "");
  const [form, setForm] = useState({
    project: "",
    partOfProject: "",
    capacityManager: user.email,
    buyer: "",
    sqd: "",
    status: "ACTIVE",
  });
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [error, setError] = useState("");
  const [completedImport, setCompletedImport] = useState<ParsedImportFile | null>(null);
  const [completedMapping, setCompletedMapping] = useState<Record<string, string>>({});
  const [completedColumns, setCompletedColumns] = useState<string[]>(cmfColumns);
  const [notice, setNotice] = useState("");
  const [createCustomColumns, setCreateCustomColumns] = useState<CustomColumnDraft[]>([]);
  const [manageCustomColumns, setManageCustomColumns] = useState<ApiProjectColumn[]>([]);
  const [newManageCustomColumn, setNewManageCustomColumn] = useState<CustomColumnDraft>({ name: "", ownerRole: "BUYER", section: defaultCustomSection("BUYER") });
  const manageProject = projects.find((item) => item.id === selectedManageProject) ?? projects[0];
  const [manageForm, setManageForm] = useState({
    partOfProject: manageProject?.partOfProject ?? "",
    capacityManager: manageProject?.capacityManager ?? "",
    buyer: manageProject?.buyer ?? "",
    sqd: manageProject?.sqd ?? "",
    supplier: manageProject?.supplier ?? "",
    status: manageProject?.status ?? "ACTIVE",
  });
  const canManageSelected = manageProject ? canEditProject(user, role, manageProject) : false;

  useEffect(() => {
    if (!manageProject) return;
    setManageForm({
      partOfProject: manageProject.partOfProject,
      capacityManager: manageProject.capacityManager.startsWith("Unassigned") ? "" : manageProject.capacityManager,
      buyer: manageProject.buyer.startsWith("Unassigned") ? "" : manageProject.buyer,
      sqd: manageProject.sqd.startsWith("Unassigned") ? "" : manageProject.sqd,
      supplier: manageProject.supplier === "Multiple suppliers" ? "" : manageProject.supplier,
      status: manageProject.status,
    });
  }, [manageProject?.id]);

  useEffect(() => {
    if (!manageProject?.apiId || mode !== "manage") return;
    fetchProjectColumns(manageProject.apiId)
      .then((columns) => setManageCustomColumns(columns.filter((column) => column.is_custom)))
      .catch(() => setManageCustomColumns([]));
  }, [manageProject?.apiId, mode]);

  function setField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function addCreateCustomColumn() {
    setCreateCustomColumns((current) => [...current, { name: "", ownerRole: "BUYER", section: defaultCustomSection("BUYER") }]);
  }

  function updateCreateCustomColumn(index: number, patch: Partial<CustomColumnDraft>) {
    setCreateCustomColumns((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)));
  }

  function removeCreateCustomColumn(index: number) {
    setCreateCustomColumns((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  async function addManagedCustomColumn() {
    if (!manageProject?.apiId || !newManageCustomColumn.name.trim()) return;
    if (!canManageSelected) {
      setError("Read-only: you are not assigned to this project.");
      return;
    }
    setError("");
    setNotice("");
    try {
      const column = await addCustomColumn(manageProject.apiId, {
        column_name: newManageCustomColumn.name,
        owner_role: newManageCustomColumn.ownerRole,
        section: newManageCustomColumn.section,
        actor_email: user.email,
      });
      setManageCustomColumns((current) => [...current.filter((item) => item.column_name !== column.column_name), column]);
      setNewManageCustomColumn({ name: "", ownerRole: "BUYER", section: defaultCustomSection("BUYER") });
      setNotice("Custom column added.");
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to add custom column");
    }
  }

  async function loadCompletedCmf(file: File) {
    setError("");
    setNotice("");
    try {
      const [parsed, schemaColumns] = await Promise.all([
        parseImportFile({ filename: file.name, content_base64: await fileToBase64(file) }),
        fetchSchema().catch(() => cmfColumns),
      ]);
      const usableColumns = schemaColumns.filter((column) => column !== "CMF LINE NÂ°");
      setCompletedColumns(usableColumns);
      setCompletedImport(parsed);
      setCompletedMapping(Object.fromEntries(usableColumns.map((column) => [column, guessMappedColumn(column, parsed.columns)])));
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to read completed CMF");
      setSaveState("error");
    }
  }

  async function importCompletedRows(projectId: number) {
    if (!completedImport) return { ok: 0, failed: 0 };
    let ok = 0;
    let failed = 0;
    for (const row of completedImport.rows) {
      const partColumn = completedMapping["PART NUMBER"];
      const partNumber = partColumn ? String(row[partColumn] ?? "").trim() : "";
      if (!partNumber) {
        failed += 1;
        continue;
      }
      const values = Object.fromEntries(
        completedColumns
          .filter((column) => column !== "PART NUMBER" && column !== "APQP GRID" && completedMapping[column])
          .map((column) => [column, row[completedMapping[column]] ?? ""])
          .filter(([, value]) => String(value).trim())
      );
      try {
        await upsertRecord(projectId, {
          part_number: partNumber,
          apqp_grid: completedMapping["APQP GRID"] ? String(row[completedMapping["APQP GRID"]] ?? "") : undefined,
          values,
          updated_by: form.capacityManager || "capacity_manager",
          actor_email: user.email,
        });
        ok += 1;
      } catch {
        failed += 1;
      }
    }
    return { ok, failed };
  }

  async function submitProject() {
    setSaveState("saving");
    setError("");
    setNotice("");
    try {
      const created = await createProject({
        project: form.project,
        part_of_project: form.partOfProject,
        capacity_manager_name: form.capacityManager,
        buyer_assigned_name: form.buyer || undefined,
        sqd_assigned_name: form.sqd || undefined,
        cmf_status: form.status,
        created_by: form.capacityManager,
        custom_columns: createCustomColumns
          .filter((column) => column.name.trim())
          .map((column) => ({ column_name: column.name.trim(), owner_role: column.ownerRole, section: column.section })),
      });
      const imported = await importCompletedRows(created.id);
      onProjectCreated({ ...mapApiProject(created), records: completedImport ? imported.ok : mapApiProject(created).records });
      setSaveState("saved");
      if (completedImport) {
        if (imported.failed) {
          setError(`${imported.ok} imported, ${imported.failed} skipped/errors`);
        } else {
          setNotice(`${imported.ok} rows imported into new CMF`);
        }
      }
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to create project");
      setSaveState("error");
    }
  }

  async function saveManagedProject() {
    if (!manageProject?.apiId) return;
    if (!canManageSelected) {
      setError("Read-only: you are not assigned to this project.");
      return;
    }
    setSaveState("saving");
    setError("");
    try {
      const updated = await updateProject(manageProject.apiId, {
        name: manageForm.partOfProject,
        capacity_manager_name: manageForm.capacityManager || undefined,
        buyer_assigned_name: manageForm.buyer || undefined,
        sqd_assigned_name: manageForm.sqd || undefined,
        supplier_name: manageForm.supplier || undefined,
        cmf_status: manageForm.status,
        actor_email: user.email,
      });
      onProjectUpdated(mapApiProject(updated));
      setSaveState("saved");
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to update project");
      setSaveState("error");
    }
  }

  return (
    <section className="page-grid">
      <div className="page-title">
        <div>
          <span className="eyebrow">{mode === "create" ? "Create Project" : "Manage Projects"}</span>
          <h1>{mode === "create" ? "Create Projet / Part of Project" : "Project Control"}</h1>
          <p>{mode === "create" ? "One project can contain multiple parts of project, while each pair stays unique." : "Review assignments, statuses, and project ownership."}</p>
        </div>
      </div>

      <div className={mode === "create" ? "split-layout" : "project-list"}>
        {mode === "manage" && manageProject && (
          <div className="panel form-panel">
            <PanelHeader title="Edit Project" action={manageProject.project} />
            <label className="field">
              <span>Project</span>
              <select value={selectedManageProject} onChange={(event) => setSelectedManageProject(event.target.value)}>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.project} / {project.partOfProject}</option>
                ))}
              </select>
            </label>
            {!canManageSelected && <div className="form-error">Read-only: you can view this project, but only assigned users can modify it.</div>}
            <div className="form-grid">
              <Field label="Part of Project" placeholder="Part" value={manageForm.partOfProject} onChange={(value) => setManageForm((current) => ({ ...current, partOfProject: value }))} disabled={!canManageSelected} />
              <Field label="Capacity Manager" placeholder="capacity_manager" value={manageForm.capacityManager} onChange={(value) => setManageForm((current) => ({ ...current, capacityManager: value }))} disabled={!canManageSelected} />
              <Field label="Buyer" placeholder="buyer" value={manageForm.buyer} onChange={(value) => setManageForm((current) => ({ ...current, buyer: value }))} disabled={!canManageSelected} />
              <Field label="SQD" placeholder="sqd" value={manageForm.sqd} onChange={(value) => setManageForm((current) => ({ ...current, sqd: value }))} disabled={!canManageSelected} />
              <Field label="Supplier" placeholder="supplier" value={manageForm.supplier} onChange={(value) => setManageForm((current) => ({ ...current, supplier: value }))} disabled={!canManageSelected} />
              <label className="field">
                <span>Status</span>
                <select value={manageForm.status} disabled={!canManageSelected} onChange={(event) => setManageForm((current) => ({ ...current, status: event.target.value }))}>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PAUSED">PAUSED</option>
                  <option value="ARCHIVED">ARCHIVED</option>
                </select>
              </label>
            </div>
            <div className="custom-column-box">
              <PanelHeader title="Customized Columns" action="Assign role" />
              <div className="form-grid three">
                <Field label="Column Name" placeholder="Custom CMF column" value={newManageCustomColumn.name} onChange={(value) => setNewManageCustomColumn((current) => ({ ...current, name: value }))} disabled={!canManageSelected} />
                <label className="field">
                  <span>Assigned user role</span>
                  <select
                    value={newManageCustomColumn.ownerRole}
                    disabled={!canManageSelected}
                    onChange={(event) => {
                      const ownerRole = event.target.value;
                      setNewManageCustomColumn((current) => ({ ...current, ownerRole, section: defaultCustomSection(ownerRole) }));
                    }}
                  >
                    {customColumnRoles.map((roleOption) => <option key={roleOption} value={roleOption}>{roleOption}</option>)}
                  </select>
                </label>
                <label className="field">
                  <span>Partie Section</span>
                  <select value={newManageCustomColumn.section} disabled={!canManageSelected} onChange={(event) => setNewManageCustomColumn((current) => ({ ...current, section: event.target.value }))}>
                    {(customColumnSectionsByRole[newManageCustomColumn.ownerRole] ?? []).map((sectionOption) => <option key={sectionOption} value={sectionOption}>{sectionOption}</option>)}
                  </select>
                </label>
                <button className="primary-button full" onClick={addManagedCustomColumn} disabled={!canManageSelected}>Add column</button>
              </div>
              <div className="custom-column-list">
                {manageCustomColumns.map((column) => (
                  <span key={column.column_name}>{column.column_name} {">"} {(column.roles?.[0] ?? column.owner_role)} {">"} {column.section}</span>
                ))}
              </div>
            </div>
            {error && <div className="form-error">{error}</div>}
            {notice && <div className="form-success">{notice}</div>}
            {saveState === "saved" && <div className="form-success">Project updated.</div>}
            <button className="primary-button full" onClick={saveManagedProject} disabled={!canManageSelected}>Update Project</button>
          </div>
        )}
        {mode === "create" && <div className="panel form-panel">
          <PanelHeader title="Create CMF" action="Draft" />
          <div className="form-grid">
            <Field label="Projet" placeholder="CMP EV9" value={form.project} onChange={(value) => setField("project", value)} />
            <Field label="Part of Project" placeholder="Battery Cooling" value={form.partOfProject} onChange={(value) => setField("partOfProject", value)} />
            <Field label="Capacity Manager" placeholder="capacity_manager" value={form.capacityManager} onChange={(value) => setField("capacityManager", value)} />
            <Field label="Buyer" placeholder="buyer_username" value={form.buyer} onChange={(value) => setField("buyer", value)} />
            <Field label="SQD" placeholder="sqd_username" value={form.sqd} onChange={(value) => setField("sqd", value)} />
            <label className="field">
              <span>Status</span>
              <select value={form.status} onChange={(event) => setField("status", event.target.value)}>
                <option value="ACTIVE">Active</option>
                <option value="PAUSED">Paused</option>
                <option value="ARCHIVED">Archived</option>
              </select>
            </label>
          </div>
          <div className="custom-column-box">
            <PanelHeader title="Customized Columns" action="Optional" />
            <div className="custom-column-list">
              {createCustomColumns.map((column, index) => (
                <div className="mapping-row custom-column-row" key={index}>
                  <input value={column.name} onChange={(event) => updateCreateCustomColumn(index, { name: event.target.value })} placeholder="Custom column name" />
                  <ChevronDown size={16} />
                  <select
                    value={column.ownerRole}
                    onChange={(event) => {
                      const ownerRole = event.target.value;
                      updateCreateCustomColumn(index, { ownerRole, section: defaultCustomSection(ownerRole) });
                    }}
                  >
                    {customColumnRoles.map((roleOption) => <option key={roleOption} value={roleOption}>{roleOption}</option>)}
                  </select>
                  <select value={column.section} onChange={(event) => updateCreateCustomColumn(index, { section: event.target.value })}>
                    {(customColumnSectionsByRole[column.ownerRole] ?? []).map((sectionOption) => <option key={sectionOption} value={sectionOption}>{sectionOption}</option>)}
                  </select>
                  <button className="ghost-button" onClick={() => removeCreateCustomColumn(index)}>Remove</button>
                </div>
              ))}
            </div>
            <button className="secondary-button full" onClick={addCreateCustomColumn}>Add customized column</button>
          </div>
          <div className="upload-band">
            <UploadCloud size={22} />
            <div>
              <strong>Import completed CMF</strong>
              <span>Upload Excel, CSV, TSV, or TXT, then map file columns before creation.</span>
            </div>
            <label className="ghost-button file-button">
              Browse
              <input type="file" accept=".xlsx,.xlsm,.csv,.tsv,.txt" onChange={(event) => event.target.files?.[0] && loadCompletedCmf(event.target.files[0])} />
            </label>
          </div>
          {completedImport && (
            <div className="mapping-grid create-import-mapping">
              {completedColumns.map((column) => (
                <div className="mapping-row" key={column}>
                  <span>{column}</span>
                  <ChevronDown size={16} />
                  <select value={completedMapping[column] ?? ""} onChange={(event) => setCompletedMapping((current) => ({ ...current, [column]: event.target.value }))}>
                    <option value="">Skip</option>
                    {completedImport.columns.map((fileColumn) => <option key={fileColumn} value={fileColumn}>{fileColumn}</option>)}
                  </select>
                </div>
              ))}
            </div>
          )}
          {error && <div className="form-error">{error}</div>}
          {notice && <div className="form-success">{notice}</div>}
          {saveState === "saved" && <div className="form-success">Project created in SQLite through FastAPI.</div>}
          <button className="primary-button full" onClick={submitProject} disabled={saveState === "saving"}>
            {saveState === "saving" ? "Creating..." : "Create project"}
          </button>
        </div>}

        <div className="project-list">
          {projects.map((project) => (
            <div className="project-card" key={project.id}>
              <div>
                <span className="eyebrow">{project.project}</span>
                <h3>{project.partOfProject}</h3>
              </div>
              <span className={`status ${project.status.toLowerCase()}`}>{project.status}</span>
              <div className="card-meta">
                <span>{project.records} records</span>
                <span>{project.capacityManager}</span>
                <span>{project.supplier}</span>
                <span>{project.updated}</span>
              </div>
              <div className="assignment-row">
                <span>{project.buyer}</span>
                <ArrowRight size={16} />
                <span>{project.sqd}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FullCmfGrid({
  project,
  fallbackRecords,
  title = "CMF Data",
  embedded = false,
  canEdit = false,
  role = "Buyer",
  user,
  onRecordsChanged,
}: {
  project: UIProject;
  fallbackRecords: UIRecord[];
  title?: string;
  embedded?: boolean;
  canEdit?: boolean;
  role?: AppRole;
  user?: ApiUser;
  onRecordsChanged?: (records: UIRecord[]) => void;
}) {
  const [filter, setFilter] = useState("");
  const [columns, setColumns] = useState<string[]>([]);
  const [defaultVisible, setDefaultVisible] = useState<string[]>([]);
  const [visibleColumns, setVisibleColumns] = useState<string[]>([]);
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [message, setMessage] = useState("");
  const [columnFilters, setColumnFilters] = useState<Record<string, string>>({});
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedRecordIds, setSelectedRecordIds] = useState<number[]>([]);
  const [editDraft, setEditDraft] = useState<Record<string, string> | null>(null);
  const [showActionPlan, setShowActionPlan] = useState(false);
  const [actionProblem, setActionProblem] = useState("CAT Requested vs Measured");
  const [actionText, setActionText] = useState("");
  const [actionOldValue, setActionOldValue] = useState("");
  const [actionNewValue, setActionNewValue] = useState("");
  const [showPlans, setShowPlans] = useState(false);
  const [actionPlans, setActionPlans] = useState<ApiActionPlan[]>([]);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!project?.apiId) {
      const fallbackColumns = [
        "N° SOURCING, RFQ,ODM,FETE …",
        "APQP GRID",
        "USE CASES",
        "PART NUMBER",
        "WEEKLY CAPACITY CONTRACTED (Parts/Week)",
        "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer",
        "CAT1/2/3 VALUATION (G;O;R)",
      ];
      setColumns(fallbackColumns);
      setDefaultVisible(fallbackColumns);
      setVisibleColumns(fallbackColumns);
      setRows(fallbackRecords.map((record) => ({
        "__record_id": record.id,
        "APQP GRID": record.apqp,
        "USE CASES": record.useCase,
        "PART NUMBER": record.part,
        "WEEKLY CAPACITY CONTRACTED (Parts/Week)": record.contracted,
        "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer": record.gor,
        "CAT1/2/3 VALUATION (G;O;R)": record.cat,
      })));
      return;
    }

    setMessage("Loading CMF data...");
    fetchProjectFullData(project.apiId)
      .then((data) => {
        setColumns(data.columns);
        setDefaultVisible(data.default_visible);
        setVisibleColumns(data.default_visible.length ? data.default_visible : data.columns.slice(0, 7));
        setRows(data.records);
        setMessage("");
      })
      .catch((event) => {
        setMessage(event instanceof Error ? event.message : "Unable to load CMF data");
      });
  }, [project?.apiId, fallbackRecords, reloadToken]);

  useEffect(() => {
    setSelectedRecordIds([]);
    setEditDraft(null);
    setShowActionPlan(false);
    setShowPlans(false);
  }, [project?.apiId]);

  const visibleRows = rows.filter((row) => {
    const globalMatch = Object.values(row).join(" ").toLowerCase().includes(filter.toLowerCase());
    const columnMatch = visibleColumns.every((column) => {
      const columnFilter = (columnFilters[column] ?? "").trim().toLowerCase();
      return !columnFilter || String(row[column] ?? "").toLowerCase().includes(columnFilter);
    });
    return globalMatch && columnMatch;
  });
  const ragColumns = [
    "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer Capacity Requested",
    "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer",
    "CAT1/2/3 VALUATION (G;O;R)",
  ];
  const editableGridColumns = visibleColumns.filter((column) => ![
    "CMF LINE NÂ°",
    "CMF LINE NÃ‚Â°",
    "ROADMAP",
    "CarryOver - Adapted",
    "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer Capacity Requested",
    "GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer",
    "CAT1/2/3 VALUATION (G;O;R)",
    "WEEKLY CAPACITY TO MEASURE",
  ].includes(column));
  const selectedRows = rows.filter((row) => selectedRecordIds.includes(rowRecordId(row)));
  const selectedRow = selectedRows[0];
  const canUseSelectionActions = canEdit && Boolean(project.apiId) && Boolean(user);
  const selectedIsCritical = selectedRow ? ["r", "o"].some((value) => (
    String(selectedRow["CAT1/2/3 VALUATION (G;O;R)"] ?? "").trim().toLowerCase() === value
    || String(selectedRow["GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer"] ?? "").trim().toLowerCase() === value
    || String(selectedRow["GOR (Green, Orange, Red) Supplier Capacity Contracted regarding Buyer Capacity Requested"] ?? "").trim().toLowerCase() === value
  )) : false;
  const actionTargetColumn = actionProblem === "CAT Requested vs Measured" ? "WEEKLY CAPACITY MEASURED" : "WEEKLY CAPACITY CONTRACTED (Parts/Week)";
  const actionCurrentOldValue = actionOldValue || String(selectedRow?.[actionTargetColumn] ?? "");

  function toggleColumn(column: string) {
    setVisibleColumns((current) => (
      current.includes(column)
        ? current.filter((item) => item !== column)
        : columns.filter((item) => item === column || current.includes(item))
    ));
  }

  async function exportExactCmf() {
    if (!project.apiId) return;
    setMessage("Preparing Excel export...");
    try {
      const blob = await downloadProjectCmfExport(project.apiId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `CMF_export_${project.project}_${project.partOfProject}.xlsx`.replace(/[\\/:*?"<>|]+/g, "_");
      link.click();
      URL.revokeObjectURL(url);
      setMessage("");
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to export CMF");
    }
  }

  function rowRecordId(row: Record<string, unknown>) {
    return Number(row.__record_id ?? 0);
  }

  function toggleSelectedRow(recordId: number) {
    setSelectedRecordIds((current) => (
      current.includes(recordId)
        ? current.filter((item) => item !== recordId)
        : [...current, recordId]
    ));
  }

  async function refreshProjectRows() {
    setReloadToken((current) => current + 1);
    if (project.apiId && onRecordsChanged) {
      const apiRecords = await fetchRecords(project.apiId);
      onRecordsChanged(apiRecords.map(mapApiRecord));
    }
  }

  function startEditSelected() {
    if (selectedRows.length !== 1) return;
    const row = selectedRows[0];
    setEditDraft(Object.fromEntries(editableGridColumns.map((column) => [column, String(row[column] ?? "")])));
    setShowActionPlan(false);
  }

  async function saveEditSelected() {
    if (!project.apiId || !user || !editDraft || selectedRows.length !== 1) return;
    const recordId = rowRecordId(selectedRows[0]);
    const values: Record<string, unknown> = {};
    for (const column of editableGridColumns) {
      if (column !== "PART NUMBER" && column !== "APQP GRID") {
        values[column] = editDraft[column] ?? "";
      }
    }
    setMessage("Saving selected row...");
    try {
      await updateProjectRecord(project.apiId, recordId, {
        part_number: editDraft["PART NUMBER"],
        apqp_grid: editDraft["APQP GRID"],
        values,
        updated_by: user.email,
        actor_email: user.email,
      });
      setEditDraft(null);
      setSelectedRecordIds([]);
      await refreshProjectRows();
      setMessage("Row updated and audit log saved.");
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to update row");
    }
  }

  async function deleteSelectedRows() {
    if (!project.apiId || !user || selectedRecordIds.length === 0) return;
    const confirmed = window.confirm(`Delete ${selectedRecordIds.length} selected row(s)?`);
    if (!confirmed) return;
    setMessage("Deleting selected rows...");
    try {
      for (const recordId of selectedRecordIds) {
        await deleteProjectRecord(project.apiId, recordId, user.email, user.email);
      }
      setSelectedRecordIds([]);
      await refreshProjectRows();
      setMessage("Selected rows deleted and audit log saved.");
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to delete selected rows");
    }
  }

  function startActionPlan() {
    if (!selectedRow) return;
    setActionProblem("CAT Requested vs Measured");
    setActionOldValue(String(selectedRow["WEEKLY CAPACITY MEASURED"] ?? ""));
    setActionNewValue("");
    setActionText("");
    setShowActionPlan(true);
    setEditDraft(null);
  }

  async function submitActionPlan() {
    if (!project.apiId || !user || !selectedRow) return;
    setMessage("Saving action plan...");
    try {
      await createActionPlan(project.apiId, {
        record_id: rowRecordId(selectedRow),
        problem_type: actionProblem,
        action_text: actionText,
        old_value: actionCurrentOldValue,
        new_value: actionNewValue,
        created_by: user.email,
        actor_email: user.email,
      });
      setShowActionPlan(false);
      setSelectedRecordIds([]);
      await refreshProjectRows();
      if (showPlans) {
        setActionPlans(await fetchActionPlans(project.apiId));
      }
      setMessage("Action plan saved, CMF value updated, and audit log saved.");
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to save action plan");
    }
  }

  async function toggleActionPlans() {
    if (!project.apiId) return;
    const next = !showPlans;
    setShowPlans(next);
    if (next) {
      setActionPlans(await fetchActionPlans(project.apiId));
    }
  }

  return (
    <section className={`panel page-grid ${embedded ? "global-overview-table" : ""}`}>
      <div className="page-title inside">
        <div>
          <span className="eyebrow">Unified CMF table</span>
          <h1>{title}</h1>
          <p>Initial view follows the requested CMF columns; the remaining columns stay available in the column picker.</p>
        </div>
        <div className="button-row">
          <label className="filter-input">
            <Filter size={18} />
            <input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filter all CMF columns" />
          </label>
          <button className="secondary-button" onClick={() => setVisibleColumns(defaultVisible)}>
            Reset columns
          </button>
          <button className="secondary-button" onClick={() => {
            setSelectionMode((current) => !current);
            setSelectedRecordIds([]);
            setEditDraft(null);
            setShowActionPlan(false);
          }}>
            Select
          </button>
          {selectionMode && canUseSelectionActions && (
            <>
              <button className="secondary-button" disabled={selectedRecordIds.length !== 1} onClick={startEditSelected}>
                Edit
              </button>
              <button className="secondary-button danger-button" disabled={selectedRecordIds.length === 0} onClick={deleteSelectedRows}>
                Delete
              </button>
              {role === "SQD" && (
                <button className="secondary-button" disabled={selectedRecordIds.length !== 1 || !selectedIsCritical} onClick={startActionPlan}>
                  Action plan
                </button>
              )}
            </>
          )}
          <button className="secondary-button" onClick={exportExactCmf}>
            <Download size={18} />
            Export CMF
          </button>
          <button className="secondary-button" onClick={toggleActionPlans}>
            View Action Plans
          </button>
        </div>
      </div>

      {selectionMode && !canUseSelectionActions && (
        <div className="form-error">Selection actions are read-only because you are not assigned to this project.</div>
      )}
      <div className="column-picker">
        {columns.map((column) => (
          <label key={column} className={visibleColumns.includes(column) ? "selected" : ""}>
            <input type="checkbox" checked={visibleColumns.includes(column)} onChange={() => toggleColumn(column)} />
            <span>{column}</span>
          </label>
        ))}
      </div>

      {message && <div className={message.includes("Unable") ? "form-error" : "form-success"}>{message}</div>}
      {editDraft && (
        <div className="action-panel">
          <PanelHeader title="Edit Selected Row" action="Audit tracked" />
          <div className="form-grid three">
            {editableGridColumns.map((column) => (
              <label className="field" key={column}>
                <span>{column}</span>
                <input value={editDraft[column] ?? ""} onChange={(event) => setEditDraft((current) => ({ ...(current ?? {}), [column]: event.target.value }))} />
              </label>
            ))}
          </div>
          <div className="button-row">
            <button className="primary-button" onClick={saveEditSelected}>Save changes</button>
            <button className="secondary-button" onClick={() => setEditDraft(null)}>Cancel</button>
          </div>
        </div>
      )}
      {showActionPlan && selectedRow && (
        <div className="action-panel">
          <PanelHeader title="SQD Action Plan" action={String(selectedRow["PART NUMBER"] ?? "")} />
          <div className="form-grid">
            <label className="field">
              <span>Problem</span>
              <select value={actionProblem} onChange={(event) => {
                const next = event.target.value;
                setActionProblem(next);
                const nextColumn = next === "CAT Requested vs Measured" ? "WEEKLY CAPACITY MEASURED" : "WEEKLY CAPACITY CONTRACTED (Parts/Week)";
                setActionOldValue(String(selectedRow[nextColumn] ?? ""));
              }}>
                <option>CAT Requested vs Measured</option>
                <option>GOR Requested vs Contracted</option>
              </select>
            </label>
            <label className="field">
              <span>Old value</span>
              <input value={actionCurrentOldValue} onChange={(event) => setActionOldValue(event.target.value)} />
            </label>
            <label className="field">
              <span>New value</span>
              <input value={actionNewValue} onChange={(event) => setActionNewValue(event.target.value)} />
            </label>
            <label className="field wide-field">
              <span>Action done</span>
              <textarea value={actionText} onChange={(event) => setActionText(event.target.value)} rows={4} />
            </label>
          </div>
          <div className="button-row">
            <button className="primary-button" disabled={!actionText.trim() || !actionNewValue.trim()} onClick={submitActionPlan}>Save action plan</button>
            <button className="secondary-button" onClick={() => setShowActionPlan(false)}>Cancel</button>
          </div>
        </div>
      )}
      {showPlans && (
        <div className="action-panel">
          <PanelHeader title="Action Plans" action={`${actionPlans.length} plans`} />
          <div className="table-wrap action-plan-wrap">
            <table>
              <thead>
                <tr>
                  <th>Part Number</th>
                  <th>Problem</th>
                  <th>Action</th>
                  <th>Old</th>
                  <th>New</th>
                  <th>By</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {actionPlans.map((plan) => (
                  <tr key={plan.id}>
                    <td>{plan.part_number}</td>
                    <td>{plan.problem_type}</td>
                    <td>{plan.action_text}</td>
                    <td>{plan.old_value ?? ""}</td>
                    <td>{plan.new_value ?? ""}</td>
                    <td>{plan.created_by}</td>
                    <td>{plan.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      <div className="table-wrap excel-wrap">
        <table className="excel-table">
          <thead>
            <tr>
              {selectionMode && <th className="select-col">Select</th>}
              {visibleColumns.map((column) => (
                <th key={column}>
                  <div className="excel-head">
                    <span>{column}</span>
                    <input
                      value={columnFilters[column] ?? ""}
                      onChange={(event) => setColumnFilters((current) => ({ ...current, [column]: event.target.value }))}
                      placeholder="Filter"
                    />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row, index) => (
              <tr key={index}>
                {selectionMode && (
                  <td className="select-col">
                    <input
                      type="checkbox"
                      checked={selectedRecordIds.includes(rowRecordId(row))}
                      disabled={!rowRecordId(row)}
                      onChange={() => toggleSelectedRow(rowRecordId(row))}
                    />
                  </td>
                )}
                {visibleColumns.map((column) => (
                  <td
                    key={column}
                    tabIndex={0}
                    title="Click to copy"
                    onClick={() => copyCellValue(row[column])}
                    className={`copy-cell ${ragColumns.includes(column) ? `rag-cell rag-${String(row[column] ?? "").trim().toLowerCase()}` : ""}`}
                  >
                    {String(row[column] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DataGrid({ compact = false, records, title = "All CMF Data" }: { compact?: boolean; records: UIRecord[]; title?: string }) {
  const [filter, setFilter] = useState("");
  const [columnFilters, setColumnFilters] = useState<Record<string, string>>({});
  const tableColumns = [
    { key: "part", label: "Part Number", value: (record: UIRecord) => record.part },
    { key: "apqp", label: "APQP", value: (record: UIRecord) => record.apqp },
    { key: "supplier", label: "Supplier", value: (record: UIRecord) => record.supplier },
    { key: "useCase", label: "Use case", value: (record: UIRecord) => record.useCase },
    { key: "contracted", label: "Contracted", value: (record: UIRecord) => record.contracted },
    { key: "requested", label: "Requested", value: (record: UIRecord) => record.requested },
    { key: "cat", label: "CAT", value: (record: UIRecord) => record.cat },
    { key: "gor", label: "GOR", value: (record: UIRecord) => record.gor },
  ];
  const visibleRecords = records.filter((record) => {
    const haystack = Object.values(record).join(" ").toLowerCase();
    const globalMatch = haystack.includes(filter.toLowerCase());
    const columnMatch = tableColumns.every((column) => {
      const columnFilter = (columnFilters[column.key] ?? "").trim().toLowerCase();
      return !columnFilter || String(column.value(record) ?? "").toLowerCase().includes(columnFilter);
    });
    return globalMatch && columnMatch;
  }).sort((left, right) => riskRank(left) - riskRank(right) || left.part.localeCompare(right.part));

  function exportCsv() {
    const headers = ["Part Number", "APQP", "Supplier", "Use case", "Contracted", "Requested", "Measured", "CAT", "GOR"];
    const rows = visibleRecords.map((record) => [
      record.part,
      record.apqp,
      record.supplier,
      record.useCase,
      record.contracted,
      record.requested,
      record.measured,
      record.cat,
      record.gor,
    ]);
    const csv = [headers, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${title.replaceAll(" ", "_").toLowerCase()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className={`panel ${compact ? "" : "page-grid"}`}>
      {!compact && (
        <div className="page-title inside">
          <div>
            <span className="eyebrow">Unified CMF table</span>
            <h1>{title}</h1>
            <p>Shared operational view with Buyer, Capacity Manager, SQD, and automatic columns.</p>
          </div>
          <div className="button-row">
            <label className="filter-input">
              <Filter size={18} />
              <input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filter records" />
            </label>
            <button className="secondary-button" onClick={exportCsv}>
              <Download size={18} />
              Export
            </button>
          </div>
        </div>
      )}
      {compact && <PanelHeader title="CMF Data" action="Copy / filter cells" />}
      <div className="table-wrap excel-wrap">
        <table className="excel-table">
          <thead>
            <tr>
              {tableColumns.map((column) => (
                <th key={column.key}>
                  <div className="excel-head">
                    <span>{column.label}</span>
                    <input
                      value={columnFilters[column.key] ?? ""}
                      onChange={(event) => setColumnFilters((current) => ({ ...current, [column.key]: event.target.value }))}
                      placeholder="Filter"
                    />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRecords.map((record) => (
              <tr key={record.part}>
                <td tabIndex={0} title="Click to copy" onClick={() => copyCellValue(record.part)} className="copy-cell"><strong>{record.part}</strong></td>
                <td tabIndex={0} title="Click to copy" onClick={() => copyCellValue(record.apqp)} className="copy-cell">{record.apqp}</td>
                <td tabIndex={0} title="Click to copy" onClick={() => copyCellValue(record.supplier)} className="copy-cell">{record.supplier}</td>
                <td tabIndex={0} title="Click to copy" onClick={() => copyCellValue(record.useCase)} className="copy-cell">{record.useCase}</td>
                <td tabIndex={0} title="Click to copy" onClick={() => copyCellValue(record.contracted)} className="copy-cell">{record.contracted.toLocaleString()}</td>
                <td tabIndex={0} title="Click to copy" onClick={() => copyCellValue(record.requested)} className="copy-cell">{record.requested.toLocaleString()}</td>
                <td tabIndex={0} title="Click to copy" onClick={() => copyCellValue(record.cat)} className="copy-cell"><HealthPill value={record.cat} /></td>
                <td tabIndex={0} title="Click to copy" onClick={() => copyCellValue(record.gor)} className="copy-cell"><HealthPill value={record.gor} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function BuyerWorkspace({
  project,
  records,
  section,
  canEdit,
  user,
  onSaved,
}: {
  project: UIProject;
  records: UIRecord[];
  section: "PART DATA" | "WEEKLY CONTRACTED CAPACITY";
  canEdit: boolean;
  user: ApiUser;
  onSaved: (records: UIRecord[]) => void;
}) {
  return <Workspace project={project} records={records} onSaved={onSaved} title={section} subtitle="Buyer can view and edit Buyer-owned CMF columns only." role="BUYER" section={section} createIfMissing={section === "PART DATA"} mustSelectExisting={section !== "PART DATA"} canEdit={canEdit} user={user} />;
}

function CapacityWorkspace({
  project,
  records,
  section,
  canEdit,
  user,
  onSaved,
}: {
  project: UIProject;
  records: UIRecord[];
  section: "CAPACITY SIZING" | "CAPACITY WORKSHOP (STEP 2)";
  canEdit: boolean;
  user: ApiUser;
  onSaved: (records: UIRecord[]) => void;
}) {
  return <Workspace project={project} records={records} onSaved={onSaved} title={section === "CAPACITY WORKSHOP (STEP 2)" ? "CAPACITY WORKSHOP" : section} subtitle="Capacity Manager can update capacity-owned columns on existing CMF records." role="CAPACITY_MANAGER" section={section} createIfMissing={false} mustSelectExisting canEdit={canEdit} user={user} />;
}

function SqdCapacityWorkshop({
  project,
  records,
  canEdit,
  user,
  onSaved,
}: {
  project: UIProject;
  records: UIRecord[];
  canEdit: boolean;
  user: ApiUser;
  onSaved: (records: UIRecord[]) => void;
}) {
  return (
    <Workspace
      project={project}
      records={records}
      onSaved={onSaved}
      title="CAPACITY WORKSHOP"
      subtitle="SQD can update SQD-owned workshop fields on existing CMF records."
      role="SQD"
      section="CAPACITY WORKSHOP (STEP 2)"
      createIfMissing={false}
      mustSelectExisting
      canEdit={canEdit}
      user={user}
    />
  );
}

function SqdWorkspace({
  project,
  records,
  section,
  canEdit,
  user,
  onSaved,
}: {
  project: UIProject;
  records: UIRecord[];
  section: "PART DATA" | "SUPPLIER INFORMATION" | "CAT";
  canEdit: boolean;
  user: ApiUser;
  onSaved: (records: UIRecord[]) => void;
}) {
  return (
    <section className="page-grid">
      <Workspace project={project} records={records} onSaved={onSaved} title={section} subtitle="SQD can complete existing Buyer parts or create SQD parts where allowed." role="SQD" section={section} createIfMissing={section === "PART DATA"} mustSelectExisting={section !== "PART DATA"} sqdPartDataMode={section === "PART DATA"} embedded canEdit={canEdit} user={user} />
    </section>
  );
}

function CatWorkspace({ project, records, canEdit, user, onSaved }: { project: UIProject; records: UIRecord[]; canEdit: boolean; user: ApiUser; onSaved: (records: UIRecord[]) => void }) {
  const [planningPart, setPlanningPart] = useState("");
  const [resultPart, setResultPart] = useState("");
  const [customPart, setCustomPart] = useState("");
  const [planningValues, setPlanningValues] = useState<Record<string, string>>({});
  const [resultValues, setResultValues] = useState<Record<string, string>>({ catNumber: "1" });
  const [customCatFields, setCustomCatFields] = useState<string[]>([]);
  const [customCatValues, setCustomCatValues] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const fixedCatFields = new Set([
    "CAT1 FORECASTED DATE (YYCWxx)",
    "CAT2 FORECASTED DATE (YYCWxx)",
    "CAT3 FORECASTED DATE (YYCWxx)",
    "CAT1 REALISED DATE (YYCWxx)",
    "CAT2 REALISED DATE (YYCWxx)",
    "CAT3 REALISED DATE (YYCWxx)",
    "CAT1/2/3 TYPE",
    "WEEKLY CAPACITY MEASURED",
    "WEEKLY CAPACITY ESTIMATED",
    "SHARED FOLDER - link",
    "Comments",
    "PART NUMBER",
    "APQP GRID",
  ]);

  useEffect(() => {
    if (!project.apiId) return;
    fetchEditableColumns(project.apiId, "SQD", "CAT")
      .then((columns) => setCustomCatFields(columns.filter((column) => !fixedCatFields.has(column))))
      .catch(() => setCustomCatFields([]));
  }, [project.apiId]);

  async function refreshRecords() {
    if (!project.apiId) return;
    const refreshed = await fetchRecords(project.apiId);
    onSaved(refreshed.map(mapApiRecord));
  }

  async function savePlanning() {
    if (!project.apiId || !planningPart) return;
    if (!canEdit) {
      setSaveState("error");
      setMessage("Read-only: you are not assigned to this project.");
      return;
    }
    setSaveState("saving");
    setMessage("");
    try {
      await saveRoleRecord(project.apiId, {
        part_number: planningPart,
        values: {
          "CAT1 FORECASTED DATE (YYCWxx)": planningValues["CAT1 FORECASTED DATE (YYCWxx)"] ?? "",
          "CAT3 FORECASTED DATE (YYCWxx)": planningValues["CAT3 FORECASTED DATE (YYCWxx)"] ?? "",
          "CAT2 FORECASTED DATE (YYCWxx)": planningValues["CAT2 FORECASTED DATE (YYCWxx)"] ?? "",
        },
        role: "SQD",
        section: "CAT",
        create_if_missing: false,
        updated_by: user.email,
        actor_email: user.email,
      });
      await refreshRecords();
      setSaveState("saved");
      setMessage("CAT planning saved.");
    } catch (event) {
      setSaveState("error");
      setMessage(event instanceof Error ? event.message : "Unable to save CAT planning");
    }
  }

  async function saveResults() {
    if (!project.apiId || !resultPart) return;
    if (!canEdit) {
      setSaveState("error");
      setMessage("Read-only: you are not assigned to this project.");
      return;
    }
    setSaveState("saving");
    setMessage("");
    const catNumber = resultValues.catNumber || "1";
    const realisedColumn = `CAT${catNumber} REALISED DATE (YYCWxx)`;
    try {
      await saveRoleRecord(project.apiId, {
        part_number: resultPart,
        values: {
          [realisedColumn]: resultValues["CAT REALISED DATE (YYCWxx)"] ?? "",
          "CAT1/2/3 TYPE": resultValues["CAT1/2/3 TYPE"] ?? "",
          "WEEKLY CAPACITY ESTIMATED": resultValues["WEEKLY CAPACITY ESTIMATED"] ?? "",
          "Comments": resultValues.Comments ?? "",
          "WEEKLY CAPACITY MEASURED": resultValues["WEEKLY CAPACITY MEASURED"] ?? "",
          "SHARED FOLDER - link": resultValues["SHARED FOLDER - link"] ?? "",
        },
        role: "SQD",
        section: "CAT",
        create_if_missing: false,
        updated_by: user.email,
        actor_email: user.email,
      });
      await refreshRecords();
      setSaveState("saved");
      setMessage(`${realisedColumn} updated.`);
    } catch (event) {
      setSaveState("error");
      setMessage(event instanceof Error ? event.message : "Unable to save CAT results");
    }
  }

  async function saveCustomCat() {
    if (!project.apiId || !customPart) return;
    if (!canEdit) {
      setSaveState("error");
      setMessage("Read-only: you are not assigned to this project.");
      return;
    }
    const values = Object.fromEntries(
      customCatFields
        .map((field) => [field, customCatValues[field] ?? ""])
        .filter(([, value]) => String(value).trim())
    );
    if (!Object.keys(values).length) {
      setMessage("No customized CAT values to save.");
      return;
    }
    setSaveState("saving");
    setMessage("");
    try {
      await saveRoleRecord(project.apiId, {
        part_number: customPart,
        values,
        role: "SQD",
        section: "CAT",
        create_if_missing: false,
        updated_by: user.email,
        actor_email: user.email,
      });
      await refreshRecords();
      setSaveState("saved");
      setMessage("Customized CAT fields saved.");
    } catch (event) {
      setSaveState("error");
      setMessage(event instanceof Error ? event.message : "Unable to save customized CAT fields");
    }
  }

  return (
    <section className="page-grid">
      <div className="page-title">
        <div>
          <span className="eyebrow">SQD owned data</span>
          <h1>CAT</h1>
          <p>Forecast planning and realised CAT measurements are saved to the standard CMF columns.</p>
        </div>
      </div>
      {!canEdit && <div className="form-error">Read-only: you can view all projects and records, but you can only modify projects assigned to you.</div>}

      <div className="panel form-panel">
        <PanelHeader title="Section A: CAT Planning - Forecast Dates" action="SQD" />
        <label className="field part-selector">
          <span>Select Part Number</span>
          <PartNumberPicker records={records} value={planningPart} onChange={setPlanningPart} placeholder="Type PN prefix, e.g. 9 or 95" />
        </label>
        <div className="form-grid three">
          {["CAT1 FORECASTED DATE (YYCWxx)", "CAT3 FORECASTED DATE (YYCWxx)", "CAT2 FORECASTED DATE (YYCWxx)"].map((field) => (
            <Field key={field} label={field} placeholder="YYCWxx" value={planningValues[field] ?? ""} onChange={(value) => setPlanningValues((current) => ({ ...current, [field]: value }))} disabled={!canEdit} />
          ))}
        </div>
        <button className="primary-button full" onClick={savePlanning} disabled={saveState === "saving" || !planningPart || !canEdit}>Save Section A</button>
      </div>

      <div className="panel form-panel">
        <PanelHeader title="Section B: CAT Results & Measurements" action="SQD" />
        <label className="field part-selector">
          <span>Select Part Number</span>
          <PartNumberPicker records={records} value={resultPart} onChange={setResultPart} placeholder="Type PN prefix, e.g. 9 or 95" />
        </label>
        <div className="form-grid three">
          <label className="field">
            <span>CAT Number</span>
            <select value={resultValues.catNumber ?? "1"} disabled={!canEdit} onChange={(event) => setResultValues((current) => ({ ...current, catNumber: event.target.value }))}>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
            </select>
          </label>
          {["CAT REALISED DATE (YYCWxx)", "CAT1/2/3 TYPE", "WEEKLY CAPACITY ESTIMATED", "Comments", "WEEKLY CAPACITY MEASURED", "SHARED FOLDER - link"].map((field) => (
            <Field key={field} label={field} placeholder="Enter value" value={resultValues[field] ?? ""} onChange={(value) => setResultValues((current) => ({ ...current, [field]: value }))} disabled={!canEdit} />
          ))}
        </div>
        <div className="rule-box">
          <Check size={18} />
          <span>CAT Number routes CAT REALISED DATE into CAT1, CAT2, or CAT3 REALISED DATE.</span>
        </div>
        <button className="primary-button full" onClick={saveResults} disabled={saveState === "saving" || !resultPart || !canEdit}>Save Section B</button>
      </div>

      {customCatFields.length > 0 && (
        <div className="panel form-panel">
          <PanelHeader title="Customized CAT Fields" action="SQD" />
          <label className="field part-selector">
            <span>Select Part Number</span>
            <PartNumberPicker records={records} value={customPart} onChange={setCustomPart} placeholder="Type PN prefix, e.g. 9 or 95" />
          </label>
          <div className="form-grid">
            {customCatFields.map((field) => (
              <Field key={field} label={field} placeholder="Enter value" value={customCatValues[field] ?? ""} onChange={(value) => setCustomCatValues((current) => ({ ...current, [field]: value }))} disabled={!canEdit} />
            ))}
          </div>
          <button className="primary-button full" onClick={saveCustomCat} disabled={saveState === "saving" || !customPart || !canEdit}>Save Customized CAT Fields</button>
        </div>
      )}

      {message && <div className={saveState === "error" ? "form-error" : "form-success"}>{message}</div>}
    </section>
  );
}

function CrossProjectView({ projects }: { projects: UIProject[] }) {
  const [data, setData] = useState<ApiCrossProject>({ projects: [], records: [] });
  const [filter, setFilter] = useState("");

  useEffect(() => {
    fetchCrossProject().then(setData).catch(() => setData({ projects: [], records: [] }));
  }, []);

  const filteredRows = data.records.filter((row) => Object.values(row).join(" ").toLowerCase().includes(filter.toLowerCase()));
  const adapted = data.records.filter((row) => row["CarryOver - Adapted"] === "Adapted").length;
  const carryOver = data.records.filter((row) => row["CarryOver - Adapted"] === "CarryOver").length;

  return (
    <section className="page-grid">
      <div className="page-title">
        <div>
          <span className="eyebrow">Buyer visibility</span>
          <h1>VEHICULES ROAD MAP</h1>
          <p>VEHICULES ROAD MAP view: one project returns Adapted, multiple projects return CarryOver.</p>
        </div>
        <label className="filter-input">
          <Filter size={18} />
          <input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filter part numbers" />
        </label>
      </div>
      <div className="metrics-grid">
        <Metric label="Part Numbers" value={String(data.records.length)} detail="All CMF projects" />
        <Metric label="Adapted" value={String(adapted)} detail="Exists in one project" tone="G" />
        <Metric label="CarryOver" value={String(carryOver)} detail="Exists in multiple projects" tone="O" />
        <Metric label="Projects" value={String(data.projects.length || projects.length)} detail="Road map columns" />
      </div>
      <div className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>APQP</th>
                <th>Part Name</th>
                <th>Part Number</th>
                <th>CarryOver - Adapted</th>
                {data.projects.map((projectLabel) => <th key={projectLabel}>{projectLabel}</th>)}
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((row, index) => (
                <tr key={index}>
                  <td>{String(row.APQP ?? "")}</td>
                  <td>{String(row["Part Name"] ?? "")}</td>
                  <td><strong>{String(row["Part Number"] ?? "")}</strong></td>
                  <td>{String(row["CarryOver - Adapted"] ?? "")}</td>
                  {data.projects.map((projectLabel) => <td key={projectLabel}>{row[projectLabel] ? "X" : ""}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function AdminUsers() {
  const [users, setUsers] = useState<ApiUser[]>([]);
  const [form, setForm] = useState({ email: "", fullName: "", role: "BUYER", password: "" });
  const [passwords, setPasswords] = useState<Record<number, string>>({});
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchUsers().then(setUsers).catch(() => setUsers([]));
  }, []);

  async function addUser() {
    try {
      const user = await createUser({ email: form.email, full_name: form.fullName, role: form.role, password: form.password });
      setUsers((current) => [user, ...current]);
      setMessage("User created.");
      setForm({ email: "", fullName: "", role: "BUYER", password: "" });
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to create user");
    }
  }

  async function changeRole(userId: number, role: string) {
    const updated = await updateUserRole(userId, role);
    setUsers((current) => current.map((user) => (user.id === userId ? updated : user)));
  }

  async function changePassword(userId: number) {
    const password = passwords[userId] ?? "";
    const updated = await updateUserPassword(userId, password);
    setUsers((current) => current.map((user) => (user.id === userId ? updated : user)));
    setPasswords((current) => ({ ...current, [userId]: "" }));
    setMessage("Password updated.");
  }

  async function removeUser(userId: number) {
    if (!window.confirm("Delete this user?")) return;
    await deleteUser(userId);
    setUsers((current) => current.filter((user) => user.id !== userId));
    setMessage("User deleted.");
  }

  return (
    <section className="page-grid">
      <div className="page-title">
        <div>
          <span className="eyebrow">Admin Users</span>
          <h1>User and Role Administration</h1>
          <p>Add users, update roles, and prepare project assignments.</p>
        </div>
        <button className="primary-button" onClick={addUser}><Plus size={18} /> Add user</button>
      </div>
      <div className="panel">
        <div className="form-grid three admin-create">
          <Field label="Email" placeholder="user@company.com" value={form.email} onChange={(value) => setForm((current) => ({ ...current, email: value }))} />
          <Field label="Full name" placeholder="User name" value={form.fullName} onChange={(value) => setForm((current) => ({ ...current, fullName: value }))} />
          <Field label="Password" placeholder="Minimum 6 characters" type="password" value={form.password} onChange={(value) => setForm((current) => ({ ...current, password: value }))} />
          <label className="field">
            <span>Role</span>
            <select value={form.role} onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}>
              <option value="BUYER">BUYER</option>
              <option value="CAPACITY_MANAGER">CAPACITY_MANAGER</option>
              <option value="SQD">SQD</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </label>
        </div>
        {message && <div className="form-success">{message}</div>}
        <div className="table-wrap">
          <table>
            <thead><tr><th>User</th><th>Role</th><th>Password</th><th>Actions</th></tr></thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td><strong>{user.email}</strong><br />{user.full_name}</td>
                  <td>
                    <select value={user.role} onChange={(event) => changeRole(user.id, event.target.value)}>
                      <option value="BUYER">BUYER</option>
                      <option value="CAPACITY_MANAGER">CAPACITY_MANAGER</option>
                      <option value="SQD">SQD</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                  </td>
                  <td>
                    <input className="table-input" type="password" placeholder="New password" value={passwords[user.id] ?? ""} onChange={(event) => setPasswords((current) => ({ ...current, [user.id]: event.target.value }))} />
                  </td>
                  <td>
                    <div className="button-row">
                      <button className="secondary-button" onClick={() => changePassword(user.id)}>Update password</button>
                      <button className="ghost-button danger-button" onClick={() => removeUser(user.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function DataManager({
  project,
  records,
  user,
  onSaved,
  onProjectDeleted,
}: {
  project: UIProject;
  records: UIRecord[];
  user: ApiUser;
  onSaved: (records: UIRecord[]) => void;
  onProjectDeleted: (projectId: string) => void;
}) {
  const [selectedPart, setSelectedPart] = useState("");
  const [form, setForm] = useState({ partNumber: "", apqpGrid: "", columnName: "", value: "" });
  const [logs, setLogs] = useState<ApiAuditLog[]>([]);
  const [message, setMessage] = useState("");
  const selectedRecord = records.find((record) => record.part === selectedPart);

  useEffect(() => {
    fetchAuditLogs().then(setLogs).catch(() => setLogs([]));
  }, []);

  useEffect(() => {
    if (!selectedRecord) return;
    setForm((current) => ({
      ...current,
      partNumber: selectedRecord.part,
      apqpGrid: selectedRecord.apqp === "N/A" ? "" : selectedRecord.apqp,
    }));
  }, [selectedRecord?.part]);

  async function refreshAll() {
    if (project.apiId) {
      const refreshed = await fetchRecords(project.apiId);
      onSaved(refreshed.map(mapApiRecord));
    }
    setLogs(await fetchAuditLogs().catch(() => []));
  }

  function directValues() {
    return form.columnName.trim() ? { [form.columnName.trim()]: form.value } : {};
  }

  async function addDirectRecord() {
    if (!project.apiId) return;
    setMessage("");
    try {
      await adminUpsertRecord(project.apiId, {
        part_number: form.partNumber,
        apqp_grid: form.apqpGrid,
        values: directValues(),
        updated_by: user.email,
      });
      await refreshAll();
      setMessage("Record added or updated directly in database.");
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to add record");
    }
  }

  async function updateDirectRecord() {
    if (!selectedRecord?.id) return;
    setMessage("");
    try {
      await adminUpdateRecord(selectedRecord.id, {
        part_number: form.partNumber,
        apqp_grid: form.apqpGrid,
        values: directValues(),
        updated_by: user.email,
      });
      await refreshAll();
      setMessage("Record updated directly in database.");
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to update record");
    }
  }

  async function deleteDirectRecord() {
    if (!selectedRecord?.id) return;
    if (!window.confirm(`Delete part ${selectedRecord.part} directly from database?`)) return;
    setMessage("");
    try {
      await adminDeleteRecord(selectedRecord.id, user.email);
      setSelectedPart("");
      await refreshAll();
      setMessage("Record deleted directly from database.");
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to delete record");
    }
  }

  async function resetProjectRecords() {
    if (!project.apiId) return;
    if (!window.confirm(`Reset all records for ${project.project} / ${project.partOfProject}?`)) return;
    setMessage("");
    try {
      const deleted = await adminResetProjectRecords(project.apiId, user.email);
      setSelectedPart("");
      await refreshAll();
      setMessage(`${deleted} records deleted from this CMF.`);
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to reset CMF");
    }
  }

  async function deleteCurrentProject() {
    if (!project.apiId) return;
    if (!window.confirm(`Delete CMF project ${project.project} / ${project.partOfProject}?`)) return;
    setMessage("");
    try {
      await deleteProject(project.apiId);
      onProjectDeleted(project.id);
      setMessage("Project deleted.");
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to delete project");
    }
  }

  return (
    <section className="page-grid">
      <div className="page-title">
        <div>
          <span className="eyebrow">Data Manager</span>
          <h1>Global Data Control</h1>
          <p>Admin has full direct database privileges for the selected CMF.</p>
        </div>
        <div className="button-row">
          <button className="primary-button" onClick={resetProjectRecords}>Reset CMF records</button>
          <button className="ghost-button danger-button" onClick={deleteCurrentProject}>Delete Project</button>
        </div>
      </div>
      <ImportStudio />
      <div className="panel form-panel">
        <PanelHeader title="Direct Database Editor" action={project.project} />
        <label className="field">
          <span>Select existing record</span>
          <PartNumberPicker records={records} value={selectedPart} onChange={setSelectedPart} placeholder="Type PN prefix, e.g. 9 or 95" allowEmpty />
        </label>
        <div className="form-grid three">
          <Field label="PART NUMBER" placeholder="Part number" value={form.partNumber} onChange={(value) => setForm((current) => ({ ...current, partNumber: value }))} />
          <Field label="APQP GRID" placeholder="APQP" value={form.apqpGrid} onChange={(value) => setForm((current) => ({ ...current, apqpGrid: value }))} />
          <Field label="Column Name" placeholder="Any CMF column" value={form.columnName} onChange={(value) => setForm((current) => ({ ...current, columnName: value }))} />
          <Field label="Value" placeholder="Direct DB value" value={form.value} onChange={(value) => setForm((current) => ({ ...current, value }))} />
        </div>
        <div className="button-row">
          <button className="primary-button" onClick={addDirectRecord}>Add / Upsert</button>
          <button className="secondary-button" onClick={updateDirectRecord} disabled={!selectedRecord}>Modify selected</button>
          <button className="ghost-button danger-button" onClick={deleteDirectRecord} disabled={!selectedRecord}>Delete selected</button>
        </div>
        {message && <div className={message.includes("Unable") ? "form-error" : "form-success"}>{message}</div>}
      </div>
      <div className="panel">
        <PanelHeader title="Audit Logs" action={`${logs.length} latest`} />
        <div className="table-wrap">
          <table>
            <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Project</th><th>New Value</th></tr></thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.timestamp}</td>
                  <td>{log.user_name}</td>
                  <td>{log.action}</td>
                  <td>{log.entity_type} #{log.entity_id}</td>
                  <td>{log.project_id}</td>
                  <td>{log.new_value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <DataGrid records={records} title="All Records Controlled by Admin" />
    </section>
  );
}

function Workspace({
  project,
  records,
  title,
  subtitle,
  role,
  section,
  createIfMissing,
  mustSelectExisting,
  sqdPartDataMode = false,
  canEdit,
  user,
  onSaved,
  embedded = false,
}: {
  project: UIProject;
  records: UIRecord[];
  title: string;
  subtitle: string;
  role: string;
  section: string;
  createIfMissing: boolean;
  mustSelectExisting: boolean;
  sqdPartDataMode?: boolean;
  canEdit: boolean;
  user: ApiUser;
  onSaved: (records: UIRecord[]) => void;
  embedded?: boolean;
}) {
  const [fields, setFields] = useState<string[]>(["PART NUMBER"]);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [partMode, setPartMode] = useState<"existing" | "new">(mustSelectExisting ? "existing" : "new");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [error, setError] = useState("");
  const [importData, setImportData] = useState<ParsedImportFile | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [importing, setImporting] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    if (!project.apiId) return;
    fetchEditableColumns(project.apiId, role, section)
      .then((columns) => {
        const next = ["PART NUMBER", ...columns.filter((column) => column !== "PART NUMBER")];
        setFields(Array.from(new Set(next)));
      })
      .catch(() => setFields(["PART NUMBER"]));
  }, [project.apiId, role, section]);

  function setValue(field: string, value: string) {
    setFormValues((current) => ({ ...current, [field]: value }));
  }

  function selectExistingPart(partNumber: string) {
    const record = records.find((item) => item.part === partNumber);
    setFormValues((current) => ({
      ...current,
      "PART NUMBER": partNumber,
      "APQP GRID": record?.apqp && record.apqp !== "N/A" ? record.apqp : current["APQP GRID"] ?? "",
    }));
  }

  async function loadImportFile(file: File) {
    if (!canEdit) {
      setError("Read-only: you are not assigned to this project.");
      return;
    }
    setError("");
    setNotice("");
    setSaveState("idle");
    try {
      const parsed = await parseImportFile({ filename: file.name, content_base64: await fileToBase64(file) });
      setImportData(parsed);
      setMapping(Object.fromEntries(fields.map((field) => [field, guessMappedColumn(field, parsed.columns)])));
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to read file");
      setSaveState("error");
    }
  }

  async function importMappedRows() {
    if (!project.apiId || !importData) return;
    if (!canEdit) {
      setError("Read-only: you are not assigned to this project.");
      return;
    }
    setImporting(true);
    setError("");
    setNotice("");
    let ok = 0;
    let failed = 0;
    for (const row of importData.rows) {
      const partColumn = mapping["PART NUMBER"];
      const partNumber = partColumn ? String(row[partColumn] ?? "").trim() : "";
      if (!partNumber) {
        failed += 1;
        continue;
      }
      const values = Object.fromEntries(
        fields
          .filter((field) => field !== "PART NUMBER" && field !== "APQP GRID" && mapping[field])
          .map((field) => [field, row[mapping[field]] ?? ""])
          .filter(([, value]) => String(value).trim())
      );
      try {
        await saveRoleRecord(project.apiId, {
          part_number: partNumber,
          apqp_grid: mapping["APQP GRID"] ? String(row[mapping["APQP GRID"]] ?? "") : undefined,
          values,
          role,
          section,
          create_if_missing: createIfMissing,
          updated_by: user.email,
          actor_email: user.email,
        });
        ok += 1;
      } catch {
        failed += 1;
      }
    }
    const refreshed = await fetchRecords(project.apiId);
    onSaved(refreshed.map(mapApiRecord));
    setImporting(false);
    setSaveState(failed ? "error" : "saved");
    if (failed) {
      setError(`${ok} imported, ${failed} skipped/errors`);
    } else {
      setNotice(`${ok} rows imported`);
    }
  }

  async function save() {
    if (!project.apiId) return;
    if (!canEdit) {
      setError("Read-only: you are not assigned to this project.");
      setSaveState("error");
      return;
    }
    setSaveState("saving");
    setError("");
    try {
      const values = Object.fromEntries(
        Object.entries(formValues).filter(([key, value]) => key !== "PART NUMBER" && key !== "APQP GRID" && String(value).trim())
      );
      await saveRoleRecord(project.apiId, {
        part_number: formValues["PART NUMBER"] ?? "",
        apqp_grid: formValues["APQP GRID"],
        values,
        role,
        section,
        create_if_missing: createIfMissing,
        updated_by: user.email,
        actor_email: user.email,
      });
      const refreshed = await fetchRecords(project.apiId);
      onSaved(refreshed.map(mapApiRecord));
      setSaveState("saved");
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to save record");
      setSaveState("error");
    }
  }

  return (
    <section className={embedded ? "" : "page-grid"}>
      <div className="page-title">
        <div>
          <span className="eyebrow">{role} owned data</span>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        <label className={`primary-button file-button ${!canEdit ? "disabled" : ""}`}>
          <FileUp size={18} />
          Import file
          <input type="file" disabled={!canEdit} accept=".xlsx,.xlsm,.csv,.tsv,.txt" onChange={(event) => event.target.files?.[0] && loadImportFile(event.target.files[0])} />
        </label>
      </div>
      {!canEdit && <div className="form-error">Read-only: you can view all projects and records, but you can only modify projects assigned to you.</div>}
      {importData && (
        <div className="panel">
          <PanelHeader title="Column Mapping" action={`${importData.total_rows} rows`} />
          <div className="mapping-grid">
            {fields.map((field) => (
              <div className="mapping-row" key={field}>
                <span>{field}</span>
                <ChevronDown size={16} />
                <select value={mapping[field] ?? ""} disabled={!canEdit} onChange={(event) => setMapping((current) => ({ ...current, [field]: event.target.value }))}>
                  <option value="">Skip</option>
                  {importData.columns.map((fileColumn) => <option key={fileColumn} value={fileColumn}>{fileColumn}</option>)}
                </select>
              </div>
            ))}
          </div>
          <div className="import-actions">
            <span>{importData.rows.length} preview rows loaded from file.</span>
            <button className="primary-button" onClick={importMappedRows} disabled={importing || !mapping["PART NUMBER"] || !canEdit}>
              {importing ? "Importing..." : "Import mapped rows"}
            </button>
          </div>
        </div>
      )}
      <div className="panel form-panel">
        <PanelHeader title="Manual Entry" action="Validated" />
        {sqdPartDataMode && (
          <div className="segmented">
            <button className={partMode === "existing" ? "active" : ""} onClick={() => setPartMode("existing")} disabled={!canEdit}>Complete existing Part Number</button>
            <button className={partMode === "new" ? "active" : ""} onClick={() => setPartMode("new")} disabled={!canEdit}>Create new SQD Part</button>
          </div>
        )}
        {(mustSelectExisting || partMode === "existing") && (
          <label className="field part-selector">
            <span>Select Part Number</span>
            <PartNumberPicker records={records} value={formValues["PART NUMBER"] ?? ""} onChange={selectExistingPart} placeholder="Type PN prefix, e.g. 9 or 95" />
          </label>
        )}
        <div className="form-grid three">
          {fields.map((field) => (
            <Field key={field} label={field} placeholder="Enter value" value={formValues[field] ?? ""} onChange={(value) => setValue(field, value)} disabled={!canEdit || (field === "PART NUMBER" && (mustSelectExisting || partMode === "existing"))} />
          ))}
        </div>
        {error && <div className="form-error">{error}</div>}
        {notice && <div className="form-success">{notice}</div>}
        {saveState === "saved" && <div className="form-success">Record saved in SQLite.</div>}
        <button className="primary-button full" onClick={save} disabled={saveState === "saving" || !canEdit}>
          {saveState === "saving" ? "Saving..." : "Save record"}
        </button>
      </div>
    </section>
  );

}

function ImportStudio() {
  const [parsed, setParsed] = useState<ParsedImportFile | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");

  async function loadFile(file: File) {
    try {
      const next = await parseImportFile({ filename: file.name, content_base64: await fileToBase64(file) });
      setParsed(next);
      setMapping(Object.fromEntries(cmfColumns.map((column) => [column, guessMappedColumn(column, next.columns)])));
      setMessage(`${next.total_rows} rows detected.`);
    } catch (event) {
      setMessage(event instanceof Error ? event.message : "Unable to read file");
    }
  }

  const availableColumns = parsed?.columns ?? fileColumns;

  return (
    <section className="page-grid">
      <div className="page-title">
        <div>
          <span className="eyebrow">Import studio</span>
          <h1>Column Mapping</h1>
          <p>CMF columns stay fixed; users select the matching column from the uploaded file.</p>
        </div>
        <label className="primary-button file-button">
          <UploadCloud size={18} />
          Upload file
          <input type="file" accept=".xlsx,.xlsm,.csv,.tsv,.txt" onChange={(event) => event.target.files?.[0] && loadFile(event.target.files[0])} />
        </label>
      </div>
      <div className="panel">
        <PanelHeader title="Mapping preview" action={parsed ? `${parsed.columns.length} file columns` : "Demo"} />
        {message && <div className={message.includes("Unable") || message.includes("Unsupported") ? "form-error" : "form-success"}>{message}</div>}
        <div className="mapping-grid">
          {cmfColumns.map((column, index) => (
            <div className="mapping-row" key={column}>
              <span>{column}</span>
              <ChevronDown size={16} />
              <select value={mapping[column] ?? fileColumns[index] ?? ""} onChange={(event) => setMapping((current) => ({ ...current, [column]: event.target.value }))}>
                <option value="">Skip</option>
                {availableColumns.map((fileColumn) => <option key={fileColumn} value={fileColumn}>{fileColumn}</option>)}
              </select>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function formatInteger(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

function formatCapacity(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

function formatBarValue(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

function formatPercentValue(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "0%";
  return `${Math.round(value * 100)}%`;
}

function coverageTone(value: unknown): Health | undefined {
  if (typeof value !== "number" || !Number.isFinite(value)) return undefined;
  if (value >= 1) return "G";
  if (value >= 0.9) return "O";
  return "R";
}

function riskRateTone(value: unknown): Health | undefined {
  if (typeof value !== "number" || !Number.isFinite(value)) return undefined;
  if (value === 0) return "G";
  if (value < 0.15) return "O";
  return "R";
}

function riskClass(value: unknown): string {
  const text = String(value ?? "").toLowerCase();
  if (text.includes("green")) return "risk-green";
  if (text.includes("orange")) return "risk-orange";
  if (text.includes("red")) return "risk-red";
  return "risk-unknown";
}

function formatDashboardCell(key: string, value: unknown): string {
  if (key === "coverage_rate" || key === "measured_coverage_rate") return formatPercentValue(value);
  if (["last_weekly_capacity_requested", "weekly_capacity_contracted", "weekly_capacity_measured", "capacity_gap", "measured_capacity_gap"].includes(key)) {
    return typeof value === "number" && Number.isFinite(value) ? formatCapacity(value) : "";
  }
  if (key === "priority") return value ? `P${value}` : "";
  return String(value ?? "");
}

function Metric({ label, value, detail, tone }: { label: string; value: string; detail: string; tone?: Health }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong className={tone ? `tone-${tone.toLowerCase()}` : ""}>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function PanelHeader({ title, action }: { title: string; action: string }) {
  return (
    <div className="panel-header">
      <h2>{title}</h2>
      <span className="panel-action">{action}</span>
    </div>
  );
}

function TimelineItem({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="timeline-item">
      <div className="timeline-dot" />
      <div>
        <strong>{title}</strong>
        <span>{detail}</span>
      </div>
    </div>
  );
}

function HealthPill({ value }: { value: Health | "" }) {
  if (!value) return <span className="empty-cell"></span>;
  return <span className={`health ${healthMeta[value].className}`}>{value}</span>;
}

function Field({
  label,
  placeholder,
  value,
  onChange,
  disabled = false,
  type = "text",
}: {
  label: string;
  placeholder: string;
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  type?: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} disabled={disabled} placeholder={placeholder} value={value} onChange={(event) => onChange?.(event.target.value)} />
    </label>
  );
}

function PartNumberPicker({
  records,
  value,
  onChange,
  placeholder,
  allowEmpty = false,
}: {
  records: UIRecord[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  allowEmpty?: boolean;
}) {
  const [query, setQuery] = useState(value);
  const normalized = query.trim().toLowerCase();
  const listId = useMemo(() => `pn-options-${Math.random().toString(36).slice(2)}`, []);
  const options = records
    .filter((record) => record.part)
    .filter((record) => !normalized || record.part.toLowerCase().startsWith(normalized))
    .slice(0, 80);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  return (
    <div className="pn-picker">
      <input
        value={query}
        list={listId}
        placeholder={placeholder}
        onChange={(event) => {
          setQuery(event.target.value);
          onChange(allowEmpty || event.target.value ? event.target.value : "");
        }}
      />
      <datalist id={listId}>
        {allowEmpty && <option value="">New record / no selection</option>}
        {options.map((record) => (
          <option key={record.part} value={record.part}>{record.part} / {record.apqp}</option>
        ))}
      </datalist>
    </div>
  );
}

export default App;
