"use client";

import React, { useEffect, useRef, useState } from "react";
import { LayerControl } from "./LayerControl";
import { DrawingTools } from "./DrawingTools";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import type { PDOKAnalysisResult } from "@/types";
import { AlertTriangle, MapPin, Layers, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface MapViewProps {
  projectId?: string;
  height?: string;
}

const PDOK_LAYERS = [
  {
    id: "osm",
    name: "OpenStreetMap",
    visible: true,
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  },
  {
    id: "bgt",
    name: "BGT - Grootschalige topografie",
    visible: false,
    wmsUrl: "https://service.pdok.nl/lv/bgt/wms/v1_0",
    wmsLayer: "BGT",
  },
  {
    id: "bag",
    name: "BAG - Adressen en gebouwen",
    visible: false,
    wmsUrl: "https://service.pdok.nl/lv/bag/wms/v2_0",
    wmsLayer: "pand",
  },
];

export function MapView({ projectId, height = "500px" }: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null);
  const drawnItemsRef = useRef<any>(null);
  const [mounted, setMounted] = useState(false);
  const [activeTool, setActiveTool] = useState<"none" | "line" | "polygon" | "marker">("none");
  const [layers, setLayers] = useState(PDOK_LAYERS);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<PDOKAnalysisResult | null>(null);
  const [pdokPanelOpen, setPdokPanelOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !mapRef.current || leafletMapRef.current) return;

    let L: any;
    let map: any;

    const initMap = async () => {
      try {
        L = (await import("leaflet")).default;
        await import("leaflet/dist/leaflet.css");

        // Fix default icon paths
        delete (L.Icon.Default.prototype as any)._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
          iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
          shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
        });

        map = L.map(mapRef.current, {
          center: [52.3676, 4.9041], // Netherlands center
          zoom: 8,
          zoomControl: true,
        });

        leafletMapRef.current = map;

        // Base OSM layer
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 19,
        }).addTo(map);

        // Feature group for drawn items
        const drawnItems = new L.FeatureGroup();
        drawnItemsRef.current = drawnItems;
        map.addLayer(drawnItems);

      } catch (error) {
        console.error("Map initialization failed:", error);
      }
    };

    initMap();

    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, [mounted]);

  const handleToolSelect = async (tool: typeof activeTool) => {
    setActiveTool(tool);
    const L = (await import("leaflet")).default;
    const map = leafletMapRef.current;
    const drawnItems = drawnItemsRef.current;
    if (!map || !drawnItems) return;

    // Remove any existing click handlers
    map.off("click");

    if (tool === "marker") {
      map.on("click", (e: any) => {
        L.marker([e.latlng.lat, e.latlng.lng]).addTo(drawnItems);
      });
    } else if (tool === "line" || tool === "polygon") {
      toast("Klik op de kaart om punten te plaatsen. Dubbelklik om te voltooien.", {
        icon: "ℹ️",
        duration: 3000,
      });
    }
  };

  const handleClear = async () => {
    const drawnItems = drawnItemsRef.current;
    if (drawnItems) {
      drawnItems.clearLayers();
    }
    setActiveTool("none");
    setAnalysisResult(null);
    setPdokPanelOpen(false);
    const map = leafletMapRef.current;
    if (map) map.off("click");
  };

  const handleLayerToggle = (layerId: string) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === layerId ? { ...l, visible: !l.visible } : l))
    );
  };

  const handleAnalyze = async () => {
    const drawnItems = drawnItemsRef.current;
    if (!drawnItems || drawnItems.getLayers().length === 0) {
      toast.error("Teken eerst een tracé of gebied op de kaart");
      return;
    }
    setAnalyzing(true);
    try {
      const layers = drawnItems.getLayers();
      const firstLayer = layers[0];
      const geojson = firstLayer.toGeoJSON();
      // Use live PDOK analysis endpoint
      const result = await api.analyzeGeometryPDOK(geojson.geometry);
      setAnalysisResult(result);
      setPdokPanelOpen(true);
      toast.success("PDOK analyse voltooid");
    } catch (error) {
      // Fallback to local analysis
      try {
        const layers = drawnItemsRef.current.getLayers();
        const geojson = layers[0].toGeoJSON();
        const result = await api.analyzeGeometry(geojson.geometry);
        setAnalysisResult(result as PDOKAnalysisResult);
        setPdokPanelOpen(true);
        toast("Lokale analyse voltooid (PDOK niet bereikbaar)", { icon: "⚠️" });
      } catch {
        toast.error("Analyse mislukt");
      }
    } finally {
      setAnalyzing(false);
    }
  };

  if (!mounted) {
    return (
      <div
        style={{ height }}
        className="bg-gray-100 rounded-lg flex items-center justify-center text-sm text-gray-400"
      >
        Kaart wordt geladen...
      </div>
    );
  }

  const pdok = analysisResult?.pdok;

  return (
    <div className="flex gap-3" style={{ minHeight: height }}>
      {/* Map */}
      <div className="relative flex-1" style={{ height }}>
        <div ref={mapRef} className="w-full h-full rounded-lg z-0" />

        {/* Controls overlay */}
        <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-2">
          <LayerControl
            layers={layers}
            onToggle={handleLayerToggle}
          />
        </div>

        <div className="absolute top-3 left-12 z-[1000]">
          <DrawingTools
            activeTool={activeTool}
            onSelectTool={handleToolSelect}
            onClear={handleClear}
          />
        </div>

        <div className="absolute bottom-3 left-3 z-[1000]">
          <Button
            size="sm"
            onClick={handleAnalyze}
            loading={analyzing}
            className="shadow-lg"
            icon={<Zap className="h-3.5 w-3.5" />}
          >
            PDOK analyse
          </Button>
        </div>

        {/* Quick analysis overlay (legacy) */}
        {analysisResult && !pdokPanelOpen && (
          <div className="absolute bottom-3 right-3 z-[1000] bg-white rounded-lg border border-gray-200 shadow-xl p-3 max-w-xs">
            <p className="text-xs font-semibold text-gray-800 mb-2">Analyse resultaat</p>
            {analysisResult.analysis?.estimated_length_m && (
              <p className="text-xs text-gray-600">
                Tracelengte: ~{analysisResult.analysis.estimated_length_m}m
              </p>
            )}
            {analysisResult.risks?.length > 0 && (
              <div className="mt-2">
                <p className="text-2xs font-medium text-amber-700 mb-1">Gedetecteerde risico&apos;s:</p>
                {analysisResult.risks.slice(0, 2).map((r: any, i: number) => (
                  <p key={i} className="text-2xs text-gray-600">• {r.description}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* PDOK analysis side panel */}
      {pdokPanelOpen && analysisResult && (
        <div className="w-72 shrink-0 flex flex-col gap-3 overflow-y-auto" style={{ maxHeight: height }}>
          <div className="bg-white rounded-lg border border-gray-200 p-3">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-gray-800">PDOK Analyse</p>
              <button
                className="text-xs text-gray-400 hover:text-gray-600"
                onClick={() => setPdokPanelOpen(false)}
              >
                ✕
              </button>
            </div>

            {/* Geometry info */}
            {analysisResult.analysis?.estimated_length_m && (
              <div className="flex items-center gap-1.5 mb-2">
                <Layers className="h-3.5 w-3.5 text-navy-600" />
                <span className="text-xs text-gray-700">
                  Tracelengte: <strong>{analysisResult.analysis.estimated_length_m} m</strong>
                </span>
              </div>
            )}
            {analysisResult.analysis?.estimated_area_m2 && (
              <div className="flex items-center gap-1.5 mb-2">
                <Layers className="h-3.5 w-3.5 text-navy-600" />
                <span className="text-xs text-gray-700">
                  Oppervlakte: <strong>{analysisResult.analysis.estimated_area_m2} m²</strong>
                </span>
              </div>
            )}

            {/* PDOK data */}
            {pdok && (
              <div className="space-y-2 mt-2 border-t border-gray-100 pt-2">
                {pdok.gemeente && (
                  <div className="flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-navy-500" />
                    <span className="text-xs text-gray-700">
                      Gemeente: <strong>{pdok.gemeente}</strong>
                    </span>
                  </div>
                )}

                {pdok.urban_density && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-2xs text-gray-400">Stedelijke dichtheid:</span>
                    <Badge
                      variant={
                        pdok.urban_density === "hoog"
                          ? "danger"
                          : pdok.urban_density === "gemiddeld"
                          ? "warning"
                          : "success"
                      }
                    >
                      {pdok.urban_density}
                      {pdok.address_count !== undefined && ` (${pdok.address_count} adressen)`}
                    </Badge>
                  </div>
                )}

                {pdok.natura2000_proximity !== undefined && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-2xs text-gray-400">Natura 2000:</span>
                    <Badge variant={pdok.natura2000_proximity ? "danger" : "success"}>
                      {pdok.natura2000_proximity ? "Binnen 500m" : "Niet nabij"}
                    </Badge>
                  </div>
                )}

                {pdok.crossings && (
                  <div className="mt-1">
                    <p className="text-2xs font-medium text-gray-500 mb-1">Kruisingen:</p>
                    <div className="grid grid-cols-2 gap-1">
                      <div className="text-2xs bg-gray-50 rounded px-2 py-1">
                        <span className="text-gray-400">Watergangen:</span>{" "}
                        <strong>{pdok.crossings.waterways}</strong>
                      </div>
                      <div className="text-2xs bg-gray-50 rounded px-2 py-1">
                        <span className="text-gray-400">Wegen:</span>{" "}
                        <strong>{pdok.crossings.major_roads}</strong>
                      </div>
                      <div className="text-2xs bg-gray-50 rounded px-2 py-1">
                        <span className="text-gray-400">Spoor:</span>{" "}
                        <strong>{pdok.crossings.railways}</strong>
                      </div>
                      <div className="text-2xs bg-gray-50 rounded px-2 py-1">
                        <span className="text-gray-400">Fietspad:</span>{" "}
                        <strong>{pdok.crossings.cycle_paths}</strong>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Detected risks */}
          {analysisResult.risks.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              <div className="flex items-center gap-1.5 mb-2">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                <p className="text-xs font-semibold text-gray-800">
                  Gedetecteerde risico&apos;s ({analysisResult.risks.length})
                </p>
              </div>
              <ul className="space-y-1.5">
                {analysisResult.risks.map((r, i) => (
                  <li key={i} className="text-2xs text-gray-600 flex gap-1.5">
                    <span className="text-amber-500 shrink-0">•</span>
                    {r.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Likely permits */}
          {analysisResult.permits_likely.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              <p className="text-xs font-semibold text-gray-800 mb-2">Mogelijke vergunningen</p>
              <ul className="space-y-1">
                {analysisResult.permits_likely.map((p, i) => (
                  <li key={i} className="text-2xs text-gray-600 flex gap-1.5">
                    <span className="text-blue-400 shrink-0">→</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Notes */}
          {analysisResult.notes.length > 0 && (
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-3">
              <p className="text-xs font-semibold text-gray-600 mb-1">Aandachtspunten</p>
              <ul className="space-y-1">
                {analysisResult.notes.map((n, i) => (
                  <li key={i} className="text-2xs text-gray-500">
                    {n}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
