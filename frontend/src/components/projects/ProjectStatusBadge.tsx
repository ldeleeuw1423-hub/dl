import React from "react";
import { Badge } from "@/components/ui/Badge";
import { getProjectStatusLabel } from "@/lib/utils";
import type { ProjectStatus } from "@/types";

interface ProjectStatusBadgeProps {
  status: ProjectStatus;
}

const statusVariant: Record<ProjectStatus, "success" | "warning" | "info" | "neutral"> = {
  active: "success",
  on_hold: "warning",
  completed: "info",
  cancelled: "neutral",
};

export function ProjectStatusBadge({ status }: ProjectStatusBadgeProps) {
  return (
    <Badge variant={statusVariant[status] ?? "neutral"}>
      {getProjectStatusLabel(status)}
    </Badge>
  );
}
