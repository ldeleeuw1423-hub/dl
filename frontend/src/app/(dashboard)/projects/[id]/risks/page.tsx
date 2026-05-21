"use client";

import React, { useState } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { RiskMatrix } from "@/components/risks/RiskMatrix";
import { RiskHeatmap } from "@/components/risks/RiskHeatmap";
import { RiskForm } from "@/components/risks/RiskForm";
import { Table, TableHead, TableBody, Th, Td, Tr } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { useProject } from "@/hooks/useProjects";
import { useRisks } from "@/hooks/useRisks";
import { formatDate } from "@/lib/utils";
import { Plus, Sparkles, Pencil, Trash2, Loader2 } from "lucide-react";
import type { Risk, RiskCreate } from "@/types";

const categoryVariant: Record<string, any> = {
  Technisch: "info",
  Planning: "warning",
  Financieel: "danger",
  Omgeving: "success",
  Vergunning: "warning",
  Stakeholder: "neutral",
  Overig: "neutral",
};

const statusLabel: Record<string, string> = {
  open: "Open",
  mitigated: "Gemitigeerd",
  accepted: "Geaccepteerd",
  closed: "Gesloten",
};

export default function RisksPage() {
  const { id } = useParams<{ id: string }>();
  const { project } = useProject(id);
  const { risks, loading, detecting, createRisk, updateRisk, deleteRisk, autoDetect } = useRisks(id);
  const [createOpen, setCreateOpen] = useState(false);
  const [editRisk, setEditRisk] = useState<Risk | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [selectedRisk, setSelectedRisk] = useState<Risk | null>(null);
  const [view, setView] = useState<"matrix" | "list">("matrix");

  const handleCreate = async (data: RiskCreate) => {
    setFormLoading(true);
    try {
      await createRisk(data);
      setCreateOpen(false);
    } finally {
      setFormLoading(false);
    }
  };

  const handleEdit = async (data: RiskCreate) => {
    if (!editRisk) return;
    setFormLoading(true);
    try {
      await updateRisk(editRisk.id, data);
      setEditRisk(null);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (riskId: string) => {
    if (confirm("Risico verwijderen?")) {
      await deleteRisk(riskId);
    }
  };

  return (
    <>
      <Header
        breadcrumb={[
          { label: "Projecten", href: "/projects" },
          { label: project?.name ?? "Project", href: `/projects/${id}` },
          { label: "Risico's" },
        ]}
      />
      <div className="page-container">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Risicobeheer</h1>
            <p className="text-xs text-gray-500 mt-0.5">RISMAN-methodiek — {risks.length} risico&apos;s</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={<Sparkles className="h-3.5 w-3.5" />}
              loading={detecting}
              onClick={autoDetect}
            >
              Auto-detect
            </Button>
            <Button
              size="sm"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setCreateOpen(true)}
            >
              Risico toevoegen
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 text-navy-600 animate-spin" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* View toggle */}
            <div className="flex gap-1 border border-gray-200 rounded-lg p-0.5 w-fit bg-gray-50">
              <button
                onClick={() => setView("matrix")}
                className={`px-3 py-1 text-xs rounded-md transition-all ${view === "matrix" ? "bg-white shadow-sm font-medium text-gray-900" : "text-gray-500"}`}
              >
                Matrix
              </button>
              <button
                onClick={() => setView("list")}
                className={`px-3 py-1 text-xs rounded-md transition-all ${view === "list" ? "bg-white shadow-sm font-medium text-gray-900" : "text-gray-500"}`}
              >
                Lijst
              </button>
            </div>

            {view === "matrix" ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <Card padding="md" className="lg:col-span-2">
                  <CardHeader title="Risicomatrix (RISMAN)" subtitle="5×5 kans/impact matrix" />
                  <RiskMatrix risks={risks} onSelectRisk={setSelectedRisk} />
                </Card>
                <Card padding="md">
                  <CardHeader title="Risico-heatmap" />
                  <RiskHeatmap risks={risks} />
                </Card>
              </div>
            ) : (
              <Card padding="none">
                <Table>
                  <TableHead>
                    <tr>
                      <Th>Beschrijving</Th>
                      <Th>Categorie</Th>
                      <Th align="center">K</Th>
                      <Th align="center">I</Th>
                      <Th align="center">Score</Th>
                      <Th>Status</Th>
                      <Th>Eigenaar</Th>
                      <Th>Deadline</Th>
                      <Th />
                    </tr>
                  </TableHead>
                  <TableBody>
                    {risks.map((risk) => (
                      <Tr key={risk.id}>
                        <Td>
                          <div className="max-w-xs">
                            <p className="font-medium text-gray-900 text-xs leading-snug line-clamp-2">
                              {risk.description}
                            </p>
                            {risk.auto_detected && (
                              <span className="text-2xs text-blue-500">Auto</span>
                            )}
                          </div>
                        </Td>
                        <Td>
                          <Badge variant={categoryVariant[risk.category] ?? "neutral"} size="sm">
                            {risk.category}
                          </Badge>
                        </Td>
                        <Td align="center">{risk.probability}</Td>
                        <Td align="center">{risk.impact}</Td>
                        <Td align="center">
                          <span
                            className={`font-bold text-sm ${
                              risk.score >= 16
                                ? "text-red-600"
                                : risk.score >= 10
                                ? "text-orange-600"
                                : risk.score >= 5
                                ? "text-amber-600"
                                : "text-green-600"
                            }`}
                          >
                            {risk.score}
                          </span>
                        </Td>
                        <Td>
                          <span className="text-xs text-gray-600">
                            {statusLabel[risk.status] ?? risk.status}
                          </span>
                        </Td>
                        <Td>{risk.owner ?? "—"}</Td>
                        <Td>{formatDate(risk.deadline)}</Td>
                        <Td>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="xs"
                              icon={<Pencil className="h-3 w-3" />}
                              onClick={() => setEditRisk(risk)}
                            />
                            <Button
                              variant="ghost"
                              size="xs"
                              icon={<Trash2 className="h-3 w-3" />}
                              className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              onClick={() => handleDelete(risk.id)}
                            />
                          </div>
                        </Td>
                      </Tr>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            )}
          </div>
        )}
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Risico toevoegen" size="md">
        <RiskForm
          onSubmit={handleCreate}
          onCancel={() => setCreateOpen(false)}
          loading={formLoading}
        />
      </Modal>

      <Modal
        open={!!editRisk}
        onClose={() => setEditRisk(null)}
        title="Risico bewerken"
        size="md"
      >
        {editRisk && (
          <RiskForm
            defaultValues={editRisk}
            onSubmit={handleEdit}
            onCancel={() => setEditRisk(null)}
            loading={formLoading}
          />
        )}
      </Modal>

      <Modal
        open={!!selectedRisk}
        onClose={() => setSelectedRisk(null)}
        title="Risico details"
        size="md"
      >
        {selectedRisk && (
          <div className="space-y-3 text-sm">
            <p className="font-medium text-gray-900">{selectedRisk.description}</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="text-gray-500">Kans × Impact</p>
                <p className="font-bold text-lg">
                  {selectedRisk.probability} × {selectedRisk.impact} = {selectedRisk.score}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Categorie</p>
                <p className="font-medium">{selectedRisk.category}</p>
              </div>
            </div>
            {selectedRisk.mitigation_measure && (
              <div className="p-2.5 bg-blue-50 rounded text-xs text-blue-800">
                <p className="font-medium mb-0.5">Maatregel</p>
                <p>{selectedRisk.mitigation_measure}</p>
              </div>
            )}
            {selectedRisk.owner && (
              <p className="text-xs text-gray-600">Eigenaar: {selectedRisk.owner}</p>
            )}
          </div>
        )}
      </Modal>
    </>
  );
}
