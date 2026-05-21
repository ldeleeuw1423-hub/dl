import React from "react";
import { formatDate, getDisciplineLabel } from "@/lib/utils";
import { ProjectStatusBadge } from "@/components/projects/ProjectStatusBadge";
import type { ProjectListItem } from "@/types";

interface ProjectTimelineProps {
  projects: ProjectListItem[];
}

export function ProjectTimeline({ projects }: ProjectTimelineProps) {
  const withDates = projects
    .filter((p) => p.start_date || p.end_date)
    .slice(0, 6);

  if (withDates.length === 0) {
    return (
      <div className="text-center py-4 text-sm text-gray-400">
        Geen projecten met datums gevonden
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {withDates.map((project) => (
        <div key={project.id} className="flex items-center gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <p className="text-xs font-medium text-gray-800 truncate">{project.name}</p>
              <ProjectStatusBadge status={project.status} />
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span>{getDisciplineLabel(project.discipline)}</span>
              {project.start_date && (
                <span>{formatDate(project.start_date)}</span>
              )}
              {project.end_date && (
                <>
                  <span className="text-gray-300">→</span>
                  <span>{formatDate(project.end_date)}</span>
                </>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
