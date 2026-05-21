"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader } from "@/components/ui/Card";
import { Table, TableHead, TableBody, Th, Td, Tr } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { api, getErrorMessage } from "@/lib/api";
import { formatCurrency, formatNumber, getDisciplineLabel } from "@/lib/utils";
import { Loader2, Database } from "lucide-react";
import toast from "react-hot-toast";
import type { HistoricalProject } from "@/types";

const disciplineOptions = [
  { value: "", label: "Alle disciplines" },
  { value: "Gas", label: "Gas" },
  { value: "Elektra", label: "Elektra" },
  { value: "LS_MS", label: "LS/MS Kabel" },
  { value: "Stations", label: "Stations" },
];

const locationTypeOptions = [
  { value: "", label: "Alle locatietypen" },
  { value: "urban", label: "Stedelijk" },
  { value: "rural", label: "Landelijk" },
  { value: "mixed", label: "Gemengd" },
];

const locationTypeLabel: Record<string, string> = {
  urban: "Stedelijk",
  rural: "Landelijk",
  mixed: "Gemengd",
};

export default function HistoricalPage() {
  const [projects, setProjects] = useState<HistoricalProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [discipline, setDiscipline] = useState("");
  const [locationType, setLocationType] = useState("");

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const data = await api.getHistoricalProjects({
          discipline: discipline || undefined,
          location_type: locationType || undefined,
          limit: 100,
        });
        setProjects(data);
      } catch (err) {
        toast.error(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [discipline, locationType]);

  const totalHours = (p: HistoricalProject) =>
    (p.hours_engineering ?? 0) +
    (p.hours_pm ?? 0) +
    (p.hours_om ?? 0) +
    (p.hours_workprep ?? 0);

  return (
    <>
      <Header title="Historische data" />
      <div className="page-container">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Historische projectdata</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Referentieprojecten voor ramingen en vergelijkingen
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Database className="h-4 w-4" />
            <span>{projects.length} projecten</span>
          </div>
        </div>

        <div className="flex gap-3 mb-4">
          <Select
            options={disciplineOptions}
            value={discipline}
            onChange={(e) => setDiscipline(e.target.value)}
            className="w-40"
          />
          <Select
            options={locationTypeOptions}
            value={locationType}
            onChange={(e) => setLocationType(e.target.value)}
            className="w-44"
          />
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 text-navy-600 animate-spin" />
          </div>
        ) : projects.length === 0 ? (
          <Card padding="md">
            <div className="text-center py-8">
              <Database className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-400">Geen historische projecten gevonden</p>
              <p className="text-xs text-gray-400 mt-1">
                Historische data wordt gebruikt door de AI voor betere ramingen
              </p>
            </div>
          </Card>
        ) : (
          <Card padding="none">
            <Table>
              <TableHead>
                <tr>
                  <Th>Referentie</Th>
                  <Th>Naam</Th>
                  <Th>Discipline</Th>
                  <Th>Locatietype</Th>
                  <Th align="right">Tracé (m)</Th>
                  <Th align="right">Totaal uren</Th>
                  <Th align="right">Totale kosten</Th>
                  <Th align="right">Doorlooptijd</Th>
                  <Th align="center">Risico&apos;s</Th>
                </tr>
              </TableHead>
              <TableBody>
                {projects.map((p) => (
                  <Tr key={p.id}>
                    <Td>
                      <code className="text-2xs text-gray-500 font-mono">
                        {p.reference_number}
                      </code>
                    </Td>
                    <Td>
                      <p className="font-medium text-gray-900 text-xs">{p.name}</p>
                    </Td>
                    <Td>
                      <Badge variant="default" size="sm">
                        {getDisciplineLabel(p.discipline)}
                      </Badge>
                    </Td>
                    <Td>
                      <span className="text-xs text-gray-600">
                        {locationTypeLabel[p.location_type] ?? p.location_type}
                      </span>
                    </Td>
                    <Td align="right">
                      {p.trace_length_m ? formatNumber(Number(p.trace_length_m)) : "—"}
                    </Td>
                    <Td align="right">
                      <span className="font-medium">
                        {formatNumber(totalHours(p))} u
                      </span>
                    </Td>
                    <Td align="right">
                      {p.cost_total ? formatCurrency(Number(p.cost_total)) : "—"}
                    </Td>
                    <Td align="right">
                      {p.duration_days ? `${p.duration_days} d` : "—"}
                    </Td>
                    <Td align="center">
                      <span
                        className={`text-xs font-medium ${
                          (p.risks_count ?? 0) >= 10
                            ? "text-red-600"
                            : (p.risks_count ?? 0) >= 5
                            ? "text-amber-600"
                            : "text-green-600"
                        }`}
                      >
                        {p.risks_count ?? 0}
                      </span>
                    </Td>
                  </Tr>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </div>
    </>
  );
}
