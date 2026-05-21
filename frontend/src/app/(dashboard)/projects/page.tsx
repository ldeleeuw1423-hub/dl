"use client";

import React, { useState } from "react";
import { Header } from "@/components/layout/Header";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useProjects } from "@/hooks/useProjects";
import { Plus, Search, Filter, Loader2 } from "lucide-react";
import Link from "next/link";

const statusOptions = [
  { value: "", label: "Alle statussen" },
  { value: "active", label: "Actief" },
  { value: "on_hold", label: "In de wacht" },
  { value: "completed", label: "Afgerond" },
  { value: "cancelled", label: "Geannuleerd" },
];

const disciplineOptions = [
  { value: "", label: "Alle disciplines" },
  { value: "Gas", label: "Gas" },
  { value: "Elektra", label: "Elektra" },
  { value: "LS_MS", label: "LS/MS Kabel" },
  { value: "Stations", label: "Stations" },
];

export default function ProjectsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [discipline, setDiscipline] = useState("");

  const { projects, loading, error } = useProjects({
    search: search || undefined,
    status: status || undefined,
    discipline: discipline || undefined,
  });

  return (
    <>
      <Header title="Projecten" />
      <div className="page-container">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Projecten</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {loading ? "Laden..." : `${projects.length} projecten gevonden`}
            </p>
          </div>
          <Link href="/projects/new">
            <Button icon={<Plus className="h-4 w-4" />}>
              Nieuw project
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-5">
          <div className="flex-1 max-w-xs">
            <Input
              placeholder="Zoek project, nummer, klant..."
              leftIcon={<Search className="h-3.5 w-3.5" />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select
            options={statusOptions}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-40"
          />
          <Select
            options={disciplineOptions}
            value={discipline}
            onChange={(e) => setDiscipline(e.target.value)}
            className="w-40"
          />
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 text-navy-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-12 text-red-500 text-sm">{error}</div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-sm text-gray-400 mb-4">Geen projecten gevonden</p>
            <Link href="/projects/new">
              <Button variant="outline" icon={<Plus className="h-4 w-4" />}>
                Eerste project aanmaken
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
