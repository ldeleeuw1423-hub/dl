import React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { ProjectStatusBadge } from "./ProjectStatusBadge";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency, formatDate, getDisciplineLabel, getPhaseLabel } from "@/lib/utils";
import { AlertTriangle, FileText, MapPin, Calendar } from "lucide-react";
import type { ProjectListItem } from "@/types";

interface ProjectCardProps {
  project: ProjectListItem;
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`}>
      <Card
        className="hover:shadow-card-hover hover:border-navy-200 transition-all duration-200 cursor-pointer"
        padding="md"
      >
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="min-w-0">
            <p className="text-2xs text-gray-400 font-mono mb-0.5">{project.project_number}</p>
            <h3 className="text-sm font-semibold text-gray-900 truncate">{project.name}</h3>
            {project.client && (
              <p className="text-xs text-gray-500 truncate">{project.client}</p>
            )}
          </div>
          <div className="shrink-0">
            <ProjectStatusBadge status={project.status} />
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5 mb-3">
          <Badge variant="default" size="sm">
            {getDisciplineLabel(project.discipline)}
          </Badge>
          <Badge variant="neutral" size="sm">
            {getPhaseLabel(project.phase)}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-gray-600 mb-3">
          {project.location && (
            <div className="flex items-center gap-1 col-span-2 truncate">
              <MapPin className="h-3 w-3 text-gray-400 shrink-0" />
              <span className="truncate">{project.location}</span>
            </div>
          )}
          {project.start_date && (
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3 text-gray-400 shrink-0" />
              <span>{formatDate(project.start_date)}</span>
            </div>
          )}
          {project.budget_estimated != null && (
            <div className="text-right font-medium text-gray-800">
              {formatCurrency(project.budget_estimated)}
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 pt-3 border-t border-gray-100 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3 text-amber-500" />
            <span>{project.risks_count} risico{project.risks_count !== 1 ? "s" : ""}</span>
          </div>
          <div className="flex items-center gap-1">
            <FileText className="h-3 w-3 text-blue-500" />
            <span>{project.permits_count} vergunning{project.permits_count !== 1 ? "en" : ""}</span>
          </div>
        </div>
      </Card>
    </Link>
  );
}
