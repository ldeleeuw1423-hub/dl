import React from "react";
import { cn } from "@/lib/utils";

interface ConfidenceScoreProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-600";
  if (score >= 65) return "text-amber-600";
  return "text-red-600";
}

function getBarColor(score: number): string {
  if (score >= 80) return "bg-green-500";
  if (score >= 65) return "bg-amber-500";
  return "bg-red-500";
}

function getScoreLabel(score: number): string {
  if (score >= 80) return "Hoog";
  if (score >= 65) return "Gemiddeld";
  return "Laag";
}

export function ConfidenceScore({ score, size = "md" }: ConfidenceScoreProps) {
  const pct = Math.min(100, Math.max(0, score));
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className={cn("font-semibold", size === "lg" ? "text-2xl" : "text-lg", getScoreColor(pct))}>
          {Math.round(pct)}%
        </span>
        <span className={cn("text-xs font-medium", getScoreColor(pct))}>
          {getScoreLabel(pct)} betrouwbaarheid
        </span>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700", getBarColor(pct))}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
