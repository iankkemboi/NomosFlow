"use client";
import { useEffect, useState, useCallback } from "react";
import PageShell from "@/components/layout/PageShell";
import TopBar from "@/components/layout/TopBar";
import MacWindowCard from "@/components/ui/MacWindowCard";
import StatusPill from "@/components/ui/StatusPill";
import RiskBadge from "@/components/ui/RiskBadge";
import DeviceIcon from "@/components/ui/DeviceIcon";
import Drawer from "@/components/ui/Drawer";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import { getCustomers, getPartners, getChurnScores, getCustomerPayments, getDunningTimeline } from "@/lib/api";
import { formatDate, formatCurrency, deviceLabel } from "@/lib/utils";
import type { Customer, Partner, ChurnScore, Payment, DunningAction } from "@/lib/types";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [partners, setPartners] = useState<Partner[]>([]);
  const [churnMap, setChurnMap] = useState<Record<string, ChurnScore>>({});
  const [loading, setLoading] = useState(true);

  const [filterPartner, setFilterPartner] = useState("");
  const [filterDevice, setFilterDevice] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [drawerPayments, setDrawerPayments] = useState<Payment[]>([]);
  const [drawerTimeline, setDrawerTimeline] = useState<DunningAction[]>([]);
  const [drawerLoading, setDrawerLoading] = useState(false);

  const load = useCallback(() => {
    const params: Record<string, string> = {};
    if (filterPartner) params.partner_id = filterPartner;
    if (filterDevice)  params.device_type = filterDevice;
    if (filterStatus)  params.contract_status = filterStatus;
    setLoading(true);
    Promise.all([getCustomers(params), getPartners(), getChurnScores()])
      .then(([c, p, scores]) => {
        setCustomers(c);
        setPartners(p);
        const map: Record<string, ChurnScore> = {};
        scores.forEach((s) => { map[s.customer_id] = s; });
        setChurnMap(map);
      })
      .finally(() => setLoading(false));
  }, [filterPartner, filterDevice, filterStatus]);

  useEffect(() => { load(); }, [load]);

  const openDrawer = async (customer: Customer) => {
    setSelectedCustomer(customer);
    setDrawerLoading(true);
    const [payments, timeline] = await Promise.all([
      getCustomerPayments(customer.id),
      getDunningTimeline(customer.id),
    ]);
    setDrawerPayments(payments);
    setDrawerTimeline(timeline);
    setDrawerLoading(false);
  };

  const partnerName = (id: string) => partners.find((p) => p.id === id)?.name ?? "—";

  return (
    <PageShell>
      <TopBar title="Customers" subtitle={`${customers.length} customers`} />

      <div className="flex gap-3 mb-5">
        <select value={filterPartner} onChange={(e) => setFilterPartner(e.target.value)}
          className="text-sm border border-border-card rounded-lg px-3 py-2 bg-white text-text-secondary focus:outline-none focus:ring-1 focus:ring-accent-green">
          <option value="">All Partners</option>
          {partners.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <select value={filterDevice} onChange={(e) => setFilterDevice(e.target.value)}
          className="text-sm border border-border-card rounded-lg px-3 py-2 bg-white text-text-secondary focus:outline-none focus:ring-1 focus:ring-accent-green">
          <option value="">All Devices</option>
          <option value="ev">EV</option>
          <option value="heat_pump">Heat Pump</option>
          <option value="battery">Battery</option>
        </select>
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
          className="text-sm border border-border-card rounded-lg px-3 py-2 bg-white text-text-secondary focus:outline-none focus:ring-1 focus:ring-accent-green">
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <MacWindowCard title="Customer List">
        {loading ? (
          <div className="flex justify-center py-16"><Spinner className="w-8 h-8" /></div>
        ) : customers.length === 0 ? (
          <EmptyState title="No customers found" description="Try adjusting your filters." />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-card text-left text-text-muted text-xs font-medium uppercase tracking-wide">
                <th className="pb-3 pr-4">Customer</th>
                <th className="pb-3 pr-4">Partner</th>
                <th className="pb-3 pr-4">Device</th>
                <th className="pb-3 pr-4">Status</th>
                <th className="pb-3 pr-4">Churn Risk</th>
                <th className="pb-3 pr-4">Savings/yr</th>
                <th className="pb-3">Since</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-card">
              {customers.map((c) => {
                const score = churnMap[c.id];
                return (
                  <tr
                    key={c.id}
                    onClick={() => openDrawer(c)}
                    className="cursor-pointer hover:bg-bg-page transition-colors"
                  >
                    <td className="py-3 pr-4">
                      <div>
                        <p className="font-medium text-text-primary">{c.name}</p>
                        <p className="text-xs text-text-muted">{c.email}</p>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-text-secondary">{partnerName(c.partner_id)}</td>
                    <td className="py-3 pr-4">
                      <span className="flex items-center gap-1.5 text-text-secondary">
                        <DeviceIcon deviceType={c.device_type} size={14} />
                        {deviceLabel(c.device_type)}
                      </span>
                    </td>
                    <td className="py-3 pr-4"><StatusPill status={c.contract_status} /></td>
                    <td className="py-3 pr-4">
                      {score ? <RiskBadge risk={score.risk_level} score={score.score} /> : <span className="text-text-muted">—</span>}
                    </td>
                    <td className="py-3 pr-4 text-text-secondary">
                      {c.annual_saving_eur ? formatCurrency(Number(c.annual_saving_eur)) : "—"}
                    </td>
                    <td className="py-3 text-text-muted">{formatDate(c.contract_start)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </MacWindowCard>

      <Drawer
        open={!!selectedCustomer}
        onClose={() => setSelectedCustomer(null)}
        title={selectedCustomer?.name}
      >
        {drawerLoading ? (
          <div className="flex justify-center py-16"><Spinner className="w-8 h-8" /></div>
        ) : selectedCustomer ? (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-3">
              {[
                ["Email", selectedCustomer.email],
                ["City", selectedCustomer.city ?? "—"],
                ["Device", deviceLabel(selectedCustomer.device_type)],
                ["Tariff", selectedCustomer.tariff_type],
                ["Contract start", formatDate(selectedCustomer.contract_start)],
                ["Salary day", selectedCustomer.salary_day ? `Day ${selectedCustomer.salary_day}` : "—"],
                ["Monthly kWh", selectedCustomer.monthly_kwh ? `${selectedCustomer.monthly_kwh} kWh` : "—"],
                ["Annual saving", selectedCustomer.annual_saving_eur ? formatCurrency(Number(selectedCustomer.annual_saving_eur)) : "—"],
              ].map(([label, value]) => (
                <div key={label} className="bg-bg-page rounded-lg p-3">
                  <p className="text-xs text-text-muted mb-0.5">{label}</p>
                  <p className="text-sm font-medium text-text-primary">{value}</p>
                </div>
              ))}
            </div>

            {churnMap[selectedCustomer.id] && (
              <div className="bg-white border border-border-card rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-heading font-semibold text-sm text-text-primary">Churn Risk</h4>
                  <RiskBadge risk={churnMap[selectedCustomer.id].risk_level} score={churnMap[selectedCustomer.id].score} />
                </div>
                <p className="text-sm text-text-secondary">{churnMap[selectedCustomer.id].reasoning}</p>
                {churnMap[selectedCustomer.id].action_suggested && (
                  <p className="mt-2 text-xs font-medium text-accent-green">
                    → {churnMap[selectedCustomer.id].action_suggested}
                  </p>
                )}
              </div>
            )}

            <div>
              <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">Payment History</h4>
              <div className="space-y-2">
                {drawerPayments.length === 0 && <p className="text-sm text-text-muted">No payments recorded.</p>}
                {drawerPayments.map((p) => (
                  <div key={p.id} className="flex items-center justify-between py-2 border-b border-border-card last:border-0">
                    <div>
                      <p className="text-sm font-medium text-text-primary">{formatCurrency(Number(p.amount_eur))}</p>
                      <p className="text-xs text-text-muted">Due {formatDate(p.due_date)}{p.failure_reason ? ` · ${p.failure_reason.replace(/_/g, " ")}` : ""}</p>
                    </div>
                    <StatusPill status={p.status} />
                  </div>
                ))}
              </div>
            </div>

            {drawerTimeline.length > 0 && (
              <div>
                <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">Dunning Timeline</h4>
                <div className="relative pl-4 space-y-3">
                  {drawerTimeline.map((a) => (
                    <div key={a.id} className="relative">
                      <span className="absolute -left-4 top-1 w-2 h-2 rounded-full bg-accent-green" />
                      <p className="text-xs font-semibold text-text-primary capitalize">{a.action_type.replace(/_/g, " ")}</p>
                      <p className="text-xs text-text-muted">{new Date(a.executed_at).toLocaleDateString("de-DE")}</p>
                      {a.ai_generated_message && (
                        <p className="text-xs text-text-secondary mt-0.5 italic line-clamp-2">{a.ai_generated_message}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </Drawer>
    </PageShell>
  );
}
