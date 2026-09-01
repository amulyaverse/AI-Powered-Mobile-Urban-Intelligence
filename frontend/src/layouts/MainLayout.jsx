import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, RadioReceiver, Map, AlertTriangle, Activity, Settings, Bus } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/live', label: 'Live Monitoring', icon: RadioReceiver },
  { path: '/events', label: 'Incidents & Events', icon: AlertTriangle },
  { path: '/map', label: 'GIS Map', icon: Map },
  { path: '/traffic', label: 'Traffic Analytics', icon: Activity },
  { path: '/road-conditions', label: 'Road Conditions', icon: Bus },
];

export default function MainLayout() {
  return (
    <div className="flex h-screen w-full bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-4 flex items-center gap-3 font-semibold text-lg border-b border-slate-700">
          <Bus className="w-6 h-6 text-brand-500" />
          <span>Urban Intel</span>
        </div>
        <nav className="flex-1 py-4 flex flex-col gap-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                  isActive ? 'bg-brand-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-700 text-sm text-slate-400">
          Operator: Authority Admin
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <h1 className="font-semibold text-lg text-slate-800">Command Center</h1>
          <div className="flex items-center gap-4">
            <button className="text-slate-500 hover:text-slate-700">
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center font-bold text-slate-600">
              AD
            </div>
          </div>
        </header>
        
        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
