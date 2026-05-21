"use client";

import React from "react";
import { Bell, Search, User } from "lucide-react";
import { getStoredUser } from "@/lib/auth";

interface HeaderProps {
  title?: string;
  breadcrumb?: Array<{ label: string; href?: string }>;
}

export function Header({ title, breadcrumb }: HeaderProps) {
  const user = getStoredUser();

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-6 gap-4 shrink-0">
      {/* Title / Breadcrumb */}
      <div className="flex-1 min-w-0">
        {breadcrumb && breadcrumb.length > 0 ? (
          <nav className="flex items-center gap-1 text-sm">
            {breadcrumb.map((crumb, i) => (
              <React.Fragment key={i}>
                {i > 0 && <span className="text-gray-400 mx-0.5">/</span>}
                {crumb.href ? (
                  <a
                    href={crumb.href}
                    className="text-gray-500 hover:text-navy-700 transition-colors truncate"
                  >
                    {crumb.label}
                  </a>
                ) : (
                  <span className="text-gray-900 font-medium truncate">{crumb.label}</span>
                )}
              </React.Fragment>
            ))}
          </nav>
        ) : (
          title && <h1 className="text-sm font-semibold text-gray-900 truncate">{title}</h1>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button className="p-1.5 rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors">
          <Bell className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2 pl-2 border-l border-gray-200">
          <div className="w-7 h-7 rounded-full bg-navy-800 flex items-center justify-center text-white text-xs font-semibold">
            {user?.name?.charAt(0)?.toUpperCase() ?? "U"}
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium text-gray-800 leading-tight">{user?.name ?? "Gebruiker"}</p>
            <p className="text-2xs text-gray-500 leading-tight capitalize">{user?.role ?? ""}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
