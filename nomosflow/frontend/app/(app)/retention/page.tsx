"use client";
import { useEffect, useState } from "react";
import PageShell from "@/components/layout/PageShell";
import TopBar from "@/components/layout/TopBar";
import MacWindowCard from "@/components/ui/MacWindowCard";
import RiskBadge from "@/components/ui/RiskBadge";
import DeviceIcon from "@/components/ui/DeviceIcon";
import Button from "@/components/ui/Button";
import HighlightPhrase from "@/components/ui/HighlightPhrase";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import { getChurnScores, getRetentionMessage, ApiError } from "@/lib/api";
import { deviceLabel } from "@/lib/utils";
import type { ChurnScore, RetentionMessage } from "@/lib/types";

interface MessageState {
  loading: boolean;
  data: RetentionMessage | null;
  error: string | null;
}

export default function RetentionPage() {
  const [scores, setScores] = useState<ChurnScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<Record<string, MessageState>>({});

  useEffect(() => {
    getChurnScores({ limit: "20" })
      .then((s) => setScores(s.filter((x) => x.risk_level !== "low")))
      .finally(() => setLoading(false));
  }, []);

  const generateMessage = async (customerId: string) => {
    setMessages((prev) => ({
      ...prev,
      [customerId]: { loading: true, data: null, error: null },
    }));
    try {
      const msg = await getRetentionMessage(customerId);
      setMessages((prev) => ({
        ...prev,
        [customerId]: { loading: false, data: msg, error: null },
      }));
    } catch (err) {
      const error =
        err instanceof ApiError
          ? err.message
          : "Unable to generate message. Please try again.";
      setMessages((prev) => ({
        ...prev,
        [customerId]: { loading: false, data: null, error },
      }));
    }
  };

  return (
    <PageShell>
      <TopBar
        title="AI Retention Messages"
        subtitle="Personalised AI-generated outreach for at-risk customers"
      />

      {loading ? (
        <div className="flex justify-center py-16"><Spinner className="w-8 h-8" /></div>
      ) : scores.length === 0 ? (
        <EmptyState title="No at-risk customers" description="All customers are low risk." />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {scores.map((score) => {
            const msgState = messages[score.customer_id];
            return (
              <MacWindowCard
                key={score.id}
                title={score.customer_name ?? "Unknown Customer"}
                action={
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => generateMessage(score.customer_id)}
                    loading={msgState?.loading}
                    disabled={msgState?.loading}
                  >
                    {msgState?.data ? "Regenerate" : "Generate Message"}
                  </Button>
                }
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="flex items-center gap-1.5 text-sm text-text-secondary">
                    <DeviceIcon deviceType={score.device_type ?? ""} size={14} />
                    {deviceLabel(score.device_type ?? "")}
                  </span>
                  <RiskBadge risk={score.risk_level} score={score.score} />
                  {score.partner_name && (
                    <span className="text-xs text-text-muted">{score.partner_name}</span>
                  )}
                </div>

                {score.reasoning && (
                  <p className="text-sm text-text-secondary mb-3 italic">{score.reasoning}</p>
                )}

                {msgState?.loading && (
                  <div className="flex items-center gap-2 text-sm text-text-muted py-3">
                    <Spinner className="w-4 h-4" />
                    Generating personalised message…
                  </div>
                )}

                {msgState?.error && (
                  <p className="text-sm text-red-500">{msgState.error}</p>
                )}

                {msgState?.data && (
                  <div className="bg-bg-page rounded-lg p-4 border border-border-card space-y-3">
                    <div>
                      <span className="text-xs text-text-muted uppercase tracking-wide font-medium">Subject</span>
                      <p className="text-sm font-semibold text-text-primary mt-0.5">{msgState.data.subject}</p>
                    </div>
                    <div>
                      <span className="text-xs text-text-muted uppercase tracking-wide font-medium">Body</span>
                      <div className="text-sm text-text-secondary mt-1 whitespace-pre-line leading-relaxed">
                        {msgState.data.highlight_phrase
                          ? msgState.data.body.split(msgState.data.highlight_phrase).map((part, i, arr) =>
                              i < arr.length - 1 ? (
                                <span key={i}>
                                  {part}
                                  <HighlightPhrase>{msgState.data!.highlight_phrase}</HighlightPhrase>
                                </span>
                              ) : part
                            )
                          : msgState.data.body}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-text-muted">Tone:</span>
                      <span className="text-xs font-medium text-accent-green capitalize">{msgState.data.tone}</span>
                    </div>
                  </div>
                )}

                {!msgState && score.action_suggested && (
                  <p className="text-sm text-text-secondary">
                    <span className="font-medium text-accent-green">Suggested action:</span> {score.action_suggested}
                  </p>
                )}
              </MacWindowCard>
            );
          })}
        </div>
      )}
    </PageShell>
  );
}
