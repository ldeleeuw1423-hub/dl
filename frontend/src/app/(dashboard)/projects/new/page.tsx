"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { ProjectForm } from "@/components/projects/ProjectForm";
import { useCreateProject } from "@/hooks/useProjects";
import type { ProjectCreate } from "@/types";

export default function NewProjectPage() {
  const router = useRouter();
  const { createProject, loading } = useCreateProject();

  const handleSubmit = async (data: ProjectCreate) => {
    const project = await createProject(data);
    if (project) {
      router.push(`/projects/${project.id}`);
    }
  };

  return (
    <>
      <Header
        breadcrumb={[
          { label: "Projecten", href: "/projects" },
          { label: "Nieuw project" },
        ]}
      />
      <div className="page-container max-w-2xl">
        <h1 className="text-lg font-bold text-gray-900 mb-5">Nieuw project aanmaken</h1>
        <Card padding="lg">
          <ProjectForm onSubmit={handleSubmit} loading={loading} submitLabel="Project aanmaken" />
        </Card>
      </div>
    </>
  );
}
