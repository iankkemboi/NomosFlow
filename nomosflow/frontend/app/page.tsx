"use client";
import Link from "next/link";
import {
  Zap, Shield, MessageSquare, Users, TrendingDown, AlertCircle,
  ArrowRight, CheckCircle, Building2, ChevronRight, Sparkles
} from "lucide-react";

const FEATURES = [
  {
    icon: AlertCircle,
    title: "Intelligent Dunning Engine",
    description:
      "When a direct debit fails, NomosFlow's AI instantly classifies the failure reason — insufficient funds, expired card, bank block, or SEPA reject — and schedules the optimal retry date based on your customer's salary day and payment history.",
    highlight: "3–8% of monthly revenue recovered",
  },
  {
    icon: TrendingDown,
    title: "Predictive Churn Scoring",
    description:
      "Don't wait until a customer cancels. NomosFlow scores every customer's churn risk in real time, surfacing who is recoverable at day 7 before they're gone by day 30. Powered by explainable AI reasoning.",
    highlight: "Catch churn before it happens",
  },
  {
    icon: MessageSquare,
    title: "AI Retention Messaging",
    description:
      "Generic 'your payment failed' emails drive cancellations. NomosFlow generates personalised, device-aware outreach — referencing the customer's EV, heat pump, or battery savings — with demonstrated 3× better retention outcomes.",
    highlight: "3× better retention outcomes",
  },
  {
    icon: Building2,
    title: "White-Label Partner View",
    description:
      "Switch between partner brands instantly. Whether it's Müller Wärmepumpen GmbH or a Berlin EV startup, every partner gets a fully branded operations view. Nomos's OEM proposition visualised end-to-end.",
    highlight: "7-day partner onboarding",
  },
];

const PROBLEMS = [
  {
    stat: "3–8%",
    label: "of monthly revenue at risk",
    description: "From failed payment cycles at the average energy retailer",
  },
  {
    stat: "12%",
    label: "email open rate",
    description: "For generic 'payment failed' blasts — driving more cancellations",
  },
  {
    stat: "Day 30",
    label: "too late to recover",
    description: "Most retailers discover churn after it happens, not before",
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Payment Fails",
    description: "A customer's direct debit fails. NomosFlow captures it instantly.",
  },
  {
    step: "02",
    title: "AI Classifies",
    description:
      "AI analyses the customer's device, history, and salary day to classify the root cause with confidence scoring.",
  },
  {
    step: "03",
    title: "Smart Retry Scheduled",
    description:
      "The retry is scheduled for the optimal date — right after the customer's salary day, not blindly 3 days later.",
  },
  {
    step: "04",
    title: "Personalised Outreach",
    description:
      "A device-aware retention message is generated and sent, referencing the customer's actual energy savings.",
  },
  {
    step: "05",
    title: "Churn Score Updated",
    description:
      "Churn risk is re-scored across the customer base. Your team sees exactly who to prioritise.",
  },
];

