import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Flag, Phone, Info, X } from 'lucide-react';

const EMERGENCY_CONTACTS = [
  { label: 'Police Control Room', number: '100' },
  { label: 'Fire & Rescue', number: '101' },
  { label: 'Ambulance', number: '102' },
  { label: 'Municipal Helpline', number: '1916' },
  { label: 'Road Accident Helpline', number: '1073' },
];

export default function QuickLinks() {
  const [showEmergency, setShowEmergency] = useState(false);
  const [showAbout, setShowAbout] = useState(false);

  return (
    <>
      {/* Quick Links Bar */}
      <div className="bg-slate-800 border-t border-slate-700 px-4 py-2.5 shrink-0">
        <div className="flex flex-wrap items-center gap-x-1 gap-y-1 text-xs text-slate-400">
          <span className="font-semibold text-slate-500 uppercase tracking-wider text-[10px] mr-2 hidden sm:inline">
            Quick Links:
          </span>

          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-2.5 py-1.5 rounded transition-colors cursor-pointer ${
                isActive
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              }`
            }
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Live Dashboard</span>
          </NavLink>

          <NavLink
            to="/events"
            className={({ isActive }) =>
              `flex items-center gap-1.5 px-2.5 py-1.5 rounded transition-colors cursor-pointer ${
                isActive
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              }`
            }
          >
            <Flag className="w-3.5 h-3.5" />
            <span>Report an Issue</span>
          </NavLink>

          <button
            onClick={() => setShowEmergency(true)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-slate-300 hover:bg-slate-700 hover:text-white transition-colors cursor-pointer"
          >
            <Phone className="w-3.5 h-3.5" />
            <span>Emergency Contacts</span>
          </button>

          <button
            onClick={() => setShowAbout(true)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-slate-300 hover:bg-slate-700 hover:text-white transition-colors cursor-pointer"
          >
            <Info className="w-3.5 h-3.5" />
            <span>About</span>
          </button>
        </div>
      </div>

      {/* Emergency Contacts Modal */}
      {showEmergency && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowEmergency(false)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-red-50">
              <div className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-red-600" />
                <h3 className="font-bold text-slate-800">Emergency Contacts</h3>
              </div>
              <button
                onClick={() => setShowEmergency(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-2">
              {EMERGENCY_CONTACTS.map((c) => (
                <div
                  key={c.number}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100"
                >
                  <span className="text-sm font-medium text-slate-700">{c.label}</span>
                  <a
                    href={`tel:${c.number}`}
                    className="text-lg font-bold text-red-600 hover:text-red-800 transition-colors"
                  >
                    {c.number}
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* About Modal */}
      {showAbout && (
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowAbout(false)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50">
              <div className="flex items-center gap-2">
                <Info className="w-5 h-5 text-brand-600" />
                <h3 className="font-bold text-slate-800">About This Platform</h3>
              </div>
              <button
                onClick={() => setShowAbout(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-3 text-sm text-slate-700">
              <p>
                <span className="font-semibold text-slate-800">AI-Powered Mobile Urban Intelligence</span>{' '}
                is a real-time city monitoring platform built for Smart India Hackathon 2026.
              </p>
              <p>
                It aggregates AI/edge detections from bus-mounted cameras across the city fleet to
                identify potholes, road defects, traffic anomalies, and infrastructure issues —
                enabling faster municipal response.
              </p>
              <div className="pt-2 border-t border-slate-100 text-xs text-slate-500 flex justify-between">
                <span>SIH 2026 Platform v1.0.0</span>
                <span>Operator: Authority Admin</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
