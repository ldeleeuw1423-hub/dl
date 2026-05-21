"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import type { PermitCreate } from "@/types";

interface PermitFormProps {
  defaultValues?: Partial<PermitCreate>;
  onSubmit: (data: PermitCreate) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

const authorityOptions = [
  { value: "gemeente", label: "Gemeente" },
  { value: "provincie", label: "Provincie" },
  { value: "waterschap", label: "Waterschap" },
  { value: "prorail", label: "ProRail" },
  { value: "rws", label: "Rijkswaterstaat" },
  { value: "overig", label: "Overig" },
];

const statusOptions = [
  { value: "required", label: "Vereist" },
  { value: "in_preparation", label: "In voorbereiding" },
  { value: "submitted", label: "Ingediend" },
  { value: "approved", label: "Verleend" },
  { value: "rejected", label: "Geweigerd" },
  { value: "not_required", label: "Niet vereist" },
];

const riskLevelOptions = [
  { value: "low", label: "Laag" },
  { value: "medium", label: "Gemiddeld" },
  { value: "high", label: "Hoog" },
  { value: "critical", label: "Kritiek" },
];

export function PermitForm({ defaultValues, onSubmit, onCancel, loading }: PermitFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PermitCreate>({
    defaultValues: {
      authority: "gemeente",
      status: "required",
      risk_level: "medium",
      delay_probability: 25,
      ...defaultValues,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="Type vergunning"
        required
        placeholder="bijv. Instemmingsbesluit, Omgevingsvergunning"
        error={errors.permit_type?.message}
        {...register("permit_type", { required: "Type is verplicht" })}
      />

      <Textarea
        label="Beschrijving"
        rows={3}
        placeholder="Beschrijf de vergunning en waarom deze nodig is..."
        {...register("description")}
      />

      <div className="grid grid-cols-2 gap-3">
        <Select
          label="Bevoegd gezag"
          required
          options={authorityOptions}
          {...register("authority")}
        />
        <Select
          label="Status"
          options={statusOptions}
          {...register("status")}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Select
          label="Risiconiveau"
          options={riskLevelOptions}
          {...register("risk_level")}
        />
        <Input
          label="Kans op vertraging (%)"
          type="number"
          min={0}
          max={100}
          {...register("delay_probability", { valueAsNumber: true })}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Indiendatum"
          type="date"
          {...register("submission_date")}
        />
        <Input
          label="Verwachte verlening"
          type="date"
          {...register("expected_approval")}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Eigenaar"
          placeholder="Naam verantwoordelijke"
          {...register("owner")}
        />
      </div>

      <Textarea
        label="Notities"
        rows={2}
        {...register("notes")}
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
