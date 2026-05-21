"use client";

import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { api, getErrorMessage } from "@/lib/api";
import toast from "react-hot-toast";
import {
  Building2,
  Settings,
  Euro,
  UserPlus,
  Loader2,
  ShieldCheck,
} from "lucide-react";
import type { Organization, User, UserRole, OrganizationSettings } from "@/types";

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const inviteSchema = z.object({
  email: z.string().email("Ongeldig e-mailadres"),
  name: z.string().min(2, "Naam is verplicht"),
  role: z.enum(["admin", "pm", "engineer", "om", "viewer"] as const),
});

type InviteFormData = z.infer<typeof inviteSchema>;

const settingsSchema = z.object({
  name: z.string().min(2, "Naam is verplicht"),
  hourly_rate_engineering: z.coerce.number().min(0).optional(),
  hourly_rate_pm: z.coerce.number().min(0).optional(),
  hourly_rate_om: z.coerce.number().min(0).optional(),
  hourly_rate_workprep: z.coerce.number().min(0).optional(),
  hourly_rate_execution: z.coerce.number().min(0).optional(),
  risk_threshold_high: z.coerce.number().int().min(1).max(25).optional(),
  risk_threshold_critical: z.coerce.number().int().min(1).max(25).optional(),
});

type SettingsFormData = z.infer<typeof settingsSchema>;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Beheerder",
  pm: "Projectmanager",
  engineer: "Engineer",
  om: "Omgevingsmanager",
  viewer: "Lezer",
};

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "admin", label: "Beheerder" },
  { value: "pm", label: "Projectmanager" },
  { value: "engineer", label: "Engineer" },
  { value: "om", label: "Omgevingsmanager" },
  { value: "viewer", label: "Lezer" },
];

const TIER_LABELS: Record<string, string> = {
  free: "Gratis",
  professional: "Professioneel",
  enterprise: "Enterprise",
};

const TIER_VARIANTS: Record<string, "neutral" | "info" | "success"> = {
  free: "neutral",
  professional: "info",
  enterprise: "success",
};

