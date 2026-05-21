import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { formatNumber } from "@/lib/utils";
import type { Estimation } from "@/types";

interface HoursBreakdownProps {
  estimation: Estimation;
}

const HOUR_FIELDS = [
  { key: "hours_engineering", label: "Engineering", color: "#1e2540" },
  { key: "hours_pm", label: "Projectmanagement", color: "#3d5297" },
  { key: "hours_om", label: "Omgevingsmanagement", color: "#f59e0b" },
  { key: "hours_workprep", label: "Werkvoorbereiding", color: "#6b7280" },
  { key: "hours_execution", label: "Uitvoering", color: "#10b981" },
] as const;

export function HoursBreakdown({ estimation }: HoursBreakdownProps) {
  const data = HOUR_FIELDS.map((f) => ({
    name: f.label,
    hours: Number(estimation[f.key] ?? 0),
    color: f.color,
  })).filter((d) => d.hours > 0);

  const totalHours = data.reduce((sum, d) => sum + d.hours, 0);

  return (
    <div className="space-y-4">
      {/* Bar chart */}
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{ fontSize: 12, border: "1px solid #e5e7eb", borderRadius: 6 }}
              formatter={(value: number) => [`${formatNumber(value)} uur`, ""]}
            />
            <Bar dataKey="hours" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Table breakdown */}
      <div className="space-y-1.5">
        {data.map((item) => {
          const pct = totalHours > 0 ? (item.hours / totalHours) * 100 : 0;
          return (
            <div key={item.name} className="flex items-center gap-2 text-xs">
              <div
                className="w-2 h-2 rounded-sm shrink-0"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-gray-600 flex-1 truncate">{item.name}</span>
              <span className="text-gray-400 w-8 text-right">{Math.round(pct)}%</span>
              <span className="font-medium text-gray-800 w-16 text-right">
                {formatNumber(item.hours)} u
              </span>
            </div>
          );
        })}
        <div className="flex items-center gap-2 text-xs pt-1.5 border-t border-gray-100">
          <div className="w-2 h-2 shrink-0" />
          <span className="text-gray-800 font-semibold flex-1">Totaal</span>
          <span className="text-gray-400 w-8 text-right">100%</span>
          <span className="font-bold text-gray-900 w-16 text-right">{formatNumber(totalHours)} u</span>
        </div>
      </div>
    </div>
  );
}
