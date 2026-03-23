import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  trend?: string;
  trendUp?: boolean;
  className?: string;
}

export default function StatCard({ label, value, icon: Icon, trend, trendUp, className }: StatCardProps) {
  return (
    <div className={cn("bg-white rounded-card border border-border-card shadow-card p-5 flex flex-col gap-2", className)}>
      <div className="flex items-start justify-between">
        <span className="text-xs text-text-muted font-medium uppercase tracking-wide">{label}</span>
        {Icon && (
          <span className="w-8 h-8 rounded-lg bg-accent-green-light flex items-center justify-center">
            <Icon size={16} className="text-accent-green" />
          </span>
        )}
      </div>
      <div className="text-3xl font-semibold text-text-primary font-heading">{value}</div>
      {trend && (
        <div className={cn("text-xs font-medium", trendUp ? "text-green-600" : "text-red-500")}>
          {trendUp ? "↑" : "↓"} {trend}
        </div>
      )}
    </div>
  );
}
