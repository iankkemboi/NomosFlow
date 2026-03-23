import { cn, statusColor } from "@/lib/utils";

interface StatusPillProps {
  status: string;
  className?: string;
}

const STATUS_LABELS: Record<string, string> = {
  paid: "Paid",
  failed: "Failed",
  retrying: "Retrying",
  pending: "Pending",
  written_off: "Written Off",
  active: "Active",
  suspended: "Suspended",
  cancelled: "Cancelled",
};

export default function StatusPill({ status, className }: StatusPillProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-pill text-xs font-medium border",
        statusColor(status),
        className
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}
