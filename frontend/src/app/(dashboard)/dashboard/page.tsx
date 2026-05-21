"use client";

import React from "react";
import { Header } from "@/components/layout/Header";
import { KPICard } from "@/components/dashboard/KPICard";
import { BudgetChart } from "@/components/dashboard/BudgetChart";
import { RiskOverview } from "@/components/dashboard/RiskOverview";
import { ProjectTimeline } from "@/components/dashboard/ProjectTimeline";
import { Card, CardHeader } from "@/components/ui/Card";
import { useProjects } from "@/hooks/useProjects";
import { formatCurrency, formatNumber } from "@/lib/utils";
import {
  FolderKanban,
  AlertTriangle,
  FileText,
  TrendingUp,
  Plus,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function DashboardPage() {
  const { projects, loading } = useProjects();

  const activeProjects = projects.filter((p) => p.status === "active");
  const totalBudget = projects.reduce((sum, p) => sum + Number(p.budget_estimated ?? 0), 0);
  const totalRisks = projects.reduce((sum, p) => sum + (p.risks_count ?? 0), 0);
  const totalPermits = projects.reduce((sum, p) => sum + (p.permits_count ?? 0), 0);

  const riskSummary = {
    total: totalRisks,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };

  return (
    <>
      <Header title="Dashboard" />
      <div className="page-container">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Overzicht</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {loading ? "Laden..." : `${projects.length} projecten in de database`}
            </p>
          </div>
          <Link href="/projects/new">
            <Button icon={<Plus className="h-4 w-4" />}>
              Nieuw project
            </Button>
          </Link>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KPICard
            title="Actieve projecten"
            value={loading ? "—" : activeProjects.length}
            subtitle={`van ${projects.length} totaal`}
            icon={<FolderKanban className="h-4 w-4" />}
            color="default"
          />
          <KPICard
            title="Totaal budget"
            value={loading ? "—" : formatCurrency(totalBudget)}
            subtitle="Geraamd"
            icon={<TrendingUp className="h-4 w-4" />}
            color="green"
          />
          <KPICard
            title="Open risico's"
            value={loading ? "—" : totalRisks}
            subtitle="Alle projecten"
            icon={<AlertTriangle className="h-4 w-4" />}
            color="amber"
          />
          <KPICard
            title="Vergunningen"
            value={loading ? "—" : totalPermits}
            subtitle="In behandeling"
            icon={<FileText className="h-4 w-4" />}
            color="blue"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
          <Card padding="md" className="lg:col-span-2">
            <CardHeader
              title="Budgetvergelijking"
              subtitle="Geraamd vs. actueel per project"
            />
            <BudgetChart projects={projects} />
          </Card>

          <Card padding="md">
            <CardHeader title="Risico-overzicht" subtitle="Alle actieve projecten" />
            <RiskOverview summary={riskSummary} />
          </Card>
        </div>

        {/* Timeline */}
        <Card padding="md">
          <CardHeader
            title="Project timeline"
            subtitle="Lopende en geplande projecten"
            actions={
              <Link href="/projects">
                <button className="text-xs text-navy-600 hover:text-navy-800">
                  Alle projecten →
                </button>
              </Link>
            }
          />
          <ProjectTimeline projects={projects} />
        </Card>
      </div>
    </>
  );
}
