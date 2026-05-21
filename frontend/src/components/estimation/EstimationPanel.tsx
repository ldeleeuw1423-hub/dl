"use client";

import React, { useState } from "react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { ConfidenceScore } from "./ConfidenceScore";
import { HoursBreakdown } from "./HoursBreakdown";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency, formatDateTime, formatNumber } from "@/lib/utils";
import { Sparkles, RefreshCw, Info } from "lucide-react";
import type { Estimation, EstimationGenerateRequest, Project } from "@/types";

interface EstimationPanelProps {
  project: Project;
  estimation: Estimation | null;
  generating: boolean;
  onGenerate: (req: EstimationGenerateRequest) => Promise<void>;
}

const locationTypeOptions = [
  { value: "urban", label: "Stedelijk" },
  { value: "rural", label: "Landelijk" },
  { value: "mixed", label: "Gemengd" },
];

export function EstimationPanel({
  project,
  estimation,
  generating,
  onGenerate,
}: EstimationPanelProps) {
  const [showForm, setShowForm] = useState(!estimation);
  const [params, setParams] = useState<EstimationGenerateRequest>({
    trace_length_m: undefined,
    num_crossings: undefined,
    num_permits: undefined,
    num_stakeholders: undefined,
    location_type: "urban",
  });

  const handleGenerate = async () => {
    await onGenerate(params);
    setShowForm(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Generate panel */}
      <Card padding="md" className="lg:col-span-1">
        <CardHeader
          title="Raming genereren"
          subtitle="Voer parameters in voor een AI-raming"
          actions={
            estimation && (
              <button
                onClick={() => setShowForm(!showForm)}
                className="text-xs text-navy-600 hover:text-navy-800"
              >
                {showForm ? "Verbergen" : "Herberekenen"}
              </button>
            )
          }
        />

        {showForm && (
          <div className="space-y-3">
            <Input
              label="Tracelengte (m)"
              type="number"
              min={0}
              placeholder="bijv. 750"
              value={params.trace_length_m ?? ""}
              onChange={(e) =>
                setParams((p) => ({
                  ...p,
                  trace_length_m: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
            />
            <Input
              label="Aantal kruisingen"
              type="number"
              min={0}
              placeholder="bijv. 5"
              value={params.num_crossings ?? ""}
              onChange={(e) =>
                setParams((p) => ({
                  ...p,
                  num_crossings: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
            />
            <Input
              label="Aantal vergunningen"
              type="number"
              min={0}
              placeholder="bijv. 3"
              value={params.num_permits ?? ""}
              onChange={(e) =>
                setParams((p) => ({
                  ...p,
                  num_permits: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
            />
            <Input
              label="Stakeholders"
              type="number"
              min={0}
              placeholder="bijv. 8"
              value={params.num_stakeholders ?? ""}
              onChange={(e) =>
                setParams((p) => ({
                  ...p,
                  num_stakeholders: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
            />
            <Select
              label="Locatietype"
              options={locationTypeOptions}
              value={params.location_type ?? "urban"}
              onChange={(e) =>
                setParams((p) => ({ ...p, location_type: e.target.value }))
              }
            />
            <Button
              className="w-full"
              onClick={handleGenerate}
              loading={generating}
              icon={<Sparkles className="h-4 w-4" />}
            >
              {estimation ? "Herbereken raming" : "Genereer raming"}
            </Button>
          </div>
        )}

        {estimation && !showForm && (
          <div className="space-y-3">
            <ConfidenceScore score={Number(estimation.confidence_score ?? 0)} />
            <div className="flex items-center gap-2">
              <Badge variant={estimation.methodology?.includes("AI") ? "info" : "neutral"} size="sm">
                {estimation.methodology ?? "Regelgebaseerd"}
              </Badge>
              <span className="text-2xs text-gray-400">
                v{estimation.version} — {formatDateTime(estimation.created_at)}
              </span>
            </div>
            {estimation.reasoning && (
              <div className="flex gap-2 p-2.5 bg-blue-50 rounded-md text-xs text-blue-800">
                <Info className="h-3.5 w-3.5 mt-0.5 shrink-0 text-blue-500" />
                <p>{estimation.reasoning}</p>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Results */}
      {estimation && (
        <>
          <Card padding="md" className="lg:col-span-2">
            <CardHeader title="Urenverdeling" />
            <HoursBreakdown estimation={estimation} />
          </Card>

          <Card padding="md" className="lg:col-span-1">
            <CardHeader title="Kostenoverzicht" />
            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">Materiaalkosten</span>
                <span className="font-medium">{formatCurrency(Number(estimation.cost_materials))}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">Totale kosten</span>
                <span className="font-semibold text-navy-800">
                  {formatCurrency(Number(estimation.cost_total))}
                </span>
              </div>
              <div className="pt-2 border-t border-gray-100">
                <p className="text-2xs text-gray-500 mb-1.5">Bandbreedte</p>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-gray-500">Laag (-15%)</span>
                  <span className="font-medium text-green-700">
                    {formatCurrency(Number(estimation.bandwidth_low))}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs mt-1">
                  <span className="text-gray-500">Hoog (+25%)</span>
                  <span className="font-medium text-amber-700">
                    {formatCurrency(Number(estimation.bandwidth_high))}
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {estimation.similar_projects && estimation.similar_projects.length > 0 && (
            <Card padding="md" className="lg:col-span-2">
              <CardHeader title="Vergelijkbare projecten" />
              <div className="space-y-2">
                {estimation.similar_projects.map((sp: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 p-2 rounded bg-gray-50 text-xs"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800 truncate">{sp.name}</p>
                      <p className="text-gray-500">{sp.reference_number}</p>
                    </div>
                    <div className="text-right shrink-0">
                      {sp.cost_total && (
                        <p className="font-medium text-gray-700">
                          {formatCurrency(sp.cost_total)}
                        </p>
                      )}
                      <p className="text-gray-400">
                        {Math.round((sp.similarity_score ?? 0) * 100)}% match
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
