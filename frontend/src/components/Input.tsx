import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";

const fieldBase =
  "w-full rounded-[12px] border border-border bg-surface2 px-3.5 py-2.5 text-sm text-text placeholder:text-faint transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/40";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, className = "", id, ...rest },
  ref,
) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="field-label">
          {label}
        </label>
      )}
      <input id={inputId} ref={ref} className={`${fieldBase} ${className}`} {...rest} />
    </div>
  );
});

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, className = "", id, ...rest },
  ref,
) {
  const areaId = id || label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={areaId} className="field-label">
          {label}
        </label>
      )}
      <textarea id={areaId} ref={ref} className={`${fieldBase} resize-none ${className}`} {...rest} />
    </div>
  );
});
