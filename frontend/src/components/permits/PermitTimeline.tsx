import React from "react";
import { formatDate, getPermitStatusLabel } from "@/lib/utils";
import { CheckCircle2, Clock, AlertCircle, XCircle, Circle } from "lucide-react";
import type { Permit, PermitStatus } from "@/types";

interface PermitTimelineProps {
  permits: Permit[];
}

const statusIcon: Record<PermitStatus, React.ReactNode> = {
  required: <Circle className="h-4 w-4 text-gray-400" />,
  in_preparation: <Clock className="h-4 w-4 text-blue-500" />,
  submitted: <Clock className="h-4 w-4 text-amber-500" />,
  approved: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  rejected: <XCircle className="h-4 w-4 text-red-500" />,
  not_required: <CheckCircle2 className="h-4 w-4 text-gray-300" />,
};

const statusBorderColor: Record<PermitStatus, string> = {
  required: "border-gray-200",
  in_preparation: "border-blue-200",
  submitted: "border-amber-300",
  approved: "border-green-300",
  rejected: "border-red-300",
  not_required: "border-gray-100",
};

export function PermitTimeline({ permits }: PermitTimelineProps) {
  if (permits.length === 0) {
    return (
      <div className="text-center py-6 text-sm text-gray-400">
        Geen vergunningen geregistreerd
      </div>
    );
  }

  const sorted = [...permits].sort((a, b) => {
    const aDate = a.expected_approval ?? a.submission_date ?? "";
    const bDate = b.expected_approval ?? b.submission_date ?? "";
    return aDate.localeCompare(bDate);
  });

  return (
    <div className="space-y-3">
      {sorted.map((permit, idx) => (
        <div
          key={permit.id}
          className={`relative flex gap-3 p-3 rounded-lg border ${statusBorderColor[permit.status as PermitStatus] ?? "border-gray-200"} bg-white`}
        >
          <div className="shrink-0 mt-0.5">
            {statusIcon[permit.status as PermitStatus] ?? <Circle className="h-4 w-4 text-gray-400" />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{permit.permit_type}</p>
                <p className="text-xs text-gray-500 capitalize">
                  {permit.authority} — {getPermitStatusLabel(permit.status)}
                </p>
              </div>
              {permit.delay_probability != null && permit.delay_probability >= 30 && (
                <div className="flex items-center gap-1 text-xs text-amber-600 shrink-0">
                  <AlertCircle className="h-3 w-3" />
                  <span>{permit.delay_probability}%</span>
                </div>
              )}
            </div>
            <div className="flex gap-4 mt-1.5 text-xs text-gray-500">
              {permit.submission_date && (
                <span>Indienen: {formatDate(permit.submission_date)}</span>
              )}
              {permit.expected_approval && (
                <span>Verwacht: {formatDate(permit.expected_approval)}</span>
              )}
              {permit.actual_approval && (
                <span className="text-green-600">Verleend: {formatDate(permit.actual_approval)}</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
