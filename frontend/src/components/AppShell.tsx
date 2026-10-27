"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import {
  LayoutDashboard,
  FileText,
  MessagesSquare,
  LogOut,
  Menu,
  X,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/resumes/new", label: "Resumes", icon: FileText },
  { href: "/analyze", label: "New Prep", icon: Sparkles },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  const sidebar = (
    <div className="flex h-full flex-col">
      <Link href="/dashboard" className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-accent">
          <MessagesSquare className="h-4.5 w-4.5 text-white" />
        </div>
        <span className="font-display text-[15px] font-bold tracking-tight text-text">
          Interview Coach
        </span>
      </Link>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 rounded-[10px] px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "border-l-2 border-accent bg-accent/10 text-text"
                  : "text-muted hover:bg-surface2 hover:text-text"
              }`}
            >
              <Icon className="h-4.5 w-4.5" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-3">
        <div className="flex items-center gap-3 rounded-[10px] px-3 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-surface2 font-mono text-sm text-muted">
            {(user?.username || user?.email || "?").charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-text">{user?.username || "User"}</p>
            <p className="truncate text-xs text-faint">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="text-faint hover:text-danger"
            aria-label="Log out"
            title="Log out"
          >
            <LogOut className="h-4.5 w-4.5" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-border bg-surface md:block">
        {sidebar}
      </aside>

      {/* Mobile top bar */}
      <div className="fixed inset-x-0 top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-surface px-4 md:hidden">
        <span className="font-display font-bold text-text">Interview Coach</span>
        <button onClick={() => setMobileOpen(true)} aria-label="Open menu">
          <Menu className="h-5 w-5 text-muted" />
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 border-r border-border bg-surface">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-4 text-faint"
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      {/* Main */}
      <main className="flex-1 pt-14 md:ml-60 md:pt-0">
        <div className="mx-auto max-w-[1080px] px-4 py-8 md:px-6">{children}</div>
      </main>
    </div>
  );
}