const PARTNERS_DEMO = [
  { name: "Müller Wärmepumpen GmbH", device: "Heat Pump", color: "#3D6B2C", customers: 9 },
  { name: "VoltDrive Berlin", device: "EV", color: "#2563EB", customers: 8 },
  { name: "SolarSpeicher AG", device: "Battery", color: "#EA580C", customers: 8 },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-[#F9F7F2] font-body">

      {/* ── Nav ── */}
      <nav className="sticky top-0 z-50 bg-[#F9F7F2]/90 backdrop-blur-md border-b border-[#E8E4DC]">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-heading font-bold text-xl text-[#1A1A1A] tracking-tight">NomosFlow</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-[#EBF2E6] text-[#3D6B2C] font-medium">AI</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-[#6B6860]">
            <a href="#how-it-works" className="hover:text-[#1A1A1A] transition-colors">How it works</a>
            <a href="#features" className="hover:text-[#1A1A1A] transition-colors">Features</a>
            <a href="#partners" className="hover:text-[#1A1A1A] transition-colors">Partners</a>
          </div>
          <Link
            href="/dashboard"
            className="flex items-center gap-2 bg-[#3D6B2C] text-white text-sm font-medium px-4 py-2 rounded-full hover:bg-[#2d5221] transition-colors"
          >
            Open Dashboard <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-24 text-center">
        <div className="inline-flex items-center gap-2 bg-[#EBF2E6] text-[#3D6B2C] text-xs font-semibold px-3 py-1.5 rounded-full mb-8">
          <Sparkles size={12} />
          Built for European Energy Retailers
        </div>

        <h1 className="font-heading font-bold text-5xl md:text-6xl text-[#1A1A1A] leading-tight mb-6 max-w-4xl mx-auto">
          Stop losing revenue to
          <span className="relative inline-block mx-3">
            <span className="relative z-10">failed payments</span>
            <span className="absolute inset-x-0 bottom-1 h-3 -z-0 rounded" style={{ background: "#EBF2E6" }} />
          </span>
          and silent churn
        </h1>

        <p className="text-lg text-[#6B6860] max-w-2xl mx-auto mb-10 leading-relaxed">
          NomosFlow is the AI operations back-office for white-label energy retailers. Intelligent dunning,
          predictive churn scoring, and personalised retention outreach — all in one dashboard.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 bg-[#3D6B2C] text-white font-semibold px-6 py-3 rounded-full hover:bg-[#2d5221] transition-colors shadow-sm"
          >
            Open Live Dashboard <ArrowRight size={16} />
          </Link>
          <a
            href="#how-it-works"
            className="flex items-center gap-2 text-[#6B6860] font-medium px-6 py-3 rounded-full border border-[#E8E4DC] hover:bg-white transition-colors"
          >
            See how it works <ChevronRight size={16} />
          </a>
        </div>

        {/* MacWindow Hero Card */}
        <div className="mt-16 bg-white rounded-[12px] border border-[#E8E4DC] shadow-[0_8px_40px_rgba(0,0,0,0.08)] overflow-hidden text-left max-w-4xl mx-auto">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-[#E8E4DC] bg-[#F9F7F2]">
            <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
            <span className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
            <span className="w-3 h-3 rounded-full bg-[#28CA41]" />
            <span className="ml-3 text-xs font-medium text-[#6B6860]">NomosFlow — AI Dunning Engine</span>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-4 gap-4 mb-6">
              {[
                { label: "Total Customers", value: "25", color: "#3D6B2C" },
                { label: "Failed Payments",  value: "7",  color: "#DC2626" },
                { label: "At-Risk Customers",value: "4",  color: "#EA580C" },
                { label: "Revenue at Risk",  value: "€1,840", color: "#CA8A04" },
              ].map((card) => (
                <div key={card.label} className="bg-[#F9F7F2] rounded-[12px] p-4 border border-[#E8E4DC]">
                  <p className="text-2xl font-bold" style={{ color: card.color }}>{card.value}</p>
                  <p className="text-xs text-[#A09D97] mt-1">{card.label}</p>
                </div>
              ))}
            </div>
            <div className="space-y-2">
              {[
                { name: "Lukas Bauer",  partner: "VoltDrive Berlin",     device: "EV",         amount: "€ 142,00", status: "failed",   risk: "critical" },
                { name: "Anna Schmidt", partner: "Müller Wärmepumpen",   device: "Heat Pump",  amount: "€ 98,00",  status: "retrying", risk: "high"     },
                { name: "Felix Wagner", partner: "SolarSpeicher AG",      device: "Battery",    amount: "€ 210,00", status: "paid",     risk: "low"      },
              ].map((row) => (
                <div key={row.name} className="flex items-center justify-between py-2.5 border-b border-[#E8E4DC] last:border-0">
                  <div>
                    <p className="text-sm font-medium text-[#1A1A1A]">{row.name}</p>
                    <p className="text-xs text-[#A09D97]">{row.partner} · {row.device}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-[#1A1A1A]">{row.amount}</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      row.status === "failed"   ? "bg-red-50 text-red-700"  :
                      row.status === "retrying" ? "bg-blue-50 text-blue-700" :
                      "bg-green-50 text-green-700"
                    }`}>{row.status}</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      row.risk === "critical" ? "bg-red-50 text-red-700"    :
                      row.risk === "high"     ? "bg-orange-50 text-orange-700" :
                      "bg-green-50 text-green-700"
                    }`}>{row.risk}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Problem Stats ── */}
      <section className="bg-[#1A1A1A] py-16">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-center text-[#6B6860] text-sm font-medium uppercase tracking-widest mb-10">
            The problem with energy retail at scale
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {PROBLEMS.map((p) => (
              <div key={p.stat} className="text-center">
                <p className="font-heading text-5xl font-bold text-white mb-2">{p.stat}</p>
                <p className="text-[#EBF2E6] font-semibold text-sm mb-2">{p.label}</p>
                <p className="text-[#6B6860] text-sm leading-relaxed">{p.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section id="how-it-works" className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <p className="text-[#3D6B2C] text-sm font-semibold uppercase tracking-widest mb-3">How NomosFlow works</p>
          <h2 className="font-heading text-4xl font-bold text-[#1A1A1A] mb-4">
            From failed payment to recovered customer
          </h2>
          <p className="text-[#6B6860] max-w-xl mx-auto">
            A fully automated AI pipeline that turns payment failures into retention opportunities.
          </p>
        </div>
        <div className="relative">
          <div className="hidden md:block absolute left-[calc(50%-1px)] top-8 bottom-8 w-px bg-[#E8E4DC]" />
          <div className="space-y-8">
            {HOW_IT_WORKS.map((step, i) => (
              <div key={step.step} className={`flex items-center gap-8 ${i % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"}`}>
                <div className={`flex-1 ${i % 2 === 0 ? "md:text-right" : "md:text-left"}`}>
                  <div className={`bg-white rounded-[12px] border border-[#E8E4DC] shadow-[0_1px_3px_rgba(0,0,0,0.06)] p-5 inline-block w-full md:max-w-sm ${i % 2 === 0 ? "md:ml-auto" : ""}`}>
                    <p className="text-xs font-bold text-[#3D6B2C] mb-2">STEP {step.step}</p>
                    <h3 className="font-heading font-semibold text-[#1A1A1A] text-base mb-1">{step.title}</h3>
                    <p className="text-sm text-[#6B6860] leading-relaxed">{step.description}</p>
                  </div>
                </div>
                <div className="hidden md:flex w-10 h-10 rounded-full bg-[#EBF2E6] border-2 border-[#3D6B2C] items-center justify-center flex-shrink-0 z-10">
                  <span className="text-xs font-bold text-[#3D6B2C]">{step.step}</span>
                </div>
                <div className="flex-1 hidden md:block" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="bg-white py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-[#3D6B2C] text-sm font-semibold uppercase tracking-widest mb-3">Capabilities</p>
            <h2 className="font-heading text-4xl font-bold text-[#1A1A1A] mb-4">Everything your ops team needs</h2>
            <p className="text-[#6B6860] max-w-xl mx-auto">
              Built specifically for the complexity of white-label energy retail — not a generic CRM bolted on.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {FEATURES.map((f) => (
              <div key={f.title} className="bg-[#F9F7F2] rounded-[12px] border border-[#E8E4DC] p-6 hover:shadow-[0_4px_20px_rgba(0,0,0,0.08)] transition-shadow">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#EBF2E6] flex items-center justify-center flex-shrink-0">
                    <f.icon size={18} className="text-[#3D6B2C]" />
                  </div>
                  <div>
                    <h3 className="font-heading font-semibold text-[#1A1A1A] text-base mb-2">{f.title}</h3>
                    <p className="text-sm text-[#6B6860] leading-relaxed mb-3">{f.description}</p>
                    <span className="inline-flex items-center gap-1.5 bg-[#3D6B2C] text-white text-xs font-semibold px-3 py-1 rounded-full">
                      <CheckCircle size={11} />
                      {f.highlight}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── AI Message Demo ── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <p className="text-[#3D6B2C] text-sm font-semibold uppercase tracking-widest mb-3">AI Retention Messaging</p>
            <h2 className="font-heading text-4xl font-bold text-[#1A1A1A] mb-5 leading-tight">
              Not a template. A real conversation.
            </h2>
            <p className="text-[#6B6860] leading-relaxed mb-6">
              The AI reads the customer's device type, their energy savings, their payment history, and upcoming
              cheap tariff windows — then writes a message that sounds human, not automated.
            </p>
            <div className="space-y-3">
              {[
                "Aware of the customer's EV charging window savings",
                "References specific upcoming low-tariff periods",
                "Adjusts tone based on churn risk level",
                "Never sounds like a generic debt reminder",
              ].map((point) => (
                <div key={point} className="flex items-center gap-3">
                  <CheckCircle size={16} className="text-[#3D6B2C] flex-shrink-0" />
                  <span className="text-sm text-[#6B6860]">{point}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-[12px] border border-[#E8E4DC] shadow-[0_4px_20px_rgba(0,0,0,0.06)] overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-[#E8E4DC] bg-[#F9F7F2]">
              <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
              <span className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
              <span className="w-3 h-3 rounded-full bg-[#28CA41]" />
              <span className="ml-2 text-xs text-[#A09D97]">AI Retention Message · Lukas Bauer · EV</span>
            </div>
            <div className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700 font-medium">critical risk</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-[#EBF2E6] text-[#3D6B2C] font-medium">EV</span>
                <span className="text-xs text-[#A09D97]">VoltDrive Berlin</span>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-[#A09D97] uppercase tracking-wide font-medium mb-1">Subject</p>
                  <p className="text-sm font-semibold text-[#1A1A1A]">
                    Your VoltDrive energy plan — a quick note about your recent payment
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[#A09D97] uppercase tracking-wide font-medium mb-1">Body</p>
                  <p className="text-sm text-[#6B6860] leading-relaxed">
                    Hi Lukas,<br /><br />
                    We noticed your direct debit for February didn{"'"}t go through. No worries —
                    these things happen. Your EV charging plan is still active and{" "}
                    <span className="bg-[#3D6B2C] text-white px-1.5 py-0.5 rounded text-xs font-medium mx-0.5">
                      you{"'"}re saving €340/yr vs a fixed tariff
                    </span>
                    {" "}with your overnight charging windows.<br /><br />
                    We{"'"}ve rescheduled your payment for the 28th. If anything{"'"}s changed, let us know.
                  </p>
                </div>
                <div className="flex items-center gap-2 pt-1">
                  <span className="text-xs text-[#A09D97]">Tone:</span>
                  <span className="text-xs font-semibold text-[#3D6B2C]">empathetic</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Partners ── */}
      <section id="partners" className="bg-[#F2EFE9] py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-[#3D6B2C] text-sm font-semibold uppercase tracking-widest mb-3">White-Label Partners</p>
            <h2 className="font-heading text-4xl font-bold text-[#1A1A1A] mb-4">One engine. Many brands.</h2>
            <p className="text-[#6B6860] max-w-xl mx-auto">
              NomosFlow supports every OEM partner with a fully branded view. Switch between partners in
              one click — the data, the risk scores, and the outreach all follow.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PARTNERS_DEMO.map((p) => (
              <div key={p.name} className="bg-white rounded-[12px] border border-[#E8E4DC] shadow-[0_1px_3px_rgba(0,0,0,0.06)] p-5">
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-bold"
                    style={{ backgroundColor: p.color }}
                  >
                    {p.name[0]}
                  </div>
                  <div>
                    <p className="font-heading font-semibold text-[#1A1A1A] text-sm">{p.name}</p>
                    <p className="text-xs text-[#A09D97]">{p.device} · {p.customers} customers</p>
                  </div>
                </div>
                <div className="rounded-lg p-3 text-xs font-medium" style={{ backgroundColor: p.color + "15", color: p.color }}>
                  Powered by Nomos infrastructure
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="bg-[#1A1A1A] py-20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-[#EBF2E6]/10 text-[#EBF2E6] text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
            <Zap size={12} />
            Live demo — backend + frontend fully operational
          </div>
          <h2 className="font-heading text-4xl font-bold text-white mb-5 leading-tight">
            Ready to see NomosFlow in action?
          </h2>
          <p className="text-[#6B6860] mb-10 text-lg leading-relaxed">
            Open the live dashboard. Seed the database with 3 partners and 25 customers.
            Run the AI dunning cycle and watch it process payments in real time.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 bg-[#3D6B2C] text-white font-semibold px-8 py-3.5 rounded-full hover:bg-[#2d5221] transition-colors"
            >
              Open Dashboard <ArrowRight size={16} />
            </Link>
            <Link
              href="/dunning"
              className="flex items-center gap-2 text-[#A09D97] font-medium px-6 py-3.5 rounded-full border border-[#333] hover:border-[#555] hover:text-white transition-colors"
            >
              <Shield size={14} />
              Run Dunning Cycle
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-[#E8E4DC] py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-heading font-bold text-[#1A1A1A]">NomosFlow</span>
            <span className="text-[#A09D97] text-sm">— AI Dunning Engine</span>
          </div>
          <p className="text-xs text-[#A09D97]">
            Built for Nomos · B2B white-label energy infrastructure
          </p>
          <div className="flex items-center gap-4 text-sm text-[#6B6860]">
            <Link href="/dashboard" className="hover:text-[#1A1A1A] transition-colors">Dashboard</Link>
            <Link href="/customers" className="hover:text-[#1A1A1A] transition-colors">Customers</Link>
            <Link href="/dunning" className="hover:text-[#1A1A1A] transition-colors">Dunning</Link>
            <Link href="/retention" className="hover:text-[#1A1A1A] transition-colors">Retention</Link>
          </div>
        </div>
      </footer>

    </div>
  );
}
