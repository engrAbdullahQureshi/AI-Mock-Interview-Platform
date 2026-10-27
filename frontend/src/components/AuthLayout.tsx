import Link from "next/link";
import { MessagesSquare } from "lucide-react";
import type { ReactNode } from "react";

export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <Link href="/" className="mb-8 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-accent">
          <MessagesSquare className="h-5 w-5 text-white" />
        </div>
        <span className="font-display text-lg font-bold tracking-tight">Interview Coach</span>
      </Link>
      <div className="w-full max-w-sm rounded-[16px] border border-border bg-surface p-7">
        <h1 className="font-display text-2xl font-bold">{title}</h1>
        <p className="mb-6 mt-1 text-sm text-muted">{subtitle}</p>
        {children}
      </div>
    </div>
  );
}
