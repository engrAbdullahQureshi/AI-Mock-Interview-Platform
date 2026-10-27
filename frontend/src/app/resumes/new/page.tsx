"use client";

import { useState, useRef, type DragEvent } from "react";
import { useRouter } from "next/navigation";
import { UploadCloud, FileText, Mail, Phone, MapPin, Briefcase, GraduationCap, ArrowRight } from "lucide-react";
import { Protected } from "@/components/Protected";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Skeleton, SkeletonText } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { api } from "@/lib/api";
import { isApiError } from "@/lib/auth";
import type { ResumeResponse } from "@/lib/types";

const ACCEPT = ".pdf,.docx,.txt";

export default function ResumeUploadPage() {
  return (
    <Protected>
      <ResumeUpload />
    </Protected>
  );
}

function ResumeUpload() {
  const toast = useToast();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [resume, setResume] = useState<ResumeResponse | null>(null);

  async function handleFile(file: File) {
    if (file.size > 10 * 1024 * 1024) {
      toast.error("File too large — max 10MB.");
      return;
    }
    setUploading(true);
    setResume(null);
    try {
      const res = await api.uploadResume(file);
      setResume(res);
      if (!res.parsed_data) {
        toast.show("Uploaded, but AI parsing returned nothing. You can still continue.", "info");
      } else {
        toast.success("Resume parsed successfully.");
      }
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold">Upload your resume</h1>
        <p className="mt-1 text-sm text-muted">
          PDF, DOCX or TXT (max 10MB). We extract a structured profile with an LLM.
        </p>
      </div>

      {!resume && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-[16px] border-2 border-dashed px-6 py-16 text-center transition-colors ${
            dragging ? "border-accent bg-accent/5" : "border-border bg-surface/50 hover:border-accent/50"
          }`}
        >
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10">
            <UploadCloud className="h-7 w-7 text-accent" />
          </div>
          <p className="font-display text-lg font-semibold">Drop your resume here</p>
          <p className="mt-1 text-sm text-muted">or click to browse</p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
        </div>
      )}

      {uploading && (
        <Card>
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 shrink-0 rounded-full shimmer" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <p className="mt-4 text-sm text-muted">Reading your resume…</p>
          <div className="mt-3">
            <SkeletonText lines={3} />
          </div>
        </Card>
      )}

      {resume && <ParsedProfile resume={resume} onContinue={() => router.push(`/analyze?resume=${resume.id}`)} onReset={() => setResume(null)} />}
    </div>
  );
}

function ParsedProfile({
  resume,
  onContinue,
  onReset,
}: {
  resume: ResumeResponse;
  onContinue: () => void;
  onReset: () => void;
}) {
  const p = resume.parsed_data;
  return (
    <div className="space-y-5 animate-[rise_0.35s_ease-out]">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 font-display text-lg font-bold text-accent">
              {(p?.full_name || resume.file_name).charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="font-display text-xl font-bold">{p?.full_name || resume.file_name}</h2>
              {p?.summary && <p className="mt-0.5 max-w-lg text-sm text-muted line-clamp-2">{p.summary}</p>}
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-surface2 px-3 py-1 text-xs text-muted">
            <FileText className="h-3.5 w-3.5" /> {resume.file_name}
          </span>
        </div>

        {p && (
          <div className="mt-4 flex flex-wrap gap-4 text-sm text-muted">
            {p.email && <span className="inline-flex items-center gap-1.5"><Mail className="h-4 w-4 text-faint" />{p.email}</span>}
            {p.phone && <span className="inline-flex items-center gap-1.5"><Phone className="h-4 w-4 text-faint" />{p.phone}</span>}
            {p.location && <span className="inline-flex items-center gap-1.5"><MapPin className="h-4 w-4 text-faint" />{p.location}</span>}
          </div>
        )}
      </Card>

      {p?.skills && p.skills.length > 0 && (
        <Card title="Skills">
          <div className="flex flex-wrap gap-2">
            {p.skills.map((s) => (
              <span key={s} className="rounded-full bg-accent/10 px-3 py-1 text-sm font-medium text-accent">
                {s}
              </span>
            ))}
          </div>
        </Card>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        {p?.work_experience && p.work_experience.length > 0 && (
          <Card title="Experience">
            <ol className="space-y-4">
              {p.work_experience.map((w, i) => (
                <li key={i} className="relative border-l border-border pl-4">
                  <span className="absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full bg-accent" />
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-4 w-4 text-faint" />
                    <p className="font-medium">{w.position || "—"}</p>
                  </div>
                  <p className="text-sm text-muted">{w.company}{w.duration ? ` · ${w.duration}` : ""}</p>
                  {w.description && <p className="mt-1 text-sm text-faint line-clamp-2">{w.description}</p>}
                </li>
              ))}
            </ol>
          </Card>
        )}

        {p?.education && p.education.length > 0 && (
          <Card title="Education">
            <ol className="space-y-4">
              {p.education.map((ed, i) => (
                <li key={i} className="flex items-start gap-2">
                  <GraduationCap className="mt-0.5 h-4 w-4 shrink-0 text-faint" />
                  <div>
                    <p className="font-medium">{ed.degree}{ed.field ? `, ${ed.field}` : ""}</p>
                    <p className="text-sm text-muted">{ed.institution}{ed.year ? ` · ${ed.year}` : ""}</p>
                  </div>
                </li>
              ))}
            </ol>
          </Card>
        )}
      </div>

      <div className="flex items-center justify-between gap-3">
        <Button variant="ghost" onClick={onReset}>
          Upload a different resume
        </Button>
        <Button size="lg" onClick={onContinue}>
          Next: target a job <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
