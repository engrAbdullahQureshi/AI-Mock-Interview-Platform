"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles, FileText, MessagesSquare, ArrowRight, CheckCircle2, Clock } from "lucide-react";
import { Protected } from "@/components/Protected";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { api } from "@/lib/api";
import type { ResumeResponse, InterviewListResponse } from "@/lib/types";

export default function DashboardPage() {
  return (
    <Protected>
      <Dashboard />
    </Protected>
  );
}

function Dashboard() {
  const toast = useToast();
  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [interviews, setInterviews] = useState<InterviewListResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [r, i] = await Promise.all([api.listResumes(), api.listInterviews()]);
        setResumes(r.resumes);
        setInterviews(i.interviews);
      } catch {
        toast.error("Couldn't load your dashboard.");
      } finally {
        setLoading(false);
      }
    })();
  }, [toast]);

  const empty = !loading && resumes.length === 0 && interviews.length === 0;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold">Dashboard</h1>
          <p className="mt-1 text-sm text-muted">Your resumes and interview reports.</p>
        </div>
        <Link href="/analyze">
          <Button size="lg">
            <Sparkles className="h-4 w-4" /> New Interview Prep
          </Button>
        </Link>
      </div>

      {loading && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      )}

      {empty && (
        <EmptyState
          icon={Sparkles}
          title="Let's prep for a real job"
          description="Upload your resume, paste a job description, and run a tailored mock interview that scores you against the role."
          action={
            <Link href="/analyze">
              <Button size="lg">
                Start now <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          }
        />
      )}

      {!loading && !empty && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Recent resumes" action={<Link href="/resumes/new"><Button variant="secondary" size="sm">Upload</Button></Link>}>
            {resumes.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted">No resumes yet.</p>
            ) : (
              <ul className="space-y-2">
                {resumes.slice(0, 5).map((r) => (
                  <li
                    key={r.id}
                    className="flex items-center gap-3 rounded-[10px] border border-border bg-surface2 px-3 py-2.5"
                  >
                    <FileText className="h-4.5 w-4.5 shrink-0 text-accent" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {r.parsed_data?.full_name || r.file_name}
                      </p>
                      <p className="truncate text-xs text-faint">
                        {r.parsed_data?.skills?.slice(0, 4).join(" · ") || r.file_name}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card title="Recent interviews">
            {interviews.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted">No interviews yet.</p>
            ) : (
              <ul className="space-y-2">
                {interviews.slice(0, 5).map((iv) => {
                  const done = iv.status === "completed";
                  const href = done ? `/interview/${iv.id}/report` : `/interview/${iv.id}`;
                  return (
                    <li key={iv.id}>
                      <Link
                        href={href}
                        className="flex items-center gap-3 rounded-[10px] border border-border bg-surface2 px-3 py-2.5 transition-colors hover:border-accent/50"
                      >
                        <MessagesSquare className="h-4.5 w-4.5 shrink-0 text-accent" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">{iv.job_title}</p>
                          <p className="text-xs text-faint">{iv.question_count} questions</p>
                        </div>
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            done ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
                          }`}
                        >
                          {done ? <CheckCircle2 className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                          {done ? "Report" : "Active"}
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
