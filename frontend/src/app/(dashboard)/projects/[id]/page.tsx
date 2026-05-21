"use client";

import React, { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ProjectStatusBadge } from "@/components/projects/ProjectStatusBadge";
import { Modal } from "@/components/ui/Modal";
import { ProjectForm } from "@/components/projects/ProjectForm";
import { useProject } from "@/hooks/useProjects";
import {
  formatCurrency,
  formatDate,
  formatNumber,
  getDisciplineLabel,
  getPhaseLabel,
} from "@/lib/utils";
import {
  MapPin,
  Calendar,
  Building2,
  Pencil,
  AlertTriangle,
  FileText,
  BarChart2,
  Map,
  Loader2,
  TrendingUp,
  Clock,
} from "lucide-react";
import type { ProjectCreate } from "@/types";

const tabItems = [
  { id: "overview", label: "Overzicht", href: "" },
  { id: "estimation", label: "Raming", href: "/estimation" },
  { id: "risks", label: "Risico's", href: "/risks" },
  { id: "permits", label: "Vergunningen", href: "/permits" },
  { id: "gis", label: "GIS / Kaart", href: "/gis" },
];

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { project, loading, error, updateProject } = useProject(id);
  const [editOpen, setEditOpen] = useState(false);
  const [editLoading, setEditLoading] = useState(false);

  const handleEdit = async (data: ProjectCreate) => {
    setEditLoading(true);
    try {
      await updateProject(data);
      setEditOpen(false);
    } finally {
      setEditLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-6 w-6 text-navy-600 animate-spin" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-red-500">
        {error ?? "Project niet gevonden"}
      </div>
    );
  }

  const tabs = tabItems.map((t) => ({
    ...t,
    fullHref: `/projects/${id}${t.href}`,
  }));

  return (
    <>
      <Header
        breadcrumb={[
          { label: "Projecten", href: "/projects" },
          { label: project.name },
        ]}
      />
      <div className="page-container">
        {/* Project header */}
        <div className="flex items-start justify-between mb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <p className="text-xs font-mono text-gray-400">{project.project_number}</p>
              <ProjectStatusBadge status={project.status} />
              <Badge variant="default">{getDisciplineLabel(project.discipline)}</Badge>
              <Badge variant="neutral">{getPhaseLabel(project.phase)}</Badge>
            </div>
            <h1 className="text-xl font-bold text-gray-900">{project.name}</h1>
            {project.client && (
              <p className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
                <Building2 className="h-3.5 w-3.5" />
                {project.client}
              </p>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            icon={<Pencil className="h-3.5 w-3.5" />}
            onClick={() => setEditOpen(true)}
          >
            Bewerken
          </Button>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          <Card padding="sm">
            <p className="text-2xs text-gray-500 uppercase tracking-wide mb-1">Budget geraamd</p>
            <p className="text-base font-bold text-navy-900">
              {project.budget_estimated ? formatCurrency(Number(project.budget_estimated)) : "—"}
            </p>
          </Card>
          <Card padding="sm">
            <p className="text-2xs text-gray-500 uppercase tracking-wide mb-1">Budget actueel</p>
            <p className="text-base font-bold text-gray-700">
              {project.budget_actual ? formatCurrency(Number(project.budget_actual)) : "—"}
            </p>
          </Card>
          <Card padding="sm">
            <p className="text-2xs text-gray-500 uppercase tracking-wide mb-1">Uren geraamd</p>
            <p className="text-base font-bold text-navy-900">
              {project.hours_estimated ? `${formatNumber(Number(project.hours_estimated))} u` : "—"}
            </p>
          </Card>
          <Card padding="sm">
            <p className="text-2xs text-gray-500 uppercase tracking-wide mb-1">Startdatum</p>
            <p className="text-base font-bold text-gray-700">
              {formatDate(project.start_date)}
            </p>
          </Card>
        </div>

        {/* Tab navigation */}
        <div className="border-b border-gray-200 mb-5">
          <nav className="flex gap-0">
            {tabs.map((tab) => (
              <Link
                key={tab.id}
                href={tab.fullHref}
                className="tab-button tab-button-inactive"
              >
                {tab.label}
              </Link>
            ))}
          </nav>
        </div>

        {/* Overview content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card padding="md">
            <CardHeader title="Projectdetails" />
            <div className="space-y-2.5">
              {project.location && (
                <div className="flex gap-2 text-sm">
                  <MapPin className="h-4 w-4 text-gray-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-2xs text-gray-500 mb-0.5">Locatie</p>
                    <p className="text-gray-800">{project.location}</p>
                  </div>
                </div>
              )}
              <div className="flex gap-2 text-sm">
                <Calendar className="h-4 w-4 text-gray-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-2xs text-gray-500 mb-0.5">Looptijd</p>
                  <p className="text-gray-800">
                    {formatDate(project.start_date)} — {formatDate(project.end_date)}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          <Card padding="md">
            <CardHeader title="Projectbeschrijving" />
            {project.scope_description ? (
              <p className="text-sm text-gray-700 leading-relaxed">{project.scope_description}</p>
            ) : (
              <p className="text-sm text-gray-400 italic">Geen beschrijving opgegeven</p>
            )}
          </Card>

          <Card padding="md" className="lg:col-span-2">
            <CardHeader title="Snelle acties" />
            <div className="flex flex-wrap gap-2">
              <Link href={`/projects/${id}/estimation`}>
                <Button variant="outline" size="sm" icon={<BarChart2 className="h-3.5 w-3.5" />}>
                  Raming genereren
                </Button>
              </Link>
              <Link href={`/projects/${id}/risks`}>
                <Button variant="outline" size="sm" icon={<AlertTriangle className="h-3.5 w-3.5" />}>
                  Risico&apos;s beheren
                </Button>
              </Link>
              <Link href={`/projects/${id}/permits`}>
                <Button variant="outline" size="sm" icon={<FileText className="h-3.5 w-3.5" />}>
                  Vergunningen
                </Button>
              </Link>
              <Link href={`/projects/${id}/gis`}>
                <Button variant="outline" size="sm" icon={<Map className="h-3.5 w-3.5" />}>
                  GIS / Kaart
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>

      {/* Edit modal */}
      <Modal open={editOpen} onClose={() => setEditOpen(false)} title="Project bewerken" size="lg">
        <ProjectForm
          defaultValues={{
            project_number: project.project_number,
            name: project.name,
            client: project.client,
            location: project.location,
            phase: project.phase,
            discipline: project.discipline,
            status: project.status,
            scope_description: project.scope_description,
            budget_estimated: project.budget_estimated
              ? Number(project.budget_estimated)
              : undefined,
          }}
          onSubmit={handleEdit}
          loading={editLoading}
          submitLabel="Wijzigingen opslaan"
        />
      </Modal>
    </>
  );
}
