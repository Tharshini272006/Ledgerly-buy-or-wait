import { Bell, ChevronRight, Menu, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";
import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { RequestForm } from "./components/RequestForm";
import { Recommendation } from "./components/Recommendation";
import { CashFlowChart } from "./components/CashFlowChart";
import { HistoryPanel } from "./components/HistoryPanel";
import { profile, requests } from "./data/ledgerData";
import { money } from "./lib/format";

function App() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [selectedId, setSelectedId] = useState(requests[0].id);
  const [amount, setAmount] = useState(String(requests[0].amount));
  const [description, setDescription] = useState(requests[0].title);
  const [loading, setLoading] = useState(false);
  const [revealed, setRevealed] = useState(true);
  const [activeSection, setActiveSection] = useState("Overview");
  const request = requests.find((item) => item.id === selectedId) || requests[0];
  const selectRequest = (event) => { const next = requests.find((item) => item.id === event.target.value); setSelectedId(next.id); setAmount(String(next.amount)); setDescription(next.title); setRevealed(false); };
  const analyze = () => { setLoading(true); setRevealed(false); window.setTimeout(() => { setLoading(false); setRevealed(true); }, 850); };
  const navigate = (section) => {
    setActiveSection(section);
    setMobileOpen(false);
    const target = {
      Overview: "overview",
      "Payment planner": "payment-planner",
      "Cash flow": "cash-flow",
      "Payment history": "payment-history",
    }[section];
    document.getElementById(target)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  return <div className="app-shell"><Sidebar open={mobileOpen} onClose={() => setMobileOpen(false)} activeSection={activeSection} onSelect={navigate} /><main className="main-content">
    <header className="topbar"><button className="icon-button mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={19} /></button><div className="breadcrumb"><span>Workspace</span><ChevronRight size={14} /><b>Overview</b></div><div className="top-actions"><button className="icon-button" aria-label="Notifications"><Bell size={18} /><i /></button><span className="avatar">TD</span></div></header>
    <section className="page-header" id="overview"><div><span className="eyebrow live"><i /> Live financial forecast</span><h1>Can I afford this?</h1><p>Check a payment against your projected cash flow before it becomes a problem.</p></div><div className="header-meta"><span>Updated 2 min ago</span><button>Next 90 days <ChevronRight size={14} /></button></div></section>
    <section className="metrics"><article><span className="metric-icon"><TrendingUp size={16} /></span><b>{money(request.balance, request.currency)}</b><small>Available to spend <em>+8.4%</em></small></article><article><span className="metric-icon"><ShieldCheck size={16} /></span><b>{money(request.safe, request.currency)}</b><small>Safe payment capacity <em>Current request</em></small></article><article><span className="metric-icon"><Sparkles size={16} /></span><b>{money(request.minimum, request.currency)}</b><small>90-day cash floor <em>Protected</em></small></article></section>
    <section className="request-picker"><span>Review a real request</span><select value={selectedId} onChange={selectRequest}>{requests.map((item) => <option value={item.id} key={item.id}>{item.id} · {item.title}</option>)}</select></section>
    <section className="primary-grid" id="payment-planner"><RequestForm request={{ ...request, currency: request.currency }} amount={amount} setAmount={setAmount} description={description} setDescription={setDescription} onAnalyze={analyze} loading={loading} /><Recommendation request={{ ...request, currency: request.currency }} revealed={revealed} /></section>
    <section className="lower-grid" id="cash-flow"><CashFlowChart /><article className="card insight-panel"><div className="panel-heading"><div><span className="eyebrow">Why this decision</span><h3>What changes the outcome?</h3></div><Sparkles size={17} className="blue-icon" /></div>{["Protect your cash floor", "Use the earliest safe date", "Keep flexible spending optional"].map((text, index) => <div className="insight" key={text}><b>0{index + 1}</b><div><strong>{text}</strong><p>{index === 0 ? `Your ${money(request.minimum, request.currency)} minimum stays protected in this recommendation.` : index === 1 ? request.earliest ? `The first safe full payment date is ${request.earliest}.` : "No safe full-payment date is available within the forecast." : "No protected categories need to be reduced for this recommendation."}</p></div></div>)}<div className="insight-footer">↘ Recommended action: {request.status === "affordable_now" ? "pay in full today." : request.status === "not_affordable" ? "do not proceed." : "wait until the cash floor recovers."}</div></article></section>
    <section id="payment-history"><HistoryPanel /></section><section className="bottom-strip"><span className="strip-icon"><TrendingUp size={16} /></span><div><small>Financial trajectory</small><b>Stable with room to improve</b></div><div className="strip-stat"><small>Monthly surplus</small><b>{money(7840, profile.currency)}</b></div><div className="strip-stat"><small>Risk level</small><b className="risk">Low</b></div></section>
  </main></div>;
}
export default App;
