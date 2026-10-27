"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import type { Dimensions } from "@/lib/types";
import { DIMENSION_LABELS } from "@/lib/types";

export function DimensionChart({ dimensions }: { dimensions: Dimensions }) {
  const data = (Object.keys(DIMENSION_LABELS) as (keyof Dimensions)[]).map((k) => ({
    dimension: DIMENSION_LABELS[k],
    score: dimensions[k],
  }));

  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="#262e3d" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: "#9aa6b9", fontSize: 12 }}
          />
          <PolarRadiusAxis
            domain={[0, 100]}
            tick={{ fill: "#5e6b82", fontSize: 10 }}
            axisLine={false}
          />
          <Radar
            dataKey="score"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.3}
            strokeWidth={2}
            isAnimationActive
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
