"use client";
import { useEffect, useState } from "react";
import PageShell from "@/components/layout/PageShell";
import TopBar from "@/components/layout/TopBar";
import StatCard from "@/components/ui/StatCard";
import MacWindowCard from "@/components/ui/MacWindowCard";
import StatusPill from "@/components/ui/StatusPill";
import RiskBadge from "@/components/ui/RiskBadge";
import Spinner from "@/components/ui/Spinner";
import { getDashboardSummary, getPayments, getChurnScores } from "@/lib/api";
import { formatCurrency, formatDate, deviceLabel } from "@/lib/utils";
import type { DashboardSummary, Payment, ChurnScore } from "@/lib/types";
import { Users, AlertTriangle, TrendingDown, DollarSign } from "lucide-react";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentPayments, setRecentPayments] = useState<Payment[]>([]);
  const [atRisk, setAtRisk] = useState<ChurnScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getDashboardSummary(),
      getPayments({ limit: "10" }),
      getChurnScores({ risk_level: "critical", limit: "5" }),
    ]).then(([s, p, c]) => {
      setSummary(s);
      setRecentPayments(p);
      setAtRisk(c);
    }).catch((err) => {
      setError(err?.message ?? "Failed to connect to the NomosFlow backend. Is the server running?");
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <PageShell>
        <div className="flex items-center justify-center h-64"><Spinner className="w-8 h-8" /></div>
      </PageShell>
    );
  }

  if (error) {
    return (
      <PageShell>
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <div className="bg-red-50 border border-red-200 rounded-card px-6 py-5 max-w-lg w-full">
            <div className="flex items-center gap-3 mb-2">
              <AlertTriangle className="text-red-600" size={20} />
              <p className="font-semibold text-red-700 text-sm">Backend Unavailable</p>
            </div>
            <p className="text-sm text-red-600">{error}</p>
            <p className="text-xs text-text-muted mt-3">Start the FastAPI server with <code className="bg-red-100 px-1 rounded">uvicorn app.main:app --reload</code> then refresh.</p>
          </div>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <TopBar title="Dashboard" subtitle="NomosFlow operations overview" />

      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Customers" value={summary?.total_customers ?? 0} icon={Users} />
        <StatCard label="Failed Payments" value={summary?.failed_payments ?? 0} icon={AlertTriangle} />
        <StatCard label="At-Risk Customers" value={summary?.at_risk_customers ?? 0} icon={TrendingDown} />
        <StatCard
          label="Revenue at Risk"
          value={formatCurrency(summary?.revenue_at_risk_eur ?? 0)}
          icon={DollarSign}
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <MacWindowCard title="Recent Payments">
          <div className="space-y-2">
            {recentPayments.length === 0 && (
              <p className="text-sm text-text-muted text-center py-8">No payments found</p>
            )}
            {recentPayments.map((p) => (
              <div key={p.id} className="flex items-center justify-between py-2 border-b border-border-card last:border-0">
                <div>
                  <p className="text-sm font-medium text-text-primary">{p.customer_name}</p>
                  <p className="text-xs text-text-muted">{formatDate(p.due_date)} · {deviceLabel(p.device_type ?? "")}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-text-primary">{formatCurrency(Number(p.amount_eur))}</span>
                  <StatusPill status={p.status} />
                </div>
              </div>
            ))}
          </div>
        </MacWindowCard>

        <MacWindowCard title="Critical Risk Alerts">
          <div className="space-y-3">
            {atRisk.length === 0 && (
              <p className="text-sm text-text-muted text-center py-8">No critical customers 🎉</p>
            )}
            {atRisk.map((c) => (
              <div key={c.id} className="p-3 rounded-lg border border-red-100 bg-red-50">
                <div className="flex items-start justify-between mb-1">
                  <p className="text-sm font-semibold text-text-primary">{c.customer_name}</p>
                  <RiskBadge risk={c.risk_level} score={c.score} />
                </div>
                <p className="text-xs text-text-secondary">{c.partner_name} · {deviceLabel(c.device_type ?? "")}</p>
                {c.action_suggested && (
                  <p className="text-xs text-red-700 mt-1 font-medium">→ {c.action_suggested}</p>
                )}
              </div>
            ))}
          </div>
        </MacWindowCard>
      </div>
    </PageShell>
  );
}
