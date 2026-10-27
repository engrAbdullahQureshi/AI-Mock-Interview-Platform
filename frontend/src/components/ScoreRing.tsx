"use client";

import { useEffect, useRef, useState } from "react";
import { scoreColor } from "@/lib/score";

interface Props {
  score: number; // 0–100
  size?: number; // px diameter
  label?: string;
  glow?: boolean;
}

export function ScoreRing({ score, size = 180, label, glow = false }: Props) {
  const target = Math.max(0, Math.min(100, Math.round(score)));
  const [display, setDisplay] = useState(0);
  const stroke = size >= 120 ? 12 : 7;
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;
  const color = scoreColor(target);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    const start = performance.now();
    const duration = 900;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setDisplay(Math.round(eased * target));
      if (t < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [target]);

  const offset = circumference - (display / 100) * circumference;

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      {glow && (
        <div
          className="absolute inset-0 rounded-full"
          style={{ boxShadow: `0 0 40px ${color}33` }}
        />
      )}
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--color-surface2)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-mono font-semibold leading-none"
          style={{ fontSize: size * 0.28, color }}
        >
          {display}
        </span>
        {label && (
          <span className="mt-1 text-xs font-medium uppercase tracking-wide text-faint">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}
