import { Bot } from "lucide-react";
import type { ReactNode } from "react";

export function ChatBubble({
  role,
  children,
}: {
  role: "ai" | "user";
  children: ReactNode;
}) {
  if (role === "ai") {
    return (
      <div className="flex items-start gap-3 animate-[rise_0.3s_ease-out]">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/15 text-accent">
          <Bot className="h-4.5 w-4.5" />
        </div>
        <div className="max-w-[75%] rounded-[16px] rounded-tl-sm border border-border bg-surface2 px-4 py-3 text-sm leading-relaxed text-text whitespace-pre-wrap">
          {children}
        </div>
      </div>
    );
  }
  return (
    <div className="flex justify-end animate-[rise_0.3s_ease-out]">
      <div className="max-w-[75%] rounded-[16px] rounded-tr-sm bg-accent/15 px-4 py-3 text-sm leading-relaxed text-text whitespace-pre-wrap">
        {children}
      </div>
    </div>
  );
}

export function TypingBubble() {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/15 text-accent">
        <Bot className="h-4.5 w-4.5" />
      </div>
      <div className="flex items-center gap-1 rounded-[16px] rounded-tl-sm border border-border bg-surface2 px-4 py-4">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="typing-dot h-2 w-2 rounded-full bg-muted"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
