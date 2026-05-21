"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  FolderKanban,
  Clock,
  Settings,
  LogOut,
  Zap,
  ChevronRight,
} from "lucide-react";
import { clearAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";

const navItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Projecten",
    href: "/projects",
    icon: FolderKanban,
  },
  {
    label: "Historische data",
    href: "/historical",
    icon: Clock,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    clearAuth();
    router.push("/login");
  };

  return (
    <aside className="flex flex-col w-60 h-screen bg-navy-950 text-white shrink-0 fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 h-14 border-b border-navy-800">
        <div className="w-7 h-7 bg-amber-500 rounded flex items-center justify-center shrink-0">
          <Zap className="h-4 w-4 text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-bold text-white leading-tight truncate">InfraEstimator</p>
          <p className="text-2xs text-navy-400 leading-tight">Netbeheer NL</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 overflow-y-auto">
        <p className="px-2 mb-2 text-2xs font-semibold uppercase tracking-widest text-navy-500">
          Navigatie
        </p>
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm transition-all",
                    "group relative",
                    isActive
                      ? "bg-navy-800 text-white font-medium"
                      : "text-navy-300 hover:bg-navy-800/70 hover:text-white"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0",
                      isActive ? "text-amber-400" : "text-navy-400 group-hover:text-navy-200"
                    )}
                  />
                  <span className="truncate">{item.label}</span>
                  {isActive && (
                    <ChevronRight className="h-3 w-3 ml-auto text-navy-400 shrink-0" />
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="px-2 py-3 border-t border-navy-800 space-y-0.5">
        <Link
          href="/settings"
          className="flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm text-navy-300 hover:bg-navy-800/70 hover:text-white transition-all"
        >
          <Settings className="h-4 w-4 text-navy-400" />
          <span>Instellingen</span>
        </Link>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md text-sm text-navy-300 hover:bg-red-900/40 hover:text-red-300 transition-all"
        >
          <LogOut className="h-4 w-4" />
          <span>Uitloggen</span>
        </button>
      </div>
    </aside>
  );
}
