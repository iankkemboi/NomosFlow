"use client";
import { cn } from "@/lib/utils";

interface MacWindowCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export default function MacWindowCard({ title, children, className, action }: MacWindowCardProps) {
  return (
    <div className={cn("bg-white rounded-card border border-border-card shadow-card overflow-hidden", className)}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-card bg-bg-page">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
            <span className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
            <span className="w-3 h-3 rounded-full bg-[#28CA41]" />
          </div>
          <h2 className="font-heading text-sm font-semibold text-text-primary">{title}</h2>
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
