"use client";
import { useEffect, useRef, useState } from "react";
import PageShell from "@/components/layout/PageShell";
import TopBar from "@/components/layout/TopBar";
import MacWindowCard from "@/components/ui/MacWindowCard";
import StatusPill from "@/components/ui/StatusPill";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import DeviceIcon from "@/components/ui/DeviceIcon";
import { getDunningQueue, runDunningCycle } from "@/lib/api";
import { formatCurrency, formatDate, deviceLabel } from "@/lib/utils";

const BATCH_SIZE = 10;

interface QueueItem {
  payment_id: string;
  customer_id: string;
  customer_name: string;
  device_type: string;
  amount_eur: number;
  status: string;
  failure_reason: string | null;
  retry_count: number;
  max_retries: number;
  next_retry_date: string | null;
  due_date: string;
}

export default function DunningPage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [cycleResult, setCycleResult] = useState<{ processed: number; errors: unknown[]; queue_remaining?: number; actions?: { by?: string }[] } | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = () => {
    setLoading(true);
    getDunningQueue()
      .then((q) => setQueue(q as unknown as QueueItem[]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleRunCycle = async () => {
    setRunning(true);
    setCycleResult(null);
    setElapsed(0);
    timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    try {
      const result = await runDunningCycle(undefined, BATCH_SIZE);
      setCycleResult(result);
      load();
    } finally {
      setRunning(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  return (
    <PageShell>
      <TopBar
        title="Dunning Queue"
        subtitle="Failed & retrying payments awaiting AI processing"
        action={
          <Button onClick={handleRunCycle} loading={running} disabled={running}>
            {running ? "Running AI Cycle…" : "Run Dunning Cycle"}
          </Button>
        }
      />

      {running && (
        <div className="mb-5 p-4 bg-[#EBF2E6] border border-accent-green/20 rounded-card flex items-center gap-3">
          <Spinner className="w-4 h-4 text-accent-green" />
          <div className="text-sm text-accent-green font-medium">
            Processing batch of up to {BATCH_SIZE} payments with AI classification…
            <span className="ml-2 text-xs text-text-muted font-normal">({elapsed}s elapsed)</span>
          </div>
        </div>
      )}

      {!running && cycleResult && (() => {
        const aiCount = cycleResult.actions?.filter(a => a.by === "ai").length ?? 0;
        const ruleCount = cycleResult.actions?.filter(a => a.by === "rules").length ?? 0;
        return (
          <div className="mb-5 p-4 bg-accent-green-light border border-accent-green/20 rounded-card text-sm text-accent-green font-medium flex items-center justify-between">
            <span>✓ Batch complete — {cycleResult.processed} payment(s) processed in {elapsed}s.</span>
            <div className="flex items-center gap-3 text-xs">
              {aiCount > 0 && <span className="text-accent-green">{aiCount} AI classified</span>}
              {ruleCount > 0 && <span className="text-text-muted">{ruleCount} rule fallback</span>}
              {cycleResult.errors.length > 0 && (
                <span className="text-orange-600">{cycleResult.errors.length} error(s)</span>
              )}
              {(cycleResult.queue_remaining ?? 0) > 0 && (
                <span className="text-text-muted">{cycleResult.queue_remaining} remaining — run again</span>
              )}
            </div>
          </div>
        );
      })()}

      <MacWindowCard title={`Dunning Queue (${queue.length})`}>
        {loading ? (
          <div className="flex justify-center py-16"><Spinner className="w-8 h-8" /></div>
        ) : queue.length === 0 ? (
          <EmptyState title="Queue is clear" description="No failed or retrying payments." />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-card text-left text-text-muted text-xs font-medium uppercase tracking-wide">
                <th className="pb-3 pr-4">Customer</th>
                <th className="pb-3 pr-4">Device</th>
                <th className="pb-3 pr-4">Amount</th>
                <th className="pb-3 pr-4">Status</th>
                <th className="pb-3 pr-4">Failure Reason</th>
                <th className="pb-3 pr-4">Retries</th>
                <th className="pb-3 pr-4">Due Date</th>
                <th className="pb-3">Next Retry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-card">
              {queue.map((item) => (
                <tr key={item.payment_id} className="hover:bg-bg-page transition-colors">
                  <td className="py-3 pr-4 font-medium text-text-primary">{item.customer_name}</td>
                  <td className="py-3 pr-4">
                    <span className="flex items-center gap-1.5 text-text-secondary">
                      <DeviceIcon deviceType={item.device_type} size={14} />
                      {deviceLabel(item.device_type)}
                    </span>
                  </td>
                  <td className="py-3 pr-4 font-semibold text-text-primary">{formatCurrency(item.amount_eur)}</td>
                  <td className="py-3 pr-4"><StatusPill status={item.status} /></td>
                  <td className="py-3 pr-4 text-text-secondary capitalize">
                    {item.failure_reason?.replace(/_/g, " ") ?? "—"}
                  </td>
                  <td className="py-3 pr-4">
                    <span className={`text-sm font-medium ${item.retry_count >= item.max_retries ? "text-red-600" : "text-text-secondary"}`}>
                      {item.retry_count} / {item.max_retries}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-text-muted">{formatDate(item.due_date)}</td>
                  <td className="py-3 text-text-muted">
                    {item.next_retry_date ? formatDate(item.next_retry_date) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </MacWindowCard>
    </PageShell>
  );
}
