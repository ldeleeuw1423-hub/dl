"use client";

import React from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { EstimationPanel } from "@/components/estimation/EstimationPanel";
import { useProject } from "@/hooks/useProjects";
import { useEstimation } from "@/hooks/useEstimation";
import { Loader2 } from "lucide-react";

export default function EstimationPage() {
  const { id } = useParams<{ id: string }>();
  const { project, loading: projectLoading } = useProject(id);
  const { currentEstimation, generating, generateEstimation, loading: estLoading } = useEstimation(id);

  if (projectLoading || estLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-6 w-6 text-navy-600 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return <div className="flex-1 flex items-center justify-center text-red-500">Project niet gevonden</div>;
  }

  return (
    <>
      <Header
        breadcrumb={[
          { label: "Projecten", href: "/projects" },
          { label: project.name, href: `/projects/${id}` },
          { label: "Raming" },
        ]}
      />
      <div className="page-container">
        <div className="mb-5">
          <h1 className="text-lg font-bold text-gray-900">Projectraming</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            AI-ondersteunde uren- en kostenraming voor {project.name}
          </p>
        </div>

        <EstimationPanel
          project={project}
          estimation={currentEstimation}
          generating={generating}
          onGenerate={generateEstimation}
        />
      </div>
    </>
  );
}
