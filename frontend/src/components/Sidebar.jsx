import { BarChart3, CalendarDays, FileText, LayoutDashboard, MoreHorizontal, ShieldCheck, Sparkles, X } from "lucide-react";

const items = [
  ["Overview", LayoutDashboard],
  ["Payment planner", CalendarDays],
  ["Cash flow", BarChart3],
  ["Payment history", FileText],
];

export function Sidebar({ open, onClose, activeSection, onSelect }) {
  return (
    <>
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <div>
          <div className="brand"><span className="brand-mark"><Sparkles size={17} /></span><div><b>Ledgerly</b><small>Financial intelligence</small></div><button className="mobile-close" onClick={onClose} aria-label="Close navigation"><X size={18} /></button></div>
          <div className="workspace-chip"><span className="avatar">TD</span><div><b>Personal workspace</b><small>Protected profile</small></div><span className="chevron">›</span></div>
          <span className="section-label">Workspace</span>
          <nav>{items.map(([label, Icon]) => <button key={label} className={`nav-item ${activeSection === label ? "active" : ""}`} onClick={() => onSelect(label)}><Icon size={17} /><span>{label}</span>{activeSection === label && <i />}</button>)}</nav>
        </div>
        <div className="sidebar-bottom">
          <div className="trust-card"><ShieldCheck size={17} /><div><b>Forecast protected</b><small>90-day cash floor active</small></div></div>
          <button className="profile-row"><span className="avatar">TD</span><div><b>Tharshini</b><small>Personal finances</small></div><MoreHorizontal size={17} /></button>
        </div>
      </aside>
      {open && <button className="overlay" onClick={onClose} aria-label="Close navigation" />}
    </>
  );
}
