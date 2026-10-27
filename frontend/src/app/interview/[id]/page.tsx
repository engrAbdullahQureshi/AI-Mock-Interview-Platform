"use client";

import { use, useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import { Send, Square, Loader2 } from "lucide-react";
import { Protected } from "@/components/Protected";
import { Button } from "@/components/Button";
import { ChatBubble, TypingBubble } from "@/components/ChatBubble";
import { ProgressBar } from "@/components/ProgressBar";
import { useToast } from "@/components/Toast";
import { api, wsUrl } from "@/lib/api";
import type { InterviewResponse, WsMessage } from "@/lib/types";

interface ChatMsg {
  role: "ai" | "user";
  content: string;
}

export default function InterviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <Protected>
      <Interview id={id} />
    </Protected>
  );
}

function Interview({ id }: { id: string }) {
  const toast = useToast();
  const router = useRouter();

  const [interview, setInterview] = useState<InterviewResponse | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [draft, setDraft] = useState("");
  const [waiting, setWaiting] = useState(true); // waiting on AI
  const [connected, setConnected] = useState(false);
  const [finished, setFinished] = useState(false);
  const [qIndex, setQIndex] = useState(0);
  const [total, setTotal] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const openedRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load interview meta (title + total questions)
  useEffect(() => {
    api
      .getInterview(id)
      .then((iv) => {
        setInterview(iv);
        setTotal(iv.questions.length);
        if (iv.status === "completed") {
          router.replace(`/interview/${id}/report`);
        }
      })
      .catch(() => toast.error("Couldn't load this interview."));
  }, [id, router, toast]);

  // Open WebSocket
  useEffect(() => {
    if (openedRef.current) return;
    openedRef.current = true;

    const ws = new WebSocket(wsUrl(id));
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (ev) => {
      let msg: WsMessage;
      try {
        msg = JSON.parse(ev.data);
      } catch {
        return;
      }
      if (msg.type === "ai") {
        setMessages((m) => [...m, { role: "ai", content: msg.content }]);
        if (typeof msg.question_index === "number") setQIndex(msg.question_index);
        if (typeof msg.total_questions === "number") setTotal(msg.total_questions);
        setWaiting(false);
      } else if (msg.type === "complete") {
        setMessages((m) => [...m, { role: "ai", content: msg.content }]);
        setWaiting(false);
        setFinished(true);
        setTimeout(() => router.push(`/interview/${id}/report`), 2200);
      } else if (msg.type === "error") {
        toast.error(msg.content || "Interview error.");
        setWaiting(false);
      }
    };

    ws.onerror = () => {
      toast.error("Connection problem. Is the backend running?");
      setWaiting(false);
    };

    ws.onclose = (ev) => {
      setConnected(false);
      if (!finished && ev.code === 1008) {
        toast.error("Session rejected — please log in again.");
      }
    };

    return () => {
      ws.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, waiting]);

  function send() {
    const text = draft.trim();
    if (!text || waiting || finished) return;
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      toast.error("Not connected.");
      return;
    }
    ws.send(text);
    setMessages((m) => [...m, { role: "user", content: text }]);
    setDraft("");
    setWaiting(true);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function endInterview() {
    wsRef.current?.close();
    router.push(`/interview/${id}/report`);
  }

  const progress = total > 0 ? Math.min(total, qIndex + 1) : 0;

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-[760px] flex-col md:h-[calc(100vh-4rem)]">
      {/* Sticky header */}
      <div className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-border bg-bg/80 pb-4 pt-2 backdrop-blur">
        <div className="min-w-0">
          <h1 className="truncate font-display text-lg font-bold">
            {interview?.job_title || "Interview"}
          </h1>
          <p className="text-xs text-faint">
            {connected ? (
              <span className="inline-flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-success" /> Live
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" /> Connecting…
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden w-40 sm:block">
            <p className="mb-1 text-right text-xs text-faint">
              {total > 0 ? `Question ${progress} / ${total}` : ""}
            </p>
            <ProgressBar value={progress} max={total || 1} />
          </div>
          {!finished && (
            <Button variant="secondary" size="sm" onClick={endInterview}>
              <Square className="h-3.5 w-3.5" /> End
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto py-6">
        {messages.length === 0 && waiting && (
          <div className="flex flex-col items-center justify-center py-16 text-center text-sm text-muted">
            <Loader2 className="mb-3 h-5 w-5 animate-spin text-accent" />
            Your interviewer is getting ready…
          </div>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role}>
            {m.content}
          </ChatBubble>
        ))}
        {waiting && messages.length > 0 && <TypingBubble />}
        {finished && (
          <div className="rounded-[12px] border border-accent/30 bg-accent/5 px-4 py-3 text-center text-sm text-muted">
            Interview complete — building your report…
          </div>
        )}
      </div>

      {/* Input bar */}
      {!finished && (
        <div className="sticky bottom-0 border-t border-border bg-bg/80 pb-2 pt-3 backdrop-blur">
          <div className="flex items-end gap-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              disabled={waiting || !connected}
              placeholder={waiting ? "Waiting for the interviewer…" : "Type your answer…"}
              className="max-h-40 min-h-[48px] flex-1 resize-none rounded-[12px] border border-border bg-surface2 px-3.5 py-3 text-sm text-text placeholder:text-faint focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-60"
            />
            <Button size="lg" onClick={send} disabled={waiting || !connected || !draft.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mt-1.5 px-1 text-xs text-faint">Press Enter to send · Shift+Enter for a new line</p>
        </div>
      )}
    </div>
  );
}
