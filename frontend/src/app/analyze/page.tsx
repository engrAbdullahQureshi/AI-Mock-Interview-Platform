"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Sparkles, FileUp, ArrowRight, Wand2 } from "lucide-react";
import { Protected } from "@/components/Protected";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Textarea } from "@/components/Input";
import { ScoreRing } from "@/components/ScoreRing";
import { SkillChip } from "@/components/SkillChip";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/auth";
import { SAMPLE_JD } from "@/lib/sampleJd";
import type { ResumeResponse, GapAnalysis } from "@/lib/types";

export default function AnalyzePage() {
  return (
    <Protected>
      <Suspense fallback={<div className="py-10"><Skeleton className="h-64" /></div>}>
        <Analyze />
      </Suspense>
    </Protected>
  );
}

function jobTitleFromJd(jd: string): string {
  const firstLine = jd.split("\n").map((l) => l.trim()).find((l) => l.length > 0) || "Target Role";
  return firstLine.split(/[—\-|(]/)[0].trim().slice(0, 80) || "Target Role";
}

function Analyze() {
  const toast = useToast();
  const router = useRouter();
  const params = useSearchParams();

  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [resumeId, setResumeId] = useState<string>("");
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [jd, setJd] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [starting, setStarting] = useState(false);
  const [result, setResult] = useState<GapAnalysis | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { resumes } = await api.listResumes();
        setResumes(resumes);
        const fromQuery = params.get("resume");
        setResumeId(fromQuery && resumes.some((r) => r.id === fromQuery) ? fromQuery : resumes[0]?.id || "");
      } catch {
        toast.error("Couldn't load your resumes.");
      } finally {
        setLoadingResumes(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function analyze() {
    if (!resumeId) return toast.error("Select a resume first.");
    if (jd.trim().length < 40) return toast.error("Paste a fuller job description.");
    setAnalyzing(true);
    setResult(null);
    try {
      setResult(await api.gapAnalysis(resumeId, jd));
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }

  async function startInterview() {
    if (!result) return;
    setStarting(true);
    try {
      const iv = await api.createInterview({
        resume_id: resumeId,
        job_title: jobTitleFromJd(jd),
        num_questions: 8,
        job_description: jd,
        focus_skills: result.missing_skills,
      });
      router.push(`/interview/${iv.id}`);
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Couldn't start the interview.");
      setStarting(false);
    }
  }

  if (loadingResumes) {
    return <div className="py-6"><Skeleton className="h-72" /></div>;
  }

  if (resumes.length === 0) {
    return (
      <EmptyState
        icon={FileUp}
        title="Upload a resume first"
        description="We need your resume to score you against a job and tailor the interview."
        action={<Link href="/resumes/new"><Button size="lg">Upload resume <ArrowRight className="h-4 w-4" /></Button></Link>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold">Target a job</h1>
          <p className="mt-1 text-sm text-muted">Paste a job description and see how you stack up — honestly.</p>
        </div>
        {resumes.length > 1 && (
          <div className="flex flex-col gap-1.5">
            <label className="field-label">Resume</label>
            <select
              value={resumeId}
              onChange={(e) => setResumeId(e.target.value)}
              className="rounded-[12px] border border-border bg-surface2 px-3 py-2 text-sm text-text focus:border-accent focus:outline-none"
            >
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.parsed_data?.full_name || r.file_name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-[45%_55%]">
        {/* JD input */}
        <Card
          title="Job description"
          action={
            <Button variant="ghost" size="sm" onClick={() => setJd(SAMPLE_JD)}>
              <Wand2 className="h-3.5 w-3.5" /> Load sample JD
            </Button>
          }
        >
          <Textarea
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste the full job description here…"
            rows={16}
          />
          <Button className="mt-4 w-full" size="lg" loading={analyzing} onClick={analyze}>
            <Sparkles className="h-4 w-4" /> Analyze fit
          </Button>
        </Card>

        {/* Results */}
        <div>
          {analyzing && <AnalyzingSkeleton />}
          {!analyzing && !result && (
            <div className="flex h-full min-h-[320px] items-center justify-center rounded-[16px] border border-dashed border-border bg-surface/40 px-6 text-center">
              <p className="max-w-xs text-sm text-muted">
                Your match score and skill breakdown will appear here once you analyze.
              </p>
            </div>
          )}
          {result && (
            <div className="space-y-5 animate-[rise_0.35s_ease-out]">
              <Card>
                <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center">
                  <ScoreRing score={result.match_score} size={150} label="match" glow />
                  <div className="flex-1 text-center sm:text-left">
                    <p className="font-display text-lg font-semibold">{result.verdict}</p>
                    <p className="mt-1.5 text-sm text-muted">{result.summary}</p>
                  </div>
                </div>
              </Card>

              <Card title="What lines up" subtitle={`${result.matched_skills.length} matched`}>
                <div className="flex flex-wrap gap-2">
                  {result.matched_skills.map((s) => (
                    <SkillChip key={s} label={s} kind="matched" />
                  ))}
                </div>
              </Card>

              {result.missing_skills.length > 0 && (
                <Card title="To strengthen" subtitle="The interview will probe these">
                  <div className="flex flex-wrap gap-2">
                    {result.missing_skills.map((s) => (
                      <SkillChip key={s} label={s} kind="missing" />
                    ))}
                  </div>
                </Card>
              )}

              <Button size="lg" className="w-full" loading={starting} onClick={startInterview}>
                Start tailored interview <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AnalyzingSkeleton() {
  return (
    <div className="space-y-5">
      <Card>
        <div className="flex items-center gap-4">
          <div className="h-[150px] w-[150px] shrink-0 rounded-full shimmer" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-5/6" />
          </div>
        </div>
      </Card>
      <Card>
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-7 w-24 rounded-full" />
          ))}
        </div>
      </Card>
    </div>
  );
}
