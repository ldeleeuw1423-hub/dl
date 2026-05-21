"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Minus, Square, MapPin, Trash2 } from "lucide-react";

interface DrawingToolsProps {
  activeTool: "none" | "line" | "polygon" | "marker";
  onSelectTool: (tool: "none" | "line" | "polygon" | "marker") => void;
  onClear: () => void;
}

const tools = [
  { id: "line" as const, label: "Tracé tekenen", icon: Minus },
  { id: "polygon" as const, label: "Gebied selecteren", icon: Square },
  { id: "marker" as const, label: "Punt plaatsen", icon: MapPin },
];

export function DrawingTools({ activeTool, onSelectTool, onClear }: DrawingToolsProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-card p-2 flex flex-col gap-1.5">
      {tools.map((tool) => {
        const Icon = tool.icon;
        const isActive = activeTool === tool.id;
        return (
          <button
            key={tool.id}
            onClick={() => onSelectTool(isActive ? "none" : tool.id)}
            title={tool.label}
            className={cn(
              "p-2 rounded-md transition-colors",
              isActive
                ? "bg-navy-800 text-white"
                : "text-gray-600 hover:bg-gray-100"
            )}
          >
            <Icon className="h-4 w-4" />
          </button>
        );
      })}
      <div className="border-t border-gray-100 mt-0.5 pt-1.5">
        <button
          onClick={onClear}
          title="Alles verwijderen"
          className="p-2 rounded-md text-red-500 hover:bg-red-50 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
