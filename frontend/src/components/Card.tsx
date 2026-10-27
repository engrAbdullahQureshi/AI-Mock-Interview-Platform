import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
}

export function Card({ children, className = "", title, subtitle, action }: Props) {
  return (
    <div
      className={`print-plain rounded-[16px] border border-border bg-surface p-6 shadow-[0_1px_2px_#00000040] ${className}`}
    >
      {(title || action) && (
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            {title && <h3 className="font-display text-lg font-semibold text-text">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
