"use client";

import { useState, useEffect, useCallback } from "react";
import { api, getErrorMessage } from "@/lib/api";
import { Estimation, EstimationGenerateRequest } from "@/types";
import toast from "react-hot-toast";

export function useEstimation(projectId: string) {
  const [estimations, setEstimations] = useState<Estimation[]>([]);
  const [currentEstimation, setCurrentEstimation] = useState<Estimation | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEstimations = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getEstimations(projectId);
      setEstimations(data);
      setCurrentEstimation(data.find((e) => e.is_current) ?? data[0] ?? null);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchEstimations();
  }, [fetchEstimations]);

  const generateEstimation = async (request: EstimationGenerateRequest) => {
    setGenerating(true);
    try {
      const estimation = await api.generateEstimation(projectId, request);
      setEstimations((prev) => [estimation, ...prev.map((e) => ({ ...e, is_current: false }))]);
      setCurrentEstimation(estimation);
      toast.success("Raming gegenereerd");
      return estimation;
    } catch (err) {
      toast.error(getErrorMessage(err));
      throw err;
    } finally {
      setGenerating(false);
    }
  };

  return {
    estimations,
    currentEstimation,
    loading,
    generating,
    error,
    generateEstimation,
    refetch: fetchEstimations,
  };
}
