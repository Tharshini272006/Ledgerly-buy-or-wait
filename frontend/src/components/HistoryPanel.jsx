import { ChevronRight, Search } from "lucide-react";
import { history } from "../data/ledgerData";
import { useState } from "react";

export function HistoryPanel() {
  const [filter, setFilter] = useState("All");
  const [query, setQuery] = useState("");
  const shown = history.filter((item) => (filter === "All" || item.status === filter) && item.title.toLowerCase().includes(query.toLowerCase()));
  return <article className="card history-card"><div className="panel-heading"><div><span className="eyebrow">Activity</span><h3>Payment history</h3></div><button className="link-button">See all <ChevronRight size={14} /></button></div><div className="history-tools"><div className="search"><Search size={14} /><input placeholder="Search payments" value={query} onChange={(e) => setQuery(e.target.value)} /></div><div className="filters">{["All", "Approved", "Wait"].map((item) => <button className={filter === item ? "selected" : ""} onClick={() => setFilter(item)} key={item}>{item}</button>)}</div></div><div className="history-list">{shown.map((item) => <div className="history-row" key={item.id}><span className={`history-icon ${item.tone}`}>{item.status === "Approved" ? "✓" : "↗"}</span><div className="history-name"><b>{item.title}</b><small>{item.type} · {item.date}</small></div><strong>{item.amount}</strong><span className={`status ${item.tone}`}>{item.status}</span><ChevronRight size={15} className="row-chevron" /></div>)}</div></article>;
}
