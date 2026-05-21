"use client";

import React from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader } from "@/components/ui/Card";
import { MapView } from "@/components/gis/MapView";
import { useProject } from "@/hooks/useProjects";

export default function GISPage() {
  const { id } = useParams<{ id: string }>();
  const { project } = useProject(id);

  return (
    <>
      <Header
        breadcrumb={[
          { label: "Projecten", href: "/projects" },
          { label: project?.name ?? "Project", href: `/projects/${id}` },
          { label: "GIS / Kaart" },
        ]}
      />
      <div className="page-container">
        <div className="mb-4">
          <h1 className="text-lg font-bold text-gray-900">GIS / Kaartweergave</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Teken tracé of selecteer gebied — analyseer omgevingsfactoren met PDOK kaartlagen
          </p>
        </div>

        <Card padding="none" className="overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 flex items-center gap-3 text-xs text-gray-600">
            <span className="font-medium">Bronnen:</span>
            <span>OpenStreetMap</span>
            <span>•</span>
            <span>PDOK BGT</span>
            <span>•</span>
            <span>PDOK BAG</span>
            <span>•</span>
            <span>Natura 2000</span>
          </div>
          <MapView projectId={id} height="560px" />
        </Card>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <Card padding="sm">
            <CardHeader title="Gebruik" subtitle="Hoe de kaart te gebruiken" />
            <ul className="text-xs text-gray-600 space-y-1.5">
              <li>• Tracé tekenen: gebruik de lijn-tool</li>
              <li>• Gebied selecteren: gebruik de vlak-tool</li>
              <li>• PDOK-lagen aan/uitzetten via de lagenlijst</li>
              <li>• Klik &quot;Analyseer gebied&quot; voor automatische risicodetectie</li>
            </ul>
          </Card>
          <Card padding="sm">
            <CardHeader title="PDOK Kaartlagen" subtitle="Nederlandse geodata" />
            <ul className="text-xs text-gray-600 space-y-1.5">
              <li>• BGT: grootschalige topografie</li>
              <li>• BAG: adressen en gebouwen</li>
              <li>• AHN: hoogtegegevens</li>
              <li>• Bestuurlijke grenzen</li>
            </ul>
          </Card>
          <Card padding="sm">
            <CardHeader title="Analyse" subtitle="Automatische omgevingsdetectie" />
            <ul className="text-xs text-gray-600 space-y-1.5">
              <li>• Tracelengte berekening</li>
              <li>• Kruisingen schatten</li>
              <li>• KLIC-check herinnering</li>
              <li>• Risico-indicaties</li>
            </ul>
          </Card>
        </div>
      </div>
    </>
  );
}
