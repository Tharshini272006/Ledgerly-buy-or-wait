import { ArrowUpRight, CalendarDays, CreditCard, FileText, WalletCards } from "lucide-react";
import { money } from "../lib/format";

export function RequestForm({ request, amount, setAmount, description, setDescription, onAnalyze, loading }) {
  return <article className="card request-card">
    <div className="card-heading"><div><span className="eyebrow">Payment intelligence</span><h2>Evaluate a purchase</h2></div><span className="live-label"><i /> Live forecast</span></div>
    <div className="form">
      <label>What are you planning to pay for?<span className="field"><FileText size={16} /><input value={description} onChange={(e) => setDescription(e.target.value)} placeholder={request.title} /></span></label>
      <div className="form-row"><label>Amount<span className="field money-field"><b>{request.currency}</b><input type="number" value={amount} min="0" onChange={(e) => setAmount(e.target.value)} /></span></label><label>Need it by<span className="field"><CalendarDays size={16} /><input value={request.due} readOnly /></span></label></div>
      <div className="choice-row"><button className="choice selected"><CreditCard size={15} /> Full payment <b>✓</b></button><button className="choice"><WalletCards size={15} /> Flexible plan</button></div>
      <button className="analyze" onClick={onAnalyze} disabled={loading}>{loading ? "Reviewing your forecast…" : <>Analyze {money(Number(amount) || 0, request.currency)} <ArrowUpRight size={17} /></>}</button>
    </div>
    <div className="request-preview"><span>Current request</span><b>{description || request.title}</b><div><span>Requested<strong>{money(Number(amount) || 0, request.currency)}</strong></span><span>Safe now<strong className="blue">{money(request.safe, request.currency)}</strong></span><span>Decision<strong className="amber">{request.status === "affordable_now" ? "Approve" : "Wait"}</strong></span></div></div>
  </article>;
}
