"use client";
import { useEffect, useState } from "react";
import PageShell from "@/components/layout/PageShell";
import TopBar from "@/components/layout/TopBar";
import MacWindowCard from "@/components/ui/MacWindowCard";
import DeviceIcon from "@/components/ui/DeviceIcon";
import Spinner from "@/components/ui/Spinner";
import { getPartners, getChurnScores } from "@/lib/api";
import { deviceLabel } from "@/lib/utils";
import type { Partner, ChurnScore } from "@/lib/types";

export default function PartnersPage() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [scores, setScores] = useState<ChurnScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [activePartner, setActivePartner] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getPartners(), getChurnScores()])
      .then(([p, s]) => {
        setPartners(p);
        setScores(s);
        if (p.length > 0) setActivePartner(p[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  const riskCounts = (partnerId: string) => {
    const partnerScores = scores.filter((s) => s.partner_name === partners.find((p) => p.id === partnerId)?.name);
    return {
      critical: partnerScores.filter((s) => s.risk_level === "critical").length,
      high: partnerScores.filter((s) => s.risk_level === "high").length,
      medium: partnerScores.filter((s) => s.risk_level === "medium").length,
      low: partnerScores.filter((s) => s.risk_level === "low").length,
    };
  };

  const active = partners.find((p) => p.id === activePartner);

  return (
    <PageShell>
      <TopBar title="Partners" subtitle="White-label OEM partner overview" />

      {loading ? (
        <div className="flex justify-center py-16"><Spinner className="w-8 h-8" /></div>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-1 space-y-3">
            {partners.map((p) => {
              const counts = riskCounts(p.id);
              const isActive = activePartner === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => setActivePartner(p.id)}
                  className={`cursor-pointer bg-white rounded-card border shadow-card p-4 transition-all ${
                    isActive ? "border-accent-green ring-1 ring-accent-green/20" : "border-border-card hover:border-text-muted"
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-heading font-semibold text-text-primary text-sm">{p.name}</h3>
                      <p className="text-xs text-text-muted mt-0.5">{p.slug}</p>
                    </div>
                    <span
                      className="w-3 h-3 rounded-full mt-1"
                      style={{ backgroundColor: p.brand_color }}
                    />
                  </div>
                  <div className="flex items-center gap-2 mb-3">
                    <DeviceIcon deviceType={p.device_type} size={14} className="text-text-secondary" />
                    <span className="text-xs text-text-secondary">{deviceLabel(p.device_type)}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-text-muted">{p.customer_count} customers</span>
                    <div className="flex gap-1.5">
                      {counts.critical > 0 && <span className="px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-medium">{counts.critical} crit</span>}
                      {counts.high > 0 && <span className="px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 font-medium">{counts.high} high</span>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="col-span-2">
            {active ? (
              <MacWindowCard title={`${active.name} — White-Label Preview`}>
                <div
                  className="rounded-lg p-6 mb-4"
                  style={{ backgroundColor: active.brand_color + "15", borderColor: active.brand_color + "40", border: "1px solid" }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-white"
                      style={{ backgroundColor: active.brand_color }}
                    >
                      <DeviceIcon deviceType={active.device_type} size={20} />
                    </div>
                    <div>
                      <h3 className="font-heading font-bold text-text-primary">{active.name}</h3>
                      <p className="text-xs text-text-muted">Energy Dashboard — powered by Nomos</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      ["Customers", active.customer_count],
                      ["Risk: Critical", riskCounts(active.id).critical],
                      ["Risk: High", riskCounts(active.id).high],
                    ].map(([label, value]) => (
                      <div key={label} className="bg-white/70 rounded-lg p-3 text-center">
                        <p className="text-2xl font-bold text-text-primary">{value}</p>
                        <p className="text-xs text-text-muted mt-0.5">{label}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wide">Partner Details</h4>
                  {[
                    ["Brand Colour", active.brand_color],
                    ["Device Type", deviceLabel(active.device_type)],
                    ["Slug / API key", active.slug],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between py-2 border-b border-border-card last:border-0 text-sm">
                      <span className="text-text-secondary">{label}</span>
                      <span className="font-medium text-text-primary">{value}</span>
                    </div>
                  ))}
                </div>
              </MacWindowCard>
            ) : null}
          </div>
        </div>
      )}
    </PageShell>
  );
}
