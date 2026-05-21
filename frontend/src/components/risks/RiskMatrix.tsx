"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import type { Risk } from "@/types";

interface RiskMatrixProps {
  risks: Risk[];
  onSelectRisk?: (risk: Risk) => void;
}

const PROBABILITY_LABELS = ["Zeldzaam", "Onwaarschijnlijk", "Mogelijk", "Waarschijnlijk", "Bijna zeker"];
const IMPACT_LABELS = ["Verwaarloosbaar", "Gering", "Matig", "Ernstig", "Catastrofaal"];

function getCellColor(p: number, i: number): string {
  const score = p * i;
  if (score >= 16) return "bg-red-500";
  if (score >= 10) return "bg-orange-400";
  if (score >= 5) return "bg-amber-300";
  if (score >= 3) return "bg-yellow-200";
  return "bg-green-100";
}

function getCellTextColor(p: number, i: number): string {
  const score = p * i;
  if (score >= 10) return "text-white";
  return "text-gray-700";
}

export function RiskMatrix({ risks, onSelectRisk }: RiskMatrixProps) {
  const [hoveredCell, setHoveredCell] = useState<string | null>(null);

  const getRisksInCell = (p: number, i: number): Risk[] =>
    risks.filter((r) => r.probability === p && r.impact === i);

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[500px]">
        {/* Matrix header - Impact axis */}
        <div className="flex mb-1 ml-24">
          <div className="flex-1 text-center text-xs font-semibold text-gray-600 mb-1">
            Impact →
          </div>
        </div>
        <div className="flex mb-1 ml-24">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex-1 text-center">
              <div className="text-xs font-medium text-gray-600">{i}</div>
              <div className="text-2xs text-gray-400 leading-tight">{IMPACT_LABELS[i - 1]}</div>
            </div>
          ))}
        </div>

        <div className="flex gap-0">
          {/* Probability axis label */}
          <div className="flex flex-col justify-center w-6 mr-1">
            <div
              className="text-xs font-semibold text-gray-600 text-center"
              style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
            >
              Kans ↑
            </div>
          </div>

          {/* P labels */}
          <div className="flex flex-col w-16 shrink-0">
            {[5, 4, 3, 2, 1].map((p) => (
              <div key={p} className="flex-1 flex items-center justify-end pr-2">
                <div className="text-right">
                  <div className="text-xs font-medium text-gray-600">{p}</div>
                  <div className="text-2xs text-gray-400 leading-tight">{PROBABILITY_LABELS[p - 1]?.slice(0, 8)}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Grid cells */}
          <div className="flex-1">
            {[5, 4, 3, 2, 1].map((p) => (
              <div key={p} className="flex">
                {[1, 2, 3, 4, 5].map((i) => {
                  const cellKey = `${p}-${i}`;
                  const cellRisks = getRisksInCell(p, i);
                  const isHovered = hoveredCell === cellKey;
                  return (
                    <div
                      key={i}
                      className={cn(
                        "flex-1 h-14 border border-white/50 flex items-center justify-center cursor-default",
                        "transition-all duration-150",
                        getCellColor(p, i),
                        isHovered && "brightness-90 scale-[0.98]",
                        cellRisks.length > 0 && "cursor-pointer"
                      )}
                      onMouseEnter={() => setHoveredCell(cellKey)}
                      onMouseLeave={() => setHoveredCell(null)}
                      title={`Kans ${p}, Impact ${i}: score ${p * i}`}
                    >
                      {cellRisks.length > 0 && (
                        <div className="flex flex-wrap gap-0.5 p-1 justify-center">
                          {cellRisks.slice(0, 3).map((r) => (
                            <button
                              key={r.id}
                              onClick={() => onSelectRisk?.(r)}
                              className={cn(
                                "w-5 h-5 rounded-full text-2xs font-bold flex items-center justify-center",
                                "bg-white/30 hover:bg-white/50 transition-colors",
                                getCellTextColor(p, i)
                              )}
                              title={r.description}
                            >
                              {cellRisks.indexOf(r) + 1}
                            </button>
                          ))}
                          {cellRisks.length > 3 && (
                            <span className={cn("text-2xs font-bold", getCellTextColor(p, i))}>
                              +{cellRisks.length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 mt-3 ml-24 text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-green-100 border border-gray-200" />
            <span>Laag (1-2)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-yellow-200 border border-gray-200" />
            <span>Beperkt (3-4)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-amber-300 border border-gray-200" />
            <span>Gemiddeld (5-9)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-orange-400" />
            <span>Hoog (10-15)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm bg-red-500" />
            <span>Kritiek (16-25)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
