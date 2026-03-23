import { cn } from "@/lib/utils";

interface HighlightPhraseProps {
  children: React.ReactNode;
  className?: string;
}

export default function HighlightPhrase({ children, className }: HighlightPhraseProps) {
  return (
    <span
      className={cn(
        "inline px-1.5 py-0.5 rounded bg-accent-green text-white text-sm font-medium",
        className
      )}
    >
      {children}
    </span>
  );
}
