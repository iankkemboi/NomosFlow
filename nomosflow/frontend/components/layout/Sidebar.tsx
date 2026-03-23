"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, AlertCircle, MessageSquare, Building2, Home } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard",  label: "Dashboard",  icon: LayoutDashboard },
  { href: "/customers",  label: "Customers",  icon: Users },
  { href: "/dunning",    label: "Dunning",    icon: AlertCircle },
  { href: "/retention",  label: "Retention",  icon: MessageSquare },
  { href: "/partners",   label: "Partners",   icon: Building2 },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-bg-sidebar border-r border-border-card flex flex-col z-30">
      <div className="px-5 py-5 border-b border-border-card">
        <span className="font-heading font-bold text-lg text-text-primary tracking-tight">NomosFlow</span>
        <p className="text-xs text-text-muted mt-0.5">AI Dunning Engine</p>
      </div>
      <nav className="flex-1 py-4 px-2 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                active
                  ? "bg-accent-green-light text-accent-green border-l-2 border-accent-green pl-[10px]"
                  : "text-text-secondary hover:bg-white hover:text-text-primary"
              )}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-4 border-t border-border-card space-y-3">
        <Link
          href="/"
          className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium text-text-secondary hover:bg-white hover:text-text-primary transition-all w-full"
        >
          <Home size={15} />
          Back to Home
        </Link>
        <p className="text-xs text-text-muted px-3">NomosFlow</p>
      </div>
    </aside>
  );
}
