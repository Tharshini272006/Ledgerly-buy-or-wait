import { CalendarDays, CheckCircle2, ChevronRight, Clock3 } from "lucide-react";
import { money } from "../lib/format";

export function Recommendation({ request, revealed }) {
  const approved = request.status === "affordable_now";
  const blocked = request.status === "not_affordable";
  const verdict = approved ? "SAFE" : blocked ? "NOT AFFORDABLE" : "WAIT";
  return <article className={`card recommendation ${revealed ? "revealed" : ""} ${blocked ? "blocked" : ""}`}><div className="result-heading"><div className={`verdict-icon ${approved ? "approved" : ""} ${blocked ? "blocked" : ""}`}>{approved ? <CheckCircle2 size={21} /> : <Clock3 size={21} />}<div><span>Recommendation</span><b>{verdict}</b></div></div><span className="confidence">92% confidence</span></div>
    <div className="result-main"><span>Safe amount today</span><strong>{money(request.safe, request.currency)}</strong><p>{request.explanation}</p></div>
    <div className="result-divider" />
    <div className="date-callout"><CalendarDays size={16} /><div><span>Earliest safe full payment</span><b>{request.earliest || "Not available"}</b></div></div>
    <div className="result-stats"><span>Protected balance<b>{money(request.minimum, request.currency)}</b></span><span>Recommended method<b>{request.method.replaceAll("_", " ")}</b></span></div>
    <button className="secondary">View payment plan <ChevronRight size={15} /></button>
  </article>;
}
