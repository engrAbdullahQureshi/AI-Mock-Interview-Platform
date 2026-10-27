"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  TrendingUp,
  Target,
  Printer,
  RotateCcw,
  Loader2,
  Calendar,
} from "lucide-react";
import { Protected } from "@/components/Protected";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { ScoreRing } from "@/components/ScoreRing";
import { DimensionChart } from "@/components/DimensionChart";
import { AccordionItem } from "@/components/Accordion";
import { StatBadge } from "@/components/SkillChip";
import { useToast } from "@/components/Toast";
import { ApiError, api } from "@/lib/api";
import { DIMENSION_LABELS, type InterviewReport, type Dimensions } from "@/lib/types";
import { verdictFromScore } from "@/lib/score";

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <Protected>
      <Report id={id} />
    </Protected>
  );
}

function Report({ id }: { id: string }) {
  const toast = useToast();
  const router = useRouter();
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [status, setStatus] = useState<"loading" | "scoring" | "error">("loading");

  useEffect(() => {
    let cancelled = false;
    let attempts = 0;

    async function fetchReport() {
      try {
        const r = await api.getReport(id);
        if (!cancelled) {
          setReport(r);
          setStatus("loading");
        }
      } catch (err) {
        // 409 = interview not completed / report not ready yet → retry a few times
        if (err instanceof ApiError && err.status === 409 && attempts < 8) {
          attempts++;
          if (!cancelled) setStatus("scoring");
          setTimeout(fetchReport, 1500);
        } else if (!cancelled) {
          setStatus("error");
          toast.error(err instanceof ApiError ? err.message : "Couldn't load the report.");
        }
      }
    }
    fetchReport();
    return () => {
      cancelled = true;
    };
  }, [id, toast]);

  if (!report) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
        <Loader2 className="mb-4 h-7 w-7 animate-spin text-accent" />
        <p className="font-display text-lg font-semibold">
          {status === "scoring" ? "Scoring your interview…" : "Loading report…"}
        </p>
        <p className="mt-1 text-sm text-muted">
          {status === "scoring"
            ? "The model is grading each answer against your resume and the job."
            : "One moment."}
        </p>
        {status === "error" && (
          <Button className="mt-6" variant="secondary" onClick={() => router.push("/dashboard")}>
            Back to dashboard
          </Button>
        )}
      </div>
    );
  }

  const date = report.completed_at ? new Date(report.completed_at).toLocaleDateString() : "—";

  return (
    <div className="print-single space-y-6">
      {/* Header actions */}
      <div className="no-print flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Interview Report</h1>
          <p className="mt-1 text-sm text-muted">Every answer scored against ground truth.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => router.push("/analyze")}>
            <RotateCcw className="h-4 w-4" /> Retake
          </Button>
          <Button onClick={() => window.print()}>
            <Printer className="h-4 w-4" /> Export report
          </Button>
        </div>
      </div>

      {/* Top row: overall score + verdict */}
      <Card>
        <div className="flex flex-col items-center gap-6 sm:flex-row">
          <ScoreRing score={report.overall_score} size={180} label="overall" glow />
          <div className="flex-1 text-center sm:text-left">
            <p className="font-display text-xl font-bold">
              {report.verdict || verdictFromScore(report.overall_score)}
            </p>
            <p className="mt-2 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-sm text-muted sm:justify-start">
              <span className="inline-flex items-center gap-1.5">
                <Target className="h-4 w-4 text-faint" /> {report.job_title}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Calendar className="h-4 w-4 text-faint" /> {date}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-faint" /> {report.per_question.length} answers scored
              </span>
            </p>
            <p className="mt-3 rounded-[10px] bg-surface2 px-3 py-2 text-xs text-muted">
              The model judged each answer across five dimensions; the overall number is aggregated
              by deterministic code — so it&apos;s reproducible, not the model grading itself.
            </p>
          </div>
        </div>
      </Card>

      {/* Second row: dimensions + strengths/improvements */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Dimension breakdown">
          <DimensionChart dimensions={report.dimensions} />
          <div className="mt-2 grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-3">
            {(Object.keys(DIMENSION_LABELS) as (keyof Dimensions)[]).map((k) => (
              <div key={k} className="flex items-center justify-between gap-2">
                <span className="text-xs text-muted">{DIMENSION_LABELS[k]}</span>
                <StatBadge score={report.dimensions[k]} />
              </div>
            ))}
          </div>
        </Card>

        <div className="space-y-6">
          <Card title="Strengths" action={<TrendingUp className="h-4 w-4 text-success" />}>
            <ul className="space-y-2.5">
              {report.strengths.map((s, i) => (
                <li key={i} className="flex gap-2.5 text-sm">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  <span className="text-muted">{s}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Areas to improve" action={<Target className="h-4 w-4 text-warning" />}>
            <ul className="space-y-2.5">
              {report.improvements.map((s, i) => (
                <li key={i} className="flex gap-2.5 text-sm">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-warning" />
                  <span className="text-muted">{s}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>

      {/* JD gap recap */}
      {report.jd_gap_recap && (
        <Card title="How the JD gaps were handled">
          <p className="text-sm leading-relaxed text-muted">{report.jd_gap_recap}</p>
        </Card>
      )}

      {/* Per-question breakdown */}
      <div>
        <h2 className="mb-3 font-display text-lg font-semibold">Per-question breakdown</h2>
        <div className="space-y-2.5">
          {report.per_question.map((q) => {
            const overall = Math.round(
              (q.scores.relevance +
                q.scores.technical_depth +
                q.scores.communication +
                q.scores.specificity +
                q.scores.jd_alignment) /
                5,
            );
            return (
              <AccordionItem
                key={q.index}
                header={
                  <div className="flex items-center gap-3">
                    <StatBadge score={overall} />
                    <span className="truncate text-sm font-medium text-text">
                      Q{q.index}. {q.question}
                    </span>
                  </div>
                }
              >
                <div className="space-y-4">
                  <div>
                    <p className="field-label mb-1">Your answer</p>
                    <p className="whitespace-pre-wrap text-sm text-muted">{q.answer || "—"}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-3">
                    {(Object.keys(DIMENSION_LABELS) as (keyof Dimensions)[]).map((k) => (
                      <div key={k} className="flex items-center justify-between gap-2">
                        <span className="text-xs text-muted">{DIMENSION_LABELS[k]}</span>
                        <StatBadge score={q.scores[k]} />
                      </div>
                    ))}
                  </div>
                  <div className="rounded-[10px] border border-border bg-surface2 px-3 py-2.5">
                    <p className="field-label mb-1">Feedback</p>
                    <p className="text-sm text-text">{q.feedback}</p>
                  </div>
                </div>
              </AccordionItem>
            );
          })}
        </div>
      </div>
    </div>
  );
}
