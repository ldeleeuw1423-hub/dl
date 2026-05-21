import React from "react";
import { AlertTriangle, Shield, TrendingDown } from "lucide-react";

interface RiskSummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  total: number;
}

interface RiskOverviewProps {
  summary: RiskSummary;
}

export function RiskOverview({ summary }: RiskOverviewProps) {
  const bars = [
    { label: "Kritiek", count: summary.critical, color: "bg-red-500", textColor: "text-red-700" },
    { label: "Hoog", count: summary.high, color: "bg-orange-400", textColor: "text-orange-700" },
    { label: "Gemiddeld", count: summary.medium, color: "bg-amber-300", textColor: "text-amber-700" },
    { label: "Laag", count: summary.low, color: "bg-green-300", textColor: "text-green-700" },
  ];

  return (
    <div className="space-y-3">
      {bars.map((bar) => {
        const pct = summary.total > 0 ? (bar.count / summary.total) * 100 : 0;
        return (
          <div key={bar.label} className="flex items-center gap-2">
            <span className="text-xs text-gray-600 w-16 shrink-0">{bar.label}</span>
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${bar.color}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className={`text-xs font-semibold w-6 text-right ${bar.textColor}`}>
              {bar.count}
            </span>
          </div>
        );
      })}
      <div className="flex items-center gap-1.5 pt-1 text-xs text-gray-500">
        <Shield className="h-3.5 w-3.5" />
        <span>{summary.total} risico's totaal</span>
      </div>
    </div>
  );
}
