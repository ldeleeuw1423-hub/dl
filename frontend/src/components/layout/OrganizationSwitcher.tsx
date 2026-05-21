"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Building2, Settings, ChevronRight } from "lucide-react";
import { api, getErrorMessage } from "@/lib/api";
import type { Organization } from "@/types";
import { cn } from "@/lib/utils";

const TIER_LABELS: Record<string, string> = {
  free: "Gratis",
  professional: "Professioneel",
  enterprise: "Enterprise",
};

const TIER_COLOURS: Record<string, string> = {
  free: "text-gray-500",
  professional: "text-blue-600",
  enterprise: "text-purple-600",
};

/**
 * Shows the current organisation name in the sidebar with a link to
 * /settings/organization.
 */
export function OrganizationSwitcher() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMyOrganization()
      .then(setOrg)
      .catch((err) => {
        // Silently ignore — user may not have an org yet
        setError(getErrorMessage(err));
      });
  }, []);

  if (error || !org) {
    return null;
  }

  return (
    <Link
      href="/settings/organization"
      className={cn(
        "flex items-center gap-2 px-2.5 py-2 rounded-md",
        "text-navy-300 hover:bg-navy-800/70 hover:text-white transition-colors group"
      )}
    >
      <div className="h-7 w-7 rounded-md bg-navy-700 flex items-center justify-center shrink-0">
        <Building2 className="h-4 w-4 text-navy-200" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-navy-100 truncate">{org.name}</p>
        <p className="text-2xs text-navy-400">
          {TIER_LABELS[org.subscription_tier] ?? org.subscription_tier}
        </p>
      </div>
      <Settings className="h-3.5 w-3.5 text-navy-500 opacity-0 group-hover:opacity-100 shrink-0 transition-opacity" />
    </Link>
  );
}
