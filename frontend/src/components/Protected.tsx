"use client";

import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { useRequireAuth } from "@/lib/auth";
import { AppShell } from "./AppShell";

/** Wraps a page in auth-guard + AppShell. Shows a spinner during rehydrate. */
export function Protected({ children }: { children: ReactNode }) {
  const { ready } = useRequireAuth();

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-accent" />
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
