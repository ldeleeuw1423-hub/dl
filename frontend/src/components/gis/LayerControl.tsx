"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Eye, EyeOff, Layers } from "lucide-react";

interface Layer {
  id: string;
  name: string;
  visible: boolean;
}

interface LayerControlProps {
  layers: Layer[];
  onToggle: (layerId: string) => void;
}

export function LayerControl({ layers, onToggle }: LayerControlProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-card p-3 w-64">
      <div className="flex items-center gap-2 mb-3">
        <Layers className="h-4 w-4 text-navy-600" />
        <span className="text-xs font-semibold text-gray-800">Kaartlagen</span>
      </div>
      <div className="space-y-1.5">
        {layers.map((layer) => (
          <button
            key={layer.id}
            onClick={() => onToggle(layer.id)}
            className={cn(
              "w-full flex items-center justify-between gap-2 px-2 py-1.5 rounded text-xs",
              "transition-colors hover:bg-gray-50",
              layer.visible ? "text-gray-800" : "text-gray-400"
            )}
          >
            <span className="truncate text-left">{layer.name}</span>
            {layer.visible ? (
              <Eye className="h-3.5 w-3.5 shrink-0 text-navy-600" />
            ) : (
              <EyeOff className="h-3.5 w-3.5 shrink-0 text-gray-300" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
