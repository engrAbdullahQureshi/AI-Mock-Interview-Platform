"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { MessagesSquare, Target, FileSearch, BarChart3, ArrowRight } from "lucide-react";
import { Button } from "@/components/Button";
import { useAuth } from "@/lib/auth";

export default function Landing() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-accent">
            <MessagesSquare className="h-4.5 w-4.5 text-white" />
          </div>
          <span className="font-display text-[15px] font-bold tracking-tight">Interview Coach</span>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/login">
            <Button variant="ghost">Log in</Button>
          </Link>
          <Link href="/register">
            <Button>Get started</Button>
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-3xl px-6 pt-20 pb-16 text-center">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          Scored against the job — not vibes
        </div>
        <h1 className="font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
          Practice the interview for the{" "}
          <span className="text-accent">exact job</span> you want.
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-lg text-muted">
          Upload your resume, paste a real job description, and run a tailored mock interview.
          Every answer is scored against ground truth — your facts and the job&apos;s — and the
          number is computed by deterministic code, not the model grading itself.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Link href="/register">
            <Button size="lg">
              Start a mock interview <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="secondary">
              Use demo account
            </Button>
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-4xl gap-4 px-6 pb-24 sm:grid-cols-3">
        {[
          { icon: FileSearch, title: "It reads your resume", body: "An LLM extracts a structured profile — skills, experience, education — as the candidate's facts." },
          { icon: Target, title: "It scores the fit", body: "Paste a JD and get an honest match score, with exactly what lines up and what to strengthen." },
          { icon: BarChart3, title: "It grades every answer", body: "Five dimensions per answer, aggregated deterministically into an auditable report." },
        ].map(({ icon: Icon, title, body }) => (
          <div key={title} className="rounded-[16px] border border-border bg-surface p-5">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-[10px] bg-accent/10">
              <Icon className="h-5 w-5 text-accent" />
            </div>
            <h3 className="font-display font-semibold">{title}</h3>
            <p className="mt-1.5 text-sm text-muted">{body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
