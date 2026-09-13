import { Area, AreaChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";
import { useEffect, useRef, useState } from "react";
import { cashFlow } from "../data/ledgerData";

export function CashFlowChart() {
  const chartRef = useRef(null);
  const [width, setWidth] = useState(640);

  useEffect(() => {
    const element = chartRef.current;
    if (!element) return undefined;

    const updateWidth = () => setWidth(Math.max(280, element.clientWidth));
    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(element);

    return () => observer.disconnect();
  }, []);

  return <article className="card chart-card"><div className="panel-heading"><div><span className="eyebrow">Forecast</span><h3>90-day cash flow</h3></div><button className="link-button">View details ›</button></div><div className="legend"><span><i className="income-dot" /> Income</span><span><i className="spend-dot" /> Spending</span></div><div className="chart-wrap" ref={chartRef}><AreaChart width={width} height={190} data={cashFlow} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}><defs><linearGradient id="income" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#72a9f7" stopOpacity=".3" /><stop offset="100%" stopColor="#72a9f7" stopOpacity="0" /></linearGradient><linearGradient id="spending" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#e3a66b" stopOpacity=".22" /><stop offset="100%" stopColor="#e3a66b" stopOpacity="0" /></linearGradient></defs><CartesianGrid stroke="rgba(255,255,255,.07)" vertical={false} /><XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#7f8a9a", fontSize: 11 }} /><YAxis hide domain={[0, 100]} /><Tooltip contentStyle={{ background: "#171e28", border: "1px solid #2a3543", borderRadius: 8, color: "#fff" }} /><Area type="monotone" dataKey="income" stroke="#72a9f7" fill="url(#income)" strokeWidth={2} /><Area type="monotone" dataKey="spending" stroke="#e3a66b" fill="url(#spending)" strokeWidth={2} /></AreaChart></div></article>;
}
