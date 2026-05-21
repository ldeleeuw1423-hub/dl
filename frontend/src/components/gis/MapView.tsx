"use client";

import React, { useEffect, useRef, useState } from "react";
import { LayerControl } from "./LayerControl";
import { DrawingTools } from "./DrawingTools";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

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
  const [analysisResult, setAnalysisResult] = useState<any>(null);

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
      const result = await api.analyzeGeometry(geojson.geometry);
      setAnalysisResult(result);
      toast.success("Analyse voltooid");
    } catch (error) {
      toast.error("Analyse mislukt");
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

  return (
    <div className="relative" style={{ height }}>
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
        >
          Analyseer gebied
        </Button>
      </div>

      {/* Analysis result */}
      {analysisResult && (
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
  );
}
