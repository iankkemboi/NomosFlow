import { InboxIcon } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
}

export default function EmptyState({
  title = "Nothing here",
  description = "No records to display.",
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <InboxIcon size={36} className="text-text-muted" />
      <div>
        <p className="font-medium text-text-secondary">{title}</p>
        <p className="text-sm text-text-muted mt-1">{description}</p>
      </div>
    </div>
  );
}
