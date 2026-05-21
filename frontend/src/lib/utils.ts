import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, parseISO, isValid } from "date-fns";
import { nl } from "date-fns/locale";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(
  amount: number | undefined | null,
  currency = "EUR",
  locale = "nl-NL"
): string {
  if (amount === undefined || amount === null) return "—";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatNumber(
  value: number | undefined | null,
  decimals = 0
): string {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("nl-NL", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatDate(
  dateStr: string | undefined | null,
  fmt = "dd-MM-yyyy"
): string {
  if (!dateStr) return "—";
  try {
    const date = parseISO(dateStr);
    if (!isValid(date)) return "—";
    return format(date, fmt, { locale: nl });
  } catch {
    return "—";
  }
}

export function formatDateTime(dateStr: string | undefined | null): string {
  return formatDate(dateStr, "dd-MM-yyyy HH:mm");
}

export function calculateTotalHours(estimation: {
  hours_engineering?: number | null;
  hours_pm?: number | null;
  hours_om?: number | null;
  hours_workprep?: number | null;
  hours_execution?: number | null;
}): number {
  return (
    (estimation.hours_engineering ?? 0) +
    (estimation.hours_pm ?? 0) +
    (estimation.hours_om ?? 0) +
    (estimation.hours_workprep ?? 0) +
    (estimation.hours_execution ?? 0)
  );
}

export function getRiskColor(score: number): string {
  if (score >= 16) return "risk-critical";
  if (score >= 10) return "risk-high";
  if (score >= 5) return "risk-medium";
  return "risk-low";
}

export function getRiskLabel(score: number): string {
  if (score >= 16) return "Kritiek";
  if (score >= 10) return "Hoog";
  if (score >= 5) return "Gemiddeld";
  return "Laag";
}

export function getPermitStatusColor(status: string): string {
  const map: Record<string, string> = {
    required: "text-gray-500 bg-gray-100",
    in_preparation: "text-blue-700 bg-blue-100",
    submitted: "text-amber-700 bg-amber-100",
    approved: "text-green-700 bg-green-100",
    rejected: "text-red-700 bg-red-100",
    not_required: "text-gray-400 bg-gray-50",
  };
  return map[status] ?? "text-gray-500 bg-gray-100";
}

export function getPermitStatusLabel(status: string): string {
  const map: Record<string, string> = {
    required: "Vereist",
    in_preparation: "In voorbereiding",
    submitted: "Ingediend",
    approved: "Verleend",
    rejected: "Geweigerd",
    not_required: "Niet vereist",
  };
  return map[status] ?? status;
}

export function getProjectStatusColor(status: string): string {
  const map: Record<string, string> = {
    active: "text-green-700 bg-green-100",
    on_hold: "text-amber-700 bg-amber-100",
    completed: "text-blue-700 bg-blue-100",
    cancelled: "text-red-700 bg-red-100",
  };
  return map[status] ?? "text-gray-500 bg-gray-100";
}

export function getProjectStatusLabel(status: string): string {
  const map: Record<string, string> = {
    active: "Actief",
    on_hold: "In de wacht",
    completed: "Afgerond",
    cancelled: "Geannuleerd",
  };
  return map[status] ?? status;
}

export function getDisciplineLabel(discipline: string): string {
  const map: Record<string, string> = {
    Gas: "Gas",
    Elektra: "Elektra",
    LS_MS: "LS/MS Kabel",
    Stations: "Stations",
  };
  return map[discipline] ?? discipline;
}

export function getPhaseLabel(phase: string): string {
  const map: Record<string, string> = {
    VO: "Voorlopig Ontwerp",
    DO: "Definitief Ontwerp",
    UO: "Uitvoeringsontwerp",
    Realisatie: "Realisatie",
  };
  return map[phase] ?? phase;
}

export function truncate(str: string, length = 80): string {
  if (!str) return "";
  return str.length > length ? str.slice(0, length) + "…" : str;
}

export function generateProjectNumber(): string {
  const year = new Date().getFullYear();
  const random = Math.floor(Math.random() * 9000) + 1000;
  return `INF-${year}-${random}`;
}
