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

const BATCH_SIZE = 20;

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
  const [progress, setProgress] = useState<{ processed: number; total: number; batches: number } | null>(null);
  const [cycleResult, setCycleResult] = useState<{ processed: number; errors: unknown[]; skipped: number; quotaHit: boolean } | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cancelRef = useRef(false);

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
    cancelRef.current = false;

    const initialQueue = await getDunningQueue() as unknown as QueueItem[];
    const total = initialQueue.length;
    if (total === 0) { setRunning(false); return; }

    setProgress({ processed: 0, total, batches: 0 });
    timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);

    let totalProcessed = 0;
    let totalErrors: unknown[] = [];
    let batches = 0;
    let remaining = total;
    let prevRemaining = total + 1;
    let quotaHit = false;

    try {
      while (remaining > 0 && remaining < prevRemaining && !cancelRef.current) {
        const result = await runDunningCycle(undefined, BATCH_SIZE);
        batches += 1;
        totalProcessed += result.processed;
        totalErrors = [...totalErrors, ...result.errors];
        prevRemaining = remaining;
        remaining = result.queue_remaining ?? 0;
        if (remaining >= prevRemaining) {
          quotaHit = true;
          break;
        }
        const cleared = total - remaining;
        setProgress({ processed: cleared, total, batches });
      }

      setCycleResult({ processed: totalProcessed, errors: totalErrors, skipped: total - remaining - totalProcessed, quotaHit });
      load();
    } finally {
      setRunning(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const progressPct = progress && progress.total > 0
    ? Math.min(100, Math.round((progress.processed / progress.total) * 100))
    : 0;

  return (
    <PageShell>
      <TopBar
        title="Dunning Queue"
        subtitle="Failed & retrying payments — AI classifies and schedules retries"
        action={
          <Button onClick={handleRunCycle} loading={running} disabled={running || queue.length === 0}>
            {running ? "Processing…" : "Run AI Dunning Cycle"}
          </Button>
        }
      />

      {running && progress && (
        <div className="mb-5 p-4 bg-[#EBF2E6] border border-accent-green/20 rounded-card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-sm text-accent-green font-medium">
              <Spinner className="w-4 h-4 text-accent-green" />
              AI classifying {progress.total} payment{progress.total !== 1 ? "s" : ""}…
            </div>
            <span className="text-xs text-text-muted">{elapsed}s elapsed · batch {progress.batches}</span>
          </div>
          <div className="w-full bg-accent-green/10 rounded-full h-1.5">
            <div
              className="bg-accent-green h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <div className="mt-1.5 text-xs text-text-muted">
            {progress.processed} of {progress.total} processed
          </div>
        </div>
      )}

      {!running && cycleResult && (
        <div className={`mb-5 p-4 border rounded-card text-sm font-medium flex items-center justify-between ${
          cycleResult.quotaHit
            ? "bg-orange-50 border-orange-200"
            : "bg-accent-green-light border-accent-green/20"
        }`}>
          {cycleResult.quotaHit ? (
            <span className="text-orange-700">
              ⚠ AI quota reached — {cycleResult.processed} payment{cycleResult.processed !== 1 ? "s" : ""} classified before limit hit. Remaining payments stay in queue.
            </span>
          ) : (
            <span className="text-accent-green">
              ✓ Done — {cycleResult.processed} payment{cycleResult.processed !== 1 ? "s" : ""} classified in {elapsed}s
            </span>
          )}
          <div className="flex items-center gap-3 text-xs">
            {cycleResult.errors.length > 0 && (
              <span className="text-orange-600">{cycleResult.errors.length} error{cycleResult.errors.length !== 1 ? "s" : ""}</span>
            )}
            {!cycleResult.quotaHit && <span className="text-text-muted">Queue cleared</span>}
          </div>
        </div>
      )}

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
