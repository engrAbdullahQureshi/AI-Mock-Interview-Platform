"use client";

import { useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";

interface Props {
  header: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
}

export function AccordionItem({ header, children, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="print-plain overflow-hidden rounded-[12px] border border-border bg-surface">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition-colors hover:bg-surface2"
      >
        <div className="min-w-0 flex-1">{header}</div>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-faint transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && <div className="border-t border-border px-4 py-4">{children}</div>}
    </div>
  );
}
