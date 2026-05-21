import React from "react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  trendLabel?: string;
  color?: "default" | "amber" | "green" | "red" | "blue";
  className?: string;
}

const colorMap = {
  default: { icon: "text-navy-600 bg-navy-50", value: "text-navy-900" },
  amber: { icon: "text-amber-600 bg-amber-50", value: "text-amber-900" },
  green: { icon: "text-green-600 bg-green-50", value: "text-green-900" },
  red: { icon: "text-red-600 bg-red-50", value: "text-red-900" },
  blue: { icon: "text-blue-600 bg-blue-50", value: "text-blue-900" },
};

export function KPICard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendLabel,
  color = "default",
  className,
}: KPICardProps) {
  const colors = colorMap[color];
  return (
    <Card className={cn("flex flex-col gap-3", className)}>
      <div className="flex items-start justify-between">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{title}</p>
        {icon && (
          <div className={cn("p-1.5 rounded-md", colors.icon)}>
            {icon}
          </div>
        )}
      </div>
      <div>
        <p className={cn("text-2xl font-bold", colors.value)}>{value}</p>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {trend && (
        <div className="flex items-center gap-1 text-xs">
          {trend === "up" && <TrendingUp className="h-3 w-3 text-green-500" />}
          {trend === "down" && <TrendingDown className="h-3 w-3 text-red-500" />}
          {trend === "neutral" && <Minus className="h-3 w-3 text-gray-400" />}
          {trendLabel && (
            <span
              className={cn(
                trend === "up" && "text-green-600",
                trend === "down" && "text-red-600",
                trend === "neutral" && "text-gray-500"
              )}
            >
              {trendLabel}
            </span>
          )}
        </div>
      )}
    </Card>
  );
}
