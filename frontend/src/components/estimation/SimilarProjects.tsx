"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronRight, Clock, Euro, Ruler, Users } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import type { HistoricalProject } from "@/types";

interface SimilarProjectsProps {
  projects: HistoricalProject[];
  loading?: boolean;
}

const DISCIPLINE_LABELS: Record<string, string> = {
  Gas: "Gas",
  Elektra: "Elektra",
  LS_MS: "LS/MS",
  Stations: "Stations",
};

const LOCATION_LABELS: Record<string, string> = {
  urban: "Stedelijk",
  rural: "Landelijk",
  mixed: "Gemengd",
};

function similarityColour(score: number): string {
  if (score >= 0.85) return "text-green-700 bg-green-50 border-green-200";
  if (score >= 0.65) return "text-amber-700 bg-amber-50 border-amber-200";
  return "text-gray-600 bg-gray-100 border-gray-200";
}

function formatHours(hours: number | undefined): string {
  if (hours === undefined || hours === null) return "—";
  return `${Math.round(hours)} u`;
}

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

interface ProjectCardProps {
  project: HistoricalProject;
  rank: number;
}

function SimilarProjectCard({ project, rank }: ProjectCardProps) {
  const [expanded, setExpanded] = useState(false);
  const score = project.similarity_score ?? 0;
  const pct = Math.round(score * 100);

  const totalHours =
    (project.hours_engineering ?? 0) +
    (project.hours_pm ?? 0) +
    (project.hours_om ?? 0) +
    (project.hours_workprep ?? 0);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header row — always visible */}
      <button
        className="w-full flex items-center justify-between px-3 py-2.5 bg-white hover:bg-gray-50 transition-colors text-left"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-mono text-gray-400 w-5 shrink-0">#{rank}</span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">{project.name}</p>
            <p className="text-2xs text-gray-400">{project.reference_number}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          {/* Similarity badge */}
          <span
            className={cn(
              "text-xs font-semibold px-1.5 py-0.5 rounded border",
              similarityColour(score)
            )}
          >
            {pct}% overeenkomst
          </span>
          <Badge variant="default" className="text-2xs">
            {DISCIPLINE_LABELS[project.discipline] ?? project.discipline}
          </Badge>
          <Badge variant="neutral" className="text-2xs">
            {LOCATION_LABELS[project.location_type] ?? project.location_type}
          </Badge>
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </button>

      {/* Key metrics — always visible below header */}
      <div className="grid grid-cols-3 gap-0 border-t border-gray-100">
        <div className="flex items-center gap-1.5 px-3 py-2 border-r border-gray-100">
          <Clock className="h-3.5 w-3.5 text-gray-400 shrink-0" />
          <div>
            <p className="text-2xs text-gray-400">Totaal uren</p>
            <p className="text-xs font-medium text-gray-700">{formatHours(totalHours)}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-2 border-r border-gray-100">
          <Euro className="h-3.5 w-3.5 text-gray-400 shrink-0" />
          <div>
            <p className="text-2xs text-gray-400">Totale kosten</p>
            <p className="text-xs font-medium text-gray-700">{formatCurrency(project.cost_total)}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-2">
          <Ruler className="h-3.5 w-3.5 text-gray-400 shrink-0" />
          <div>
            <p className="text-2xs text-gray-400">Tracelengte</p>
            <p className="text-xs font-medium text-gray-700">
              {project.trace_length_m ? `${Math.round(project.trace_length_m)} m` : "—"}
            </p>
          </div>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-gray-100 px-3 py-3 bg-gray-50">
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs">
            <div>
              <span className="text-gray-400">Looptijd</span>
              <span className="ml-2 font-medium text-gray-700">
                {project.duration_days ? `${project.duration_days} dagen` : "—"}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Kruisingen</span>
              <span className="ml-2 font-medium text-gray-700">
                {project.num_crossings ?? "—"}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Vergunningen</span>
              <span className="ml-2 font-medium text-gray-700">
                {project.num_permits ?? "—"}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Stakeholders</span>
              <span className="ml-2 font-medium text-gray-700">
                {project.num_stakeholders ?? "—"}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Engineering</span>
              <span className="ml-2 font-medium text-gray-700">
                {formatHours(project.hours_engineering)}
              </span>
            </div>
            <div>
              <span className="text-gray-400">PM</span>
              <span className="ml-2 font-medium text-gray-700">
                {formatHours(project.hours_pm)}
              </span>
            </div>
            <div>
              <span className="text-gray-400">OM</span>
              <span className="ml-2 font-medium text-gray-700">
                {formatHours(project.hours_om)}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Werkvoorbereiding</span>
              <span className="ml-2 font-medium text-gray-700">
                {formatHours(project.hours_workprep)}
              </span>
            </div>
            {project.risks_count !== undefined && (
              <div>
                <span className="text-gray-400">Risico&apos;s</span>
                <span className="ml-2 font-medium text-gray-700">{project.risks_count}</span>
              </div>
            )}
            {project.num_revisions !== undefined && (
              <div>
                <span className="text-gray-400">Revisies</span>
                <span className="ml-2 font-medium text-gray-700">{project.num_revisions}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Card list showing the top similar historical projects with similarity scores.
 * Integrates with the pgvector cosine similarity search.
 */
export function SimilarProjects({ projects, loading = false }: SimilarProjectsProps) {
  if (loading) {
    return (
      <Card padding="md">
        <CardHeader title="Vergelijkbare projecten" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      </Card>
    );
  }

  if (projects.length === 0) {
    return (
      <Card padding="md">
        <CardHeader title="Vergelijkbare projecten" />
        <p className="text-sm text-gray-400 italic">
          Geen vergelijkbare historische projecten gevonden.
        </p>
      </Card>
    );
  }

  return (
    <Card padding="md">
      <CardHeader
        title="Vergelijkbare projecten"
        subtitle={`Top ${projects.length} op basis van cosinus-similariteit`}
      />
      <div className="space-y-2 mt-2">
        {projects.map((project, idx) => (
          <SimilarProjectCard key={project.id} project={project} rank={idx + 1} />
        ))}
      </div>
    </Card>
  );
}
