"use client";

import { useState, useEffect, useCallback } from "react";
import { api, getErrorMessage } from "@/lib/api";
import { Risk, RiskCreate } from "@/types";
import toast from "react-hot-toast";

export function useRisks(projectId: string) {
  const [risks, setRisks] = useState<Risk[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRisks = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRisks(projectId);
      setRisks(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchRisks();
  }, [fetchRisks]);

  const createRisk = async (payload: RiskCreate) => {
    try {
      const risk = await api.createRisk(projectId, payload);
      setRisks((prev) => [...prev, risk].sort((a, b) => b.score - a.score));
      toast.success("Risico toegevoegd");
      return risk;
    } catch (err) {
      toast.error(getErrorMessage(err));
      throw err;
    }
  };

  const updateRisk = async (riskId: string, payload: Partial<RiskCreate>) => {
    try {
      const updated = await api.updateRisk(projectId, riskId, payload);
      setRisks((prev) =>
        prev.map((r) => (r.id === riskId ? updated : r)).sort((a, b) => b.score - a.score)
      );
      toast.success("Risico bijgewerkt");
      return updated;
    } catch (err) {
      toast.error(getErrorMessage(err));
      throw err;
    }
  };

  const deleteRisk = async (riskId: string) => {
    try {
      await api.deleteRisk(projectId, riskId);
      setRisks((prev) => prev.filter((r) => r.id !== riskId));
      toast.success("Risico verwijderd");
    } catch (err) {
      toast.error(getErrorMessage(err));
      throw err;
    }
  };

  const autoDetect = async () => {
    setDetecting(true);
    try {
      const detected = await api.autoDetectRisks(projectId);
      setRisks((prev) => {
        const existingIds = new Set(prev.map((r) => r.id));
        const newRisks = detected.filter((r) => !existingIds.has(r.id));
        return [...prev, ...newRisks].sort((a, b) => b.score - a.score);
      });
      toast.success(`${detected.length} risico's gedetecteerd`);
      return detected;
    } catch (err) {
      toast.error(getErrorMessage(err));
      throw err;
    } finally {
      setDetecting(false);
    }
  };

  return {
    risks,
    loading,
    detecting,
    error,
    createRisk,
    updateRisk,
    deleteRisk,
    autoDetect,
    refetch: fetchRisks,
  };
}
