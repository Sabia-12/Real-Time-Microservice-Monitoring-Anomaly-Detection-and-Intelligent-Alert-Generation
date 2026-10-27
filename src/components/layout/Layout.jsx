/**
 * Layout — App shell with sidebar nav and mobile hamburger menu.
 * Shows DEMO banner when running with synthetic mock data.
 */
import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  Activity, Bell, History, LayoutDashboard,
  Menu, Radar, Server, Settings, X,
} from 'lucide-react';
import { isDemoMode } from '../../services/api';

const nav = [
  ['/', 'Overview', LayoutDashboard],
  ['/services', 'Services', Server],
  ['/anomalies', 'Anomalies', Activity],
  ['/alerts', 'Alerts', Bell],
  ['/incidents', 'Incidents', History],
  ['/settings', 'Settings', Settings],
];

const Links = ({ onClick }) =>
  nav.map(([to, label, Icon]) => (
    <NavLink
      key={to}
      to={to}
      end={to === '/'}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
          isActive
            ? 'bg-cyan-500/10 text-cyan-300 ring-1 ring-cyan-500/20'
            : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-100'
        }`
      }
    >
      <Icon size={17} />
      {label}
    </NavLink>
  ));

const Brand = () => (
  <div className="flex items-center gap-2.5">
    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600">
      <Radar size={16} className="text-white" />
    </div>
    <div>
      <p className="text-sm font-semibold text-slate-100 leading-tight">MSM Monitor</p>
      <p className="text-[10px] text-slate-500 leading-tight">Online Boutique</p>
    </div>
  </div>
);

export default function Layout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen md:flex">
      {/* Sidebar */}
      <aside className="sticky top-0 hidden h-screen w-56 shrink-0 flex-col gap-1 border-r border-slate-800/60 bg-[#080f1d] p-4 md:flex sidebar-glow">
        <div className="mb-5">
          <Brand />
        </div>
        <nav aria-label="Main" className="flex flex-col gap-0.5">
          <Links />
        </nav>
        <div className="mt-auto pt-4 border-t border-slate-800/60">
          <p className="text-[10px] text-slate-600 leading-relaxed">
            RE2-OB dataset · 90 cases<br />
            Fault types: cpu · delay · disk · loss · memory · socket
          </p>
        </div>
      </aside>

      {/* Main content */}
      <div className="min-w-0 flex-1 flex flex-col">
        {/* Mobile header */}
        <header className="flex items-center justify-between border-b border-slate-800/60 bg-[#080f1d] px-4 py-3 md:hidden">
          <Brand />
          <button
            aria-label="Toggle menu"
            aria-expanded={open}
            onClick={() => setOpen(!open)}
            className="rounded-md p-1.5 hover:bg-slate-800 text-slate-400"
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </header>

        {open && (
          <nav aria-label="Mobile" className="flex flex-col gap-0.5 border-b border-slate-800/60 bg-[#080f1d] p-3 md:hidden">
            <Links onClick={() => setOpen(false)} />
          </nav>
        )}

        {/* Demo mode banner */}
        {isDemoMode() && (
          <div role="status" className="border-b border-amber-500/20 bg-amber-500/8 px-4 py-2 text-xs text-amber-300">
            <strong>DEMO MODE:</strong> Values are synthetic mock data derived from Online Boutique RE2-OB structure — not live telemetry or ML output.
          </div>
        )}

        {/* Page content */}
        <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
