"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import type { RiskCreate, RiskCategory, RiskStatus } from "@/types";

interface RiskFormProps {
  defaultValues?: Partial<RiskCreate>;
  onSubmit: (data: RiskCreate) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

const categoryOptions = [
  { value: "Technisch", label: "Technisch" },
  { value: "Planning", label: "Planning" },
  { value: "Financieel", label: "Financieel" },
  { value: "Omgeving", label: "Omgeving" },
  { value: "Vergunning", label: "Vergunning" },
  { value: "Stakeholder", label: "Stakeholder" },
  { value: "Overig", label: "Overig" },
];

const scaleOptions = [
  { value: "1", label: "1 — Zeer laag" },
  { value: "2", label: "2 — Laag" },
  { value: "3", label: "3 — Gemiddeld" },
  { value: "4", label: "4 — Hoog" },
  { value: "5", label: "5 — Zeer hoog" },
];

const statusOptions = [
  { value: "open", label: "Open" },
  { value: "mitigated", label: "Gemitigeerd" },
  { value: "accepted", label: "Geaccepteerd" },
  { value: "closed", label: "Gesloten" },
];

export function RiskForm({ defaultValues, onSubmit, onCancel, loading }: RiskFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RiskCreate>({
    defaultValues: {
      category: "Technisch",
      probability: 3,
      impact: 3,
      status: "open",
      source: "manual",
      ...defaultValues,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Textarea
        label="Risicobeschrijving"
        required
        rows={3}
        placeholder="Beschrijf het risico concreet..."
        error={errors.description?.message}
        {...register("description", { required: "Beschrijving is verplicht" })}
      />

      <div className="grid grid-cols-3 gap-3">
        <Select
          label="Categorie"
          options={categoryOptions}
          {...register("category")}
        />
        <Select
          label="Kans (1-5)"
          required
          options={scaleOptions}
          error={errors.probability?.message}
          {...register("probability", { valueAsNumber: true, required: true })}
        />
        <Select
          label="Impact (1-5)"
          required
          options={scaleOptions}
          error={errors.impact?.message}
          {...register("impact", { valueAsNumber: true, required: true })}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Eigenaar"
          placeholder="Naam verantwoordelijke"
          {...register("owner")}
        />
        <Select
          label="Status"
          options={statusOptions}
          {...register("status")}
        />
      </div>

      <Input
        label="Deadline"
        type="date"
        {...register("deadline")}
      />

      <Textarea
        label="Maatregel"
        rows={3}
        placeholder="Beschrijf de beheermaatregel..."
        {...register("mitigation_measure")}
      />

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" type="button" onClick={onCancel}>
          Annuleren
        </Button>
        <Button type="submit" loading={loading}>
          Opslaan
        </Button>
      </div>
    </form>
  );
}
