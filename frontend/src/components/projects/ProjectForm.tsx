"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { generateProjectNumber } from "@/lib/utils";
import type { ProjectCreate, ProjectDiscipline, ProjectPhase, ProjectStatus } from "@/types";

interface ProjectFormProps {
  defaultValues?: Partial<ProjectCreate>;
  onSubmit: (data: ProjectCreate) => Promise<void>;
  loading?: boolean;
  submitLabel?: string;
}

const phaseOptions = [
  { value: "VO", label: "Voorlopig Ontwerp (VO)" },
  { value: "DO", label: "Definitief Ontwerp (DO)" },
  { value: "UO", label: "Uitvoeringsontwerp (UO)" },
  { value: "Realisatie", label: "Realisatie" },
];

const disciplineOptions = [
  { value: "Gas", label: "Gas" },
  { value: "Elektra", label: "Elektra" },
  { value: "LS_MS", label: "LS/MS Kabel" },
  { value: "Stations", label: "Stations" },
];

const statusOptions = [
  { value: "active", label: "Actief" },
  { value: "on_hold", label: "In de wacht" },
  { value: "completed", label: "Afgerond" },
  { value: "cancelled", label: "Geannuleerd" },
];

export function ProjectForm({
  defaultValues,
  onSubmit,
  loading = false,
  submitLabel = "Opslaan",
}: ProjectFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProjectCreate>({
    defaultValues: {
      project_number: generateProjectNumber(),
      phase: "VO",
      discipline: "Elektra",
      status: "active",
      ...defaultValues,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Projectnummer"
          required
          error={errors.project_number?.message}
          {...register("project_number", { required: "Projectnummer is verplicht" })}
        />
        <Input
          label="Projectnaam"
          required
          error={errors.name?.message}
          {...register("name", { required: "Naam is verplicht" })}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Opdrachtgever"
          placeholder="bijv. Liander, Stedin, Enexis"
          {...register("client")}
        />
        <Input
          label="Locatie"
          placeholder="bijv. Amsterdam Noord"
          {...register("location")}
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Select
          label="Discipline"
          required
          options={disciplineOptions}
          {...register("discipline", { required: "Discipline is verplicht" })}
        />
        <Select
          label="Fase"
          required
          options={phaseOptions}
          {...register("phase", { required: "Fase is verplicht" })}
        />
        <Select
          label="Status"
          options={statusOptions}
          {...register("status")}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Startdatum"
          type="date"
          {...register("start_date")}
        />
        <Input
          label="Einddatum"
          type="date"
          {...register("end_date")}
        />
      </div>

      <Input
        label="Geraamd budget (€)"
        type="number"
        min={0}
        step={1000}
        placeholder="bijv. 150000"
        {...register("budget_estimated", { valueAsNumber: true })}
      />

      <Textarea
        label="Scopebeschrijving"
        rows={4}
        placeholder="Beschrijf de scope van het project: tracé, type werkzaamheden, bijzonderheden..."
        {...register("scope_description")}
      />

      <div className="flex justify-end pt-2">
        <Button type="submit" loading={loading}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
