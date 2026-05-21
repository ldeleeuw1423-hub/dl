"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { PermitList } from "@/components/permits/PermitList";
import { PermitForm } from "@/components/permits/PermitForm";
import { PermitTimeline } from "@/components/permits/PermitTimeline";
import { useProject } from "@/hooks/useProjects";
import { api, getErrorMessage } from "@/lib/api";
import { Plus, Sparkles, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import type { Permit, PermitCreate } from "@/types";

export default function PermitsPage() {
  const { id } = useParams<{ id: string }>();
  const { project } = useProject(id);
  const [permits, setPermits] = useState<Permit[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [editPermit, setEditPermit] = useState<Permit | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [view, setView] = useState<"list" | "timeline">("list");

  const fetchPermits = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getPermits(id);
      setPermits(data);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchPermits(); }, [fetchPermits]);

  const handleCreate = async (data: PermitCreate) => {
    setFormLoading(true);
    try {
      const permit = await api.createPermit(id, data);
      setPermits((prev) => [...prev, permit]);
      setCreateOpen(false);
      toast.success("Vergunning toegevoegd");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setFormLoading(false);
    }
  };

  const handleEdit = async (data: PermitCreate) => {
    if (!editPermit) return;
    setFormLoading(true);
    try {
      const updated = await api.updatePermit(id, editPermit.id, data);
      setPermits((prev) => prev.map((p) => (p.id === editPermit.id ? updated : p)));
      setEditPermit(null);
      toast.success("Vergunning bijgewerkt");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (permitId: string) => {
    if (!confirm("Vergunning verwijderen?")) return;
    try {
      await api.deletePermit(id, permitId);
      setPermits((prev) => prev.filter((p) => p.id !== permitId));
      toast.success("Vergunning verwijderd");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const handleAutoDetect = async () => {
    setDetecting(true);
    try {
      const detected = await api.autoDetectPermits(id);
      const existingIds = new Set(permits.map((p) => p.id));
      const newPermits = detected.filter((p) => !existingIds.has(p.id));
      setPermits((prev) => [...prev, ...newPermits]);
      toast.success(`${detected.length} vergunningen gedetecteerd`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setDetecting(false);
    }
  };

  const approved = permits.filter((p) => p.status === "approved").length;
  const submitted = permits.filter((p) => p.status === "submitted").length;
  const required = permits.filter((p) => p.status === "required").length;

  return (
    <>
      <Header
        breadcrumb={[
          { label: "Projecten", href: "/projects" },
          { label: project?.name ?? "Project", href: `/projects/${id}` },
          { label: "Vergunningen" },
        ]}
      />
      <div className="page-container">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Vergunningenbeheer</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {permits.length} vergunningen — {approved} verleend, {submitted} ingediend, {required} vereist
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={<Sparkles className="h-3.5 w-3.5" />}
              loading={detecting}
              onClick={handleAutoDetect}
            >
              Auto-detect
            </Button>
            <Button
              size="sm"
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setCreateOpen(true)}
            >
              Toevoegen
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 text-navy-600 animate-spin" />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex gap-1 border border-gray-200 rounded-lg p-0.5 w-fit bg-gray-50">
              <button
                onClick={() => setView("list")}
                className={`px-3 py-1 text-xs rounded-md transition-all ${view === "list" ? "bg-white shadow-sm font-medium text-gray-900" : "text-gray-500"}`}
              >
                Tabel
              </button>
              <button
                onClick={() => setView("timeline")}
                className={`px-3 py-1 text-xs rounded-md transition-all ${view === "timeline" ? "bg-white shadow-sm font-medium text-gray-900" : "text-gray-500"}`}
              >
                Timeline
              </button>
            </div>

            {view === "list" ? (
              <Card padding="none">
                <PermitList
                  permits={permits}
                  onEdit={(p) => setEditPermit(p)}
                  onDelete={handleDelete}
                />
              </Card>
            ) : (
              <Card padding="md">
                <CardHeader title="Vergunningentimeline" subtitle="Chronologische volgorde" />
                <PermitTimeline permits={permits} />
              </Card>
            )}
          </div>
        )}
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Vergunning toevoegen" size="md">
        <PermitForm
          onSubmit={handleCreate}
          onCancel={() => setCreateOpen(false)}
          loading={formLoading}
        />
      </Modal>

      <Modal
        open={!!editPermit}
        onClose={() => setEditPermit(null)}
        title="Vergunning bewerken"
        size="md"
      >
        {editPermit && (
          <PermitForm
            defaultValues={editPermit}
            onSubmit={handleEdit}
            onCancel={() => setEditPermit(null)}
            loading={formLoading}
          />
        )}
      </Modal>
    </>
  );
}