function roleVariant(role: UserRole): "neutral" | "default" | "info" | "success" | "warning" {
  switch (role) {
    case "admin":
      return "warning";
    case "pm":
      return "default";
    case "engineer":
      return "info";
    case "om":
      return "success";
    default:
      return "neutral";
  }
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function OrganizationSettingsPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loadingOrg, setLoadingOrg] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  const [inviting, setInviting] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);

  const {
    register: registerSettings,
    handleSubmit: handleSettingsSubmit,
    reset: resetSettings,
    formState: { errors: settingsErrors },
  } = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
  });

  const {
    register: registerInvite,
    handleSubmit: handleInviteSubmit,
    reset: resetInvite,
    formState: { errors: inviteErrors },
  } = useForm<InviteFormData>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { role: "engineer" },
  });

  // Load org and users
  useEffect(() => {
    Promise.all([api.getMyOrganization(), api.getOrgUsers()])
      .then(([o, u]) => {
        setOrg(o);
        setUsers(u);
        const s = o.settings as (OrganizationSettings & Record<string, unknown>) | undefined;
        resetSettings({
          name: o.name,
          hourly_rate_engineering: s?.hourly_rate_engineering ?? undefined,
          hourly_rate_pm: s?.hourly_rate_pm ?? undefined,
          hourly_rate_om: s?.hourly_rate_om ?? undefined,
          hourly_rate_workprep: s?.hourly_rate_workprep ?? undefined,
          hourly_rate_execution: s?.hourly_rate_execution ?? undefined,
          risk_threshold_high: s?.risk_threshold_high ?? undefined,
          risk_threshold_critical: s?.risk_threshold_critical ?? undefined,
        });
      })
      .catch((err) => toast.error(getErrorMessage(err)))
      .finally(() => setLoadingOrg(false));
  }, [resetSettings]);

  const onSaveSettings = async (data: SettingsFormData) => {
    setSavingSettings(true);
    try {
      const updated = await api.updateMyOrganization({
        name: data.name,
        settings: {
          hourly_rate_engineering: data.hourly_rate_engineering,
          hourly_rate_pm: data.hourly_rate_pm,
          hourly_rate_om: data.hourly_rate_om,
          hourly_rate_workprep: data.hourly_rate_workprep,
          hourly_rate_execution: data.hourly_rate_execution,
          risk_threshold_high: data.risk_threshold_high,
          risk_threshold_critical: data.risk_threshold_critical,
        },
      });
      setOrg(updated);
      toast.success("Organisatie-instellingen opgeslagen");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSavingSettings(false);
    }
  };

  const onInvite = async (data: InviteFormData) => {
    setInviting(true);
    try {
      const newUser = await api.inviteUser(data);
      setUsers((prev) => [...prev, newUser]);
      resetInvite({ role: "engineer" });
      setInviteOpen(false);
      toast.success(`${newUser.name} uitgenodigd`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setInviting(false);
    }
  };

  if (loadingOrg) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-6 w-6 text-navy-600 animate-spin" />
      </div>
    );
  }

  if (!org) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-red-500">
        Organisatie niet gevonden
      </div>
    );
  }

  return (
    <>
      <Header
        breadcrumb={[
          { label: "Instellingen" },
          { label: "Organisatie" },
        ]}
      />
      <div className="page-container space-y-5">
        {/* Org overview */}
        <div className="flex items-center gap-3 mb-1">
          <div className="h-10 w-10 rounded-xl bg-navy-100 flex items-center justify-center">
            <Building2 className="h-5 w-5 text-navy-700" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">{org.name}</h1>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge variant={TIER_VARIANTS[org.subscription_tier] ?? "neutral"}>
                {TIER_LABELS[org.subscription_tier] ?? org.subscription_tier}
              </Badge>
              <span className="text-xs text-gray-400">
                Max {org.max_projects} projecten · Max {org.max_users} gebruikers
              </span>
            </div>
          </div>
        </div>

        {/* Settings form */}
        <Card padding="md">
          <CardHeader
            title="Organisatie-instellingen"
            subtitle="Naam en aangepaste tarieven / drempelwaarden"
            actions={
              <Settings className="h-4 w-4 text-gray-400" />
            }
          />
          <form onSubmit={handleSettingsSubmit(onSaveSettings)} className="space-y-4">
            {/* Name */}
            <div>
              <label className="form-label">Organisatienaam</label>
              <Input
                {...registerSettings("name")}
                placeholder="Bijv. Liander Regio Noord"
                error={settingsErrors.name?.message}
              />
            </div>

            {/* Custom hourly rates */}
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
                <Euro className="h-3.5 w-3.5 text-gray-400" />
                Aangepaste uurtarieven (€/uur) — laat leeg voor standaard
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div>
                  <label className="form-label">Engineering</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="105"
                    {...registerSettings("hourly_rate_engineering")}
                    error={settingsErrors.hourly_rate_engineering?.message}
                  />
                </div>
                <div>
                  <label className="form-label">Projectmanagement</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="115"
                    {...registerSettings("hourly_rate_pm")}
                    error={settingsErrors.hourly_rate_pm?.message}
                  />
                </div>
                <div>
                  <label className="form-label">Omgevingsmanagement</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="102"
                    {...registerSettings("hourly_rate_om")}
                    error={settingsErrors.hourly_rate_om?.message}
                  />
                </div>
                <div>
                  <label className="form-label">Werkvoorbereiding</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="92"
                    {...registerSettings("hourly_rate_workprep")}
                    error={settingsErrors.hourly_rate_workprep?.message}
                  />
                </div>
                <div>
                  <label className="form-label">Uitvoering</label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="88"
                    {...registerSettings("hourly_rate_execution")}
                    error={settingsErrors.hourly_rate_execution?.message}
                  />
                </div>
              </div>
            </div>

            {/* Risk thresholds */}
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-gray-400" />
                Risicodrempelwaarden (score 1–25)
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="form-label">Hoog risico (≥)</label>
                  <Input
                    type="number"
                    min={1}
                    max={25}
                    placeholder="9"
                    {...registerSettings("risk_threshold_high")}
                    error={settingsErrors.risk_threshold_high?.message}
                  />
                </div>
                <div>
                  <label className="form-label">Kritiek risico (≥)</label>
                  <Input
                    type="number"
                    min={1}
                    max={25}
                    placeholder="15"
                    {...registerSettings("risk_threshold_critical")}
                    error={settingsErrors.risk_threshold_critical?.message}
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button type="submit" loading={savingSettings}>
                Opslaan
              </Button>
            </div>
          </form>
        </Card>

        {/* Users */}
        <Card padding="md">
          <CardHeader
            title={`Gebruikers (${users.length} / ${org.max_users})`}
            subtitle="Teamleden en hun rollen binnen de organisatie"
            actions={
              <Button
                size="sm"
                icon={<UserPlus className="h-3.5 w-3.5" />}
                onClick={() => setInviteOpen((v) => !v)}
              >
                Uitnodigen
              </Button>
            }
          />

          {/* Invite form */}
          {inviteOpen && (
            <form
              onSubmit={handleInviteSubmit(onInvite)}
              className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-3"
            >
              <p className="text-xs font-semibold text-gray-700">Nieuwe gebruiker uitnodigen</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="form-label">E-mailadres</label>
                  <Input
                    type="email"
                    placeholder="naam@organisatie.nl"
                    {...registerInvite("email")}
                    error={inviteErrors.email?.message}
                  />
                </div>
                <div>
                  <label className="form-label">Naam</label>
                  <Input
                    placeholder="Volledige naam"
                    {...registerInvite("name")}
                    error={inviteErrors.name?.message}
                  />
                </div>
                <div>
                  <label className="form-label">Rol</label>
                  <select
                    {...registerInvite("role")}
                    className={cn(
                      "w-full rounded-md border border-gray-300 bg-white text-sm text-gray-900",
                      "px-3 py-2",
                      "focus:outline-none focus:ring-2 focus:ring-navy-500 focus:border-transparent",
                      inviteErrors.role && "border-red-400"
                    )}
                  >
                    {ROLE_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                  {inviteErrors.role && (
                    <p className="text-xs text-red-600 mt-0.5">{inviteErrors.role.message}</p>
                  )}
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setInviteOpen(false);
                    resetInvite({ role: "engineer" });
                  }}
                >
                  Annuleren
                </Button>
                <Button type="submit" size="sm" loading={inviting}>
                  Uitnodigen
                </Button>
              </div>
            </form>
          )}

          {/* User list */}
          {users.length === 0 ? (
            <p className="text-sm text-gray-400 italic">Geen gebruikers gevonden.</p>
          ) : (
            <div className="divide-y divide-gray-100">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between py-2.5">
                  <div className="flex items-center gap-2.5">
                    <div className="h-7 w-7 rounded-full bg-navy-100 flex items-center justify-center shrink-0">
                      <span className="text-xs font-bold text-navy-700 uppercase">
                        {u.name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">{u.name}</p>
                      <p className="text-xs text-gray-400">{u.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={roleVariant(u.role as UserRole)}>
                      {ROLE_LABELS[u.role as UserRole] ?? u.role}
                    </Badge>
                    {!u.is_active && (
                      <Badge variant="neutral">Inactief</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
