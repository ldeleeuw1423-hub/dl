"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { formatCurrency } from "@/lib/utils";
import type { ProjectListItem } from "@/types";

interface BudgetChartProps {
  projects: ProjectListItem[];
}

export function BudgetChart({ projects }: BudgetChartProps) {
  const data = projects
    .filter((p) => p.budget_estimated != null || p.budget_actual != null)
    .slice(0, 8)
    .map((p) => ({
      name: p.name.length > 15 ? p.name.slice(0, 15) + "…" : p.name,
      geraamd: Number(p.budget_estimated ?? 0),
      actueel: Number(p.budget_actual ?? 0),
    }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-sm text-gray-400">
        Nog geen budgetgegevens beschikbaar
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 10, fill: "#9ca3af" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: "#9ca3af" }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={{ fontSize: 11, border: "1px solid #e5e7eb", borderRadius: 6 }}
          formatter={(value: number, name: string) => [formatCurrency(value), name]}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Bar dataKey="geraamd" name="Geraamd" fill="#1e2540" radius={[3, 3, 0, 0]} />
        <Bar dataKey="actueel" name="Actueel" fill="#f59e0b" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
