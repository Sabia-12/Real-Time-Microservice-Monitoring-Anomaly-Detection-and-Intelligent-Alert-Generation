import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Activity, Bell, History, LayoutDashboard, Menu, Radar, Server, Settings, X } from 'lucide-react';
import { isDemoMode } from '../../services/api';

const nav = [['/', 'Overview', LayoutDashboard], ['/services', 'Services', Server], ['/anomalies', 'Anomalies', Activity],
  ['/alerts', 'Alerts', Bell], ['/incidents', 'Incidents', History], ['/settings', 'Settings', Settings]];
const Links = ({ onClick }) => nav.map(([to, label, Icon]) => (
  <NavLink key={to} to={to} end={to === '/'} onClick={onClick}
    className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${isActive ? 'bg-cyan-500/10 text-cyan-300' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}`}>
    <Icon size={18} />{label}</NavLink>));
const Brand = () => <div className="flex items-center gap-2 font-semibold text-slate-100"><Radar className="text-cyan-400" />MSM Monitor</div>;

export default function Layout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen md:flex">
      <aside className="sticky top-0 hidden h-screen w-56 shrink-0 flex-col gap-1 border-r border-slate-800 bg-[#0a1020] p-4 md:flex">
        <div className="mb-4"><Brand /></div><nav aria-label="Main" className="flex flex-col gap-1"><Links /></nav>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-between border-b border-slate-800 bg-[#0a1020] px-4 py-3 md:hidden">
          <Brand />
          <button aria-label="Toggle menu" aria-expanded={open} onClick={() => setOpen(!open)} className="rounded-md p-1.5 hover:bg-slate-800">{open ? <X /> : <Menu />}</button>
        </header>
        {open && <nav aria-label="Mobile" className="flex flex-col gap-1 border-b border-slate-800 bg-[#0a1020] p-3 md:hidden"><Links onClick={() => setOpen(false)} /></nav>}
        {isDemoMode() && <div role="status" className="border-b border-amber-500/20 bg-amber-500/10 px-4 py-2 text-xs text-amber-300">DEMO DATA: values are synthetic mock data, not live telemetry or machine-learning detections.</div>}
        <main className="mx-auto max-w-7xl p-4 md:p-6"><Outlet /></main>
      </div>
    </div>
  );
}
