"use client";

import React, { useState } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { api, getErrorMessage } from "@/lib/api";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils";

export type ExportFormat = "excel" | "pdf";

interface ExportButtonProps {
  projectId: string;
  format: ExportFormat;
  /** Optional extra CSS classes */
  className?: string;
}

const FORMAT_CONFIG: Record<
  ExportFormat,
  { label: string; mimeType: string; extension: string }
> = {
  excel: {
    label: "Export Excel",
    mimeType:
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    extension: "xlsx",
  },
  pdf: {
    label: "Export PDF",
    mimeType: "application/pdf",
    extension: "pdf",
  },
};

/**
 * Reusable export button.
 * Downloads the file directly in the browser using a Blob URL so the JWT
 * authentication header is forwarded correctly.
 */
export function ExportButton({ projectId, format, className }: ExportButtonProps) {
  const [loading, setLoading] = useState(false);
  const { label, mimeType, extension } = FORMAT_CONFIG[format];

  const handleClick = async () => {
    setLoading(true);
    try {
      const blob =
        format === "excel"
          ? await api.downloadExcel(projectId)
          : await api.downloadPdf(projectId);

      const url = URL.createObjectURL(new Blob([blob], { type: mimeType }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `project_${projectId}.${extension}`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);

      toast.success(`${label} klaar`);
    } catch (err) {
      toast.error(`Export mislukt: ${getErrorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      loading={loading}
      icon={<Download className="h-3.5 w-3.5" />}
      onClick={handleClick}
      className={cn(className)}
    >
      {label}
    </Button>
  );
}
