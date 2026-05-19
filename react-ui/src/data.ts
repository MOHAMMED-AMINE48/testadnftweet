import {
  BarChart3,
  Boxes,
  ClipboardCheck,
  Database,
  Factory,
  FileSpreadsheet,
  Gauge,
  LayoutDashboard,
  PackagePlus,
  ShieldCheck,
  Users,
} from "lucide-react";

export type Role = "Capacity Manager" | "Buyer" | "SQD" | "Admin";
export type Health = "G" | "O" | "R";

export const navigation = [
  { id: "dashboard", label: "Command Center", icon: LayoutDashboard },
  { id: "projects", label: "Projects", icon: Factory },
  { id: "data", label: "All CMF Data", icon: Database },
  { id: "buyer", label: "Buyer Workspace", icon: PackagePlus },
  { id: "capacity", label: "Capacity", icon: Gauge },
  { id: "sqd", label: "SQD Quality", icon: ShieldCheck },
  { id: "imports", label: "Imports", icon: FileSpreadsheet },
] as const;

export type ViewId = (typeof navigation)[number]["id"];

export const projects = [
  {
    id: "CMP-EV9-BATT",
    project: "CMP EV9",
    partOfProject: "Battery Cooling",
    capacityManager: "capacity_manager",
    supplier: "Novatech Systems",
    buyer: "buyer_amina",
    sqd: "sqd_youssef",
    status: "Active",
    records: 286,
    completion: 82,
    capacityHealth: "G" as Health,
    catHealth: "O" as Health,
    updated: "Today 10:24",
  },
  {
    id: "STLA-M-TRIM",
    project: "STLA Medium",
    partOfProject: "Interior Trim",
    capacityManager: "capacity_manager",
    supplier: "Atlas Components",
    buyer: "buyer_sara",
    sqd: "sqd_omar",
    status: "Active",
    records: 148,
    completion: 64,
    capacityHealth: "O" as Health,
    catHealth: "G" as Health,
    updated: "Yesterday",
  },
  {
    id: "K9-THERMAL",
    project: "K9",
    partOfProject: "Thermal Module",
    capacityManager: "capacity_manager",
    supplier: "Maghreb Mobility",
    buyer: "buyer_karim",
    sqd: "sqd_nadia",
    status: "Paused",
    records: 94,
    completion: 41,
    capacityHealth: "R" as Health,
    catHealth: "O" as Health,
    updated: "May 16",
  },
];

export const records = [
  {
    part: "PN-AC-100-01",
    apqp: "APQP-2401",
    supplier: "Novatech Systems",
    useCase: "CarryOver adapted",
    contracted: 2400,
    requested: 2150,
    measured: 2210,
    catType: "Run at rate",
    cat: "G" as Health,
    gor: "G" as Health,
    owner: "Buyer + SQD",
  },
  {
    part: "PN-MOT-5K-02",
    apqp: "APQP-2408",
    supplier: "Atlas Components",
    useCase: "New tooling",
    contracted: 1200,
    requested: 1460,
    measured: 1180,
    catType: "Industrial trial",
    cat: "O" as Health,
    gor: "O" as Health,
    owner: "Capacity",
  },
  {
    part: "PN-SENS-PRESS-04",
    apqp: "APQP-2419",
    supplier: "Maghreb Mobility",
    useCase: "New part",
    contracted: 900,
    requested: 1360,
    measured: 760,
    catType: "Supplier evidence",
    cat: "R" as Health,
    gor: "R" as Health,
    owner: "SQD",
  },
  {
    part: "PN-VALVE-DIR-05",
    apqp: "APQP-2422",
    supplier: "Novatech Systems",
    useCase: "CarryOver",
    contracted: 3200,
    requested: 2780,
    measured: 2890,
    catType: "CAT2",
    cat: "G" as Health,
    gor: "G" as Health,
    owner: "Buyer",
  },
];

export const sections = [
  { label: "PART DATA", value: 94, icon: Boxes },
  { label: "Capacity Sizing", value: 71, icon: BarChart3 },
  { label: "CAT Quality", value: 58, icon: ClipboardCheck },
  { label: "Assignments", value: 88, icon: Users },
];

export const cmfColumns = [
  "PART NUMBER",
  "APQP GRID",
  "SUPPLIER NAME",
  "USE CASES",
  "WEEKLY CAPACITY CONTRACTED (Parts/Week)",
  "LAST WEEKLY CAPACITY REQUESTED",
  "CAT1/2/3 TYPE",
  "CAT REALISED DATE (YYCWxx)",
  "WEEKLY CAPACITY MEASURED",
  "Comments",
];

export const fileColumns = [
  "PN",
  "APQP Code",
  "Vendor",
  "Use case",
  "Contracted cap",
  "Need peak",
  "CAT method",
  "CAT done CW",
  "Measured output",
  "Notes",
];
