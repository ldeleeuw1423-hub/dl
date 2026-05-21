"use client";

import { useState, useEffect, useCallback } from "react";
import { api, getErrorMessage } from "@/lib/api";
import { Project, ProjectCreate, ProjectListItem } from "@/types";
import toast from "react-hot-toast";

export function useProjects(filters?: {
  status?: string;
  discipline?: string;
  search?: string;
}) {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getProjects(filters);
      setProjects(data);
    } catch (err) {
      const msg = getErrorMessage(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [filters?.status, filters?.discipline, filters?.search]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return { projects, loading, error, refetch: fetchProjects };
}

export function useProject(id: string) {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProject = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getProject(id);
      setProject(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  const updateProject = async (payload: Partial<ProjectCreate>) => {
    if (!id) return;
    try {
      const updated = await api.updateProject(id, payload);
      setProject(updated);
      toast.success("Project bijgewerkt");
      return updated;
    } catch (err) {
      toast.error(getErrorMessage(err));
      throw err;
    }
  };

  return { project, loading, error, refetch: fetchProject, updateProject };
}

export function useCreateProject() {
  const [loading, setLoading] = useState(false);

  const createProject = async (payload: ProjectCreate): Promise<Project | null> => {
    setLoading(true);
    try {
      const project = await api.createProject(payload);
      toast.success("Project aangemaakt");
      return project;
    } catch (err) {
      toast.error(getErrorMessage(err));
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { createProject, loading };
}
