import { cn, riskLevelColor } from "@/lib/utils";

interface RiskBadgeProps {
  risk: string;
  score?: number;
  className?: string;
}

export default function RiskBadge({ risk, score, className }: RiskBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-pill text-xs font-semibold border",
        riskLevelColor(risk),
        className
      )}
    >
      <span className="capitalize">{risk}</span>
      {score !== undefined && <span className="opacity-70">· {score}</span>}
    </span>
  );
}
