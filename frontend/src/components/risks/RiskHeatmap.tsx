import React from "react";
import { Badge } from "@/components/ui/Badge";
import { getRiskLabel } from "@/lib/utils";
import type { Risk } from "@/types";

interface RiskHeatmapProps {
  risks: Risk[];
}

export function RiskHeatmap({ risks }: RiskHeatmapProps) {
  const critical = risks.filter((r) => r.score >= 16);
  const high = risks.filter((r) => r.score >= 10 && r.score < 16);
  const medium = risks.filter((r) => r.score >= 5 && r.score < 10);
  const low = risks.filter((r) => r.score < 5);

  const groups = [
    { label: "Kritiek", risks: critical, variant: "danger" as const, bgClass: "bg-red-50 border-red-200" },
    { label: "Hoog", risks: high, variant: "warning" as const, bgClass: "bg-orange-50 border-orange-200" },
    { label: "Gemiddeld", risks: medium, variant: "warning" as const, bgClass: "bg-amber-50 border-amber-200" },
    { label: "Laag", risks: low, variant: "success" as const, bgClass: "bg-green-50 border-green-200" },
  ];

  return (
    <div className="space-y-3">
      {groups.map((group) => (
        <div key={group.label} className={`rounded-lg border p-3 ${group.bgClass}`}>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant={group.variant}>{group.label}</Badge>
            <span className="text-xs text-gray-500">{group.risks.length} risico{group.risks.length !== 1 ? "'s" : ""}</span>
          </div>
          {group.risks.length === 0 ? (
            <p className="text-xs text-gray-400 italic">Geen risico's in deze categorie</p>
          ) : (
            <ul className="space-y-1">
              {group.risks.map((r) => (
                <li key={r.id} className="text-xs text-gray-700 flex items-start gap-1.5">
                  <span className="font-bold text-gray-500 shrink-0">P{r.probability}×I{r.impact}={r.score}</span>
                  <span className="truncate">{r.description}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}
