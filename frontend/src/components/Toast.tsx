"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

type ToastKind = "success" | "error" | "info";
interface ToastItem {
  id: number;
  message: string;
  kind: ToastKind;
}

interface ToastCtx {
  show: (message: string, kind?: ToastKind) => void;
  error: (message: string) => void;
  success: (message: string) => void;
}

const Ctx = createContext<ToastCtx | null>(null);

let seq = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const remove = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    (message: string, kind: ToastKind = "info") => {
      const id = ++seq;
      setItems((prev) => [...prev, { id, message, kind }]);
      setTimeout(() => remove(id), 4200);
    },
    [remove],
  );

  const value: ToastCtx = {
    show,
    error: (m) => show(m, "error"),
    success: (m) => show(m, "success"),
  };

  return (
    <Ctx.Provider value={value}>
      {children}
      <div className="no-print fixed top-4 right-4 z-50 flex w-[340px] max-w-[calc(100vw-2rem)] flex-col gap-2">
        {items.map((t) => (
          <ToastCard key={t.id} item={t} onClose={() => remove(t.id)} />
        ))}
      </div>
    </Ctx.Provider>
  );
}

function ToastCard({ item, onClose }: { item: ToastItem; onClose: () => void }) {
  const palette = {
    success: { icon: CheckCircle2, color: "text-success" },
    error: { icon: AlertCircle, color: "text-danger" },
    info: { icon: Info, color: "text-info" },
  }[item.kind];
  const Icon = palette.icon;
  return (
    <div
      role="status"
      className="animate-[rise_0.25s_ease-out] flex items-start gap-3 rounded-[12px] border border-border bg-surface2 p-3.5 shadow-[0_8px_24px_#00000059]"
    >
      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${palette.color}`} />
      <p className="flex-1 text-sm text-text">{item.message}</p>
      <button onClick={onClose} className="text-faint hover:text-text" aria-label="Dismiss">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function useToast(): ToastCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
