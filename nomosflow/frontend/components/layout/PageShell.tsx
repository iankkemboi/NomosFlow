import { cn } from "@/lib/utils";

interface PageShellProps {
  children: React.ReactNode;
  className?: string;
}

export default function PageShell({ children, className }: PageShellProps) {
  return (
    <main className={cn("ml-60 min-h-screen bg-bg-page p-8", className)}>
      {children}
    </main>
  );
}
