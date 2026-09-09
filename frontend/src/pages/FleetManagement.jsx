/**
 * FleetManagement.jsx
 * -------------------
 * Full CRUD page for managing the bus fleet.
 *
 * READ   — fetches live buses from GET /api/buses (falls back to demo data)
 * CREATE — POST /api/buses (requires live backend)
 * UPDATE — PATCH /api/buses/{id} (requires live backend)
 * DELETE — DELETE /api/buses/{id} (requires live backend; blocked if bus has events)
 *
 * Design follows existing dashboard conventions:
 *   - Tailwind CSS only (no extra libraries)
 *   - LoadingState / ErrorState from PageStatusState
 *   - Modal pattern identical to EventPage detail modal
 *   - Inline toast notifications (no third-party toast library)
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  Bus,
  Plus,
  Pencil,
  Trash2,
  RefreshCw,
  X,
  CheckCircle,
  AlertCircle,
  WifiOff,
  CheckCircle2,
} from 'lucide-react';
import { formatDateTime, formatRelativeTime } from '../utils/dateTime';
import {
  getBuses,
  createBus,
  updateBus,
  deleteBus,
  getConnectionState,
  subscribeConnectionState,
} from '../services/api';
import { LoadingState, ErrorState } from '../components/PageStatusState';
import { format, isValid } from 'date-fns';

// ── Helper utilities ──────────────────────────────────────────────────────────

const STATUS_OPTIONS = ['Active', 'Maintenance', 'Offline'];
const CAMERA_OPTIONS = ['Active', 'Offline'];

function statusBadge(status) {
  switch (status) {
    case 'Active':
      return 'bg-emerald-100 text-emerald-700';
    case 'Maintenance':
      return 'bg-amber-100 text-amber-700';
    case 'Offline':
      return 'bg-red-100 text-red-700';
    default:
      return 'bg-slate-100 text-slate-600';
  }
}

function cameraBadge(status) {
  return status === 'Active'
    ? 'bg-emerald-100 text-emerald-700'
    : 'bg-slate-100 text-slate-500';
}

function trafficBadge(traffic) {
  switch (traffic) {
    case 'High':
    case 'CRITICAL':
      return 'text-red-600 font-semibold';
    case 'Medium':
      return 'text-amber-600';
    case 'Low':
      return 'text-emerald-600';
    default:
      return 'text-slate-400';
  }
}

function formatDate(dateStr) {
  return formatDateTime(dateStr, 'dd MMM yyyy, HH:mm:ss');
}

// ── Toast Component ───────────────────────────────────────────────────────────

function Toast({ toast }) {
  if (!toast) return null;
  const isError = toast.type === 'error';
  return (
    <div
      className={`fixed bottom-6 right-6 z-[100] flex items-start gap-3 px-4 py-3 rounded-lg shadow-xl border max-w-sm text-sm font-medium animate-in slide-in-from-bottom-2 duration-200 ${
        isError
          ? 'bg-red-50 border-red-200 text-red-800'
          : 'bg-emerald-50 border-emerald-200 text-emerald-800'
      }`}
    >
      {isError ? (
        <AlertCircle className="w-5 h-5 shrink-0 text-red-500 mt-0.5" />
      ) : (
        <CheckCircle className="w-5 h-5 shrink-0 text-emerald-500 mt-0.5" />
      )}
      <span className="leading-snug">{toast.message}</span>
    </div>
  );
}

// ── Bus Form (shared for Create & Edit) ───────────────────────────────────────

const EMPTY_FORM = { id: '', route: '', status: 'Active', camera_status: 'Active' };

function BusForm({ initial = EMPTY_FORM, isEdit = false, onSubmit, onCancel, submitting, apiError }) {
  const [form, setForm] = useState({ ...EMPTY_FORM, ...initial });
  const [errors, setErrors] = useState({});

  const set = (field, value) => {
    setForm((f) => ({ ...f, [field]: value }));
    setErrors((e) => ({ ...e, [field]: '' }));
  };

  const validate = () => {
    const errs = {};
    if (!form.id.trim()) errs.id = 'Bus ID is required.';
    else if (form.id.trim().length > 20) errs.id = 'Bus ID must be 20 characters or fewer.';
    return errs;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    onSubmit({
      id: form.id.trim().toUpperCase(),
      route: form.route.trim() || null,
      status: form.status,
      camera_status: form.camera_status,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Bus ID */}
      <div>
        <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
          Bus ID {!isEdit && <span className="text-red-500">*</span>}
        </label>
        {isEdit ? (
          <div className="px-3 py-2 bg-slate-100 rounded-md border border-slate-200 text-sm text-slate-500 font-mono">
            {form.id} <span className="text-xs ml-1 text-slate-400">(cannot change ID)</span>
          </div>
        ) : (
          <>
            <input
              type="text"
              value={form.id}
              onChange={(e) => set('id', e.target.value)}
              placeholder="e.g. BUS_099"
              className={`w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-1 font-mono ${
                errors.id
                  ? 'border-red-400 focus:border-red-500 focus:ring-red-400'
                  : 'border-slate-300 focus:border-brand-500 focus:ring-brand-500'
              }`}
            />
            {errors.id && <p className="text-xs text-red-600 mt-1">{errors.id}</p>}
          </>
        )}
      </div>

      {/* Route */}
      <div>
        <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
          Route <span className="text-slate-400 font-normal normal-case">(optional)</span>
        </label>
        <input
          type="text"
          value={form.route}
          onChange={(e) => set('route', e.target.value)}
          placeholder="e.g. Route 534"
          className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
        />
      </div>

      {/* Status + Camera Status */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
            Bus Status
          </label>
          <select
            value={form.status}
            onChange={(e) => set('status', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white focus:outline-none focus:border-brand-500"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">
            Camera Status
          </label>
          <select
            value={form.camera_status}
            onChange={(e) => set('camera_status', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white focus:outline-none focus:border-brand-500"
          >
            {CAMERA_OPTIONS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      {/* API Error */}
      {apiError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
          <span>{apiError}</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="px-4 py-2 text-sm font-medium border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition disabled:opacity-50 cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 text-sm font-medium bg-slate-900 text-white rounded-md hover:bg-slate-700 transition disabled:opacity-60 cursor-pointer flex items-center gap-2"
        >
          {submitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
          {isEdit ? 'Save Changes' : 'Register Bus'}
        </button>
      </div>
    </form>
  );
}

// ── Delete Confirmation ───────────────────────────────────────────────────────

function DeleteConfirm({ bus, onConfirm, onCancel, deleting, apiError }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-700">
        Are you sure you want to <strong>permanently delete</strong> bus{' '}
        <span className="font-mono font-bold text-slate-900">{bus.id}</span>?
      </p>
      <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
        ⚠️ If this bus has associated events, the deletion will be blocked. You can set the bus status
        to <strong>Offline</strong> instead to deactivate it without losing history.
      </p>

      {apiError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
          <span>{apiError}</span>
        </div>
      )}

      <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
        <button
          onClick={onCancel}
          disabled={deleting}
          className="px-4 py-2 text-sm font-medium border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition cursor-pointer"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={deleting}
          className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-md hover:bg-red-700 transition disabled:opacity-60 cursor-pointer flex items-center gap-2"
        >
          {deleting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
          Delete Bus
        </button>
      </div>
    </div>
  );
}

// ── Modal Wrapper ─────────────────────────────────────────────────────────────

function Modal({ title, icon: Icon, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md overflow-hidden border border-slate-200">
        <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
          <div className="flex items-center gap-2">
            {Icon && <Icon className="w-5 h-5 text-slate-700" />}
            <h3 className="font-bold text-slate-800">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-200 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function FleetManagement() {
  const [buses, setBuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const [connState, setConnState] = useState(getConnectionState());

  // Modal states
  const [modal, setModal] = useState(null); // null | 'create' | 'edit' | 'delete'
  const [selectedBus, setSelectedBus] = useState(null);

  // Per-operation state
  const [submitting, setSubmitting] = useState(false);
  const [opError, setOpError] = useState('');

  // Toast
  const [toast, setToast] = useState(null);

  // Subscribe to connection state changes
  useEffect(() => {
    const unsub = subscribeConnectionState(setConnState);
    return unsub;
  }, []);

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4500);
  }, []);

  const closeModal = () => {
    setModal(null);
    setSelectedBus(null);
    setOpError('');
    setSubmitting(false);
  };

  // ── Load buses ──────────────────────────────────────────────────────────────

  const loadBuses = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    try {
      const data = await getBuses();
      setBuses(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      console.error('[FleetManagement] Failed to load buses:', err);
      setError(err.message || 'Failed to load fleet data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadBuses(false);
  }, [loadBuses]);

  // ── CRUD handlers ───────────────────────────────────────────────────────────

  const handleCreate = async (formData) => {
    setSubmitting(true);
    setOpError('');
    try {
      const created = await createBus(formData);
      setBuses((prev) => [created, ...prev]);
      closeModal();
      showToast(`Bus ${created.id} registered successfully.`);
    } catch (err) {
      setOpError(err.message || 'Failed to create bus.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (formData) => {
    setSubmitting(true);
    setOpError('');
    try {
      const updated = await updateBus(selectedBus.id, {
        route: formData.route || null,
        status: formData.status,
        camera_status: formData.camera_status,
      });
      setBuses((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
      closeModal();
      showToast(`Bus ${updated.id} updated successfully.`);
    } catch (err) {
      setOpError(err.message || 'Failed to update bus.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setSubmitting(true);
    setOpError('');
    try {
      await deleteBus(selectedBus.id);
      setBuses((prev) => prev.filter((b) => b.id !== selectedBus.id));
      closeModal();
      showToast(`Bus ${selectedBus.id} deleted.`, 'success');
    } catch (err) {
      setOpError(err.message || 'Failed to delete bus.');
      setSubmitting(false);
    }
  };

  // ── Derived stats ───────────────────────────────────────────────────────────

  const totalBuses = buses.length;
  const activeBuses = buses.filter((b) => b.status === 'Active').length;
  const offlineOrMaint = buses.filter((b) => b.status !== 'Active').length;

  // ── Render ──────────────────────────────────────────────────────────────────

  if (loading && buses.length === 0) {
    return <LoadingState message="Loading fleet data..." />;
  }

  if (error && buses.length === 0) {
    return (
      <ErrorState
        title="Fleet Data Unavailable"
        message="Could not load the bus fleet. You can retry or switch to Demo Mode."
        onRetry={() => loadBuses(false)}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Toast */}
      <Toast toast={toast} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Fleet Management</h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => loadBuses(true)}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-2 text-sm border border-slate-300 text-slate-600 rounded-md hover:bg-slate-50 transition disabled:opacity-50 cursor-pointer"
            title="Refresh fleet list"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => { setModal('create'); setOpError(''); }}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-md hover:bg-slate-700 transition cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Add Bus
          </button>
        </div>
      </div>

      {/* Demo Mode Banner */}
      {connState.isDemo && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
          <WifiOff className="w-5 h-5 shrink-0 text-amber-600 mt-0.5" />
          <div>
            <p className="font-semibold">Offline / Demo Mode — Fleet displayed below is from demo data.</p>
            <p className="text-xs mt-0.5 text-amber-700">
              Add Bus, Edit, and Delete operations require the live FastAPI backend.
              Start it with: <code className="font-mono bg-amber-100 px-1 rounded">cd backend &amp;&amp; uvicorn app.main:app --reload --port 8000</code>
              {' '}then switch to "Live API" in Platform Settings (⚙).
            </p>
          </div>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 flex items-center gap-4">
          <div className="p-2.5 bg-slate-100 rounded-lg">
            <Bus className="w-6 h-6 text-slate-600" />
          </div>
          <div>
            <p className="text-xs text-slate-500 uppercase font-semibold">Total Fleet</p>
            <p className="text-2xl font-bold text-slate-800">{totalBuses}</p>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 flex items-center gap-4">
          <div className="p-2.5 bg-emerald-50 rounded-lg">
            <Bus className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <p className="text-xs text-slate-500 uppercase font-semibold">Active</p>
            <p className="text-2xl font-bold text-emerald-700">{activeBuses}</p>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 flex items-center gap-4">
          <div className="p-2.5 bg-amber-50 rounded-lg">
            <Bus className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <p className="text-xs text-slate-500 uppercase font-semibold">Maintenance / Offline</p>
            <p className="text-2xl font-bold text-amber-700">{offlineOrMaint}</p>
          </div>
        </div>
      </div>

      {/* Fleet Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        {buses.length === 0 ? (
          <div className="p-10 text-center">
            <Bus className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No buses registered.</p>
            <p className="text-xs text-slate-400 mt-1">Click "Add Bus" to register the first bus in the fleet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs text-slate-600 uppercase tracking-wide">
                  <th className="px-4 py-3 font-semibold">Bus ID</th>
                  <th className="px-4 py-3 font-semibold">Route</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Camera</th>
                  <th className="px-4 py-3 font-semibold">Traffic</th>
                  <th className="px-4 py-3 font-semibold">Last Seen</th>
                  <th className="px-4 py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {buses.map((bus) => (
                  <tr key={bus.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-mono font-semibold text-slate-800">{bus.id}</td>
                    <td className="px-4 py-3 text-slate-600">{bus.route || <span className="text-slate-400 italic">—</span>}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${statusBadge(bus.status)}`}>
                        {bus.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cameraBadge(bus.camera_status)}`}>
                        {bus.camera_status}
                      </span>
                    </td>
                    <td className={`px-4 py-3 text-xs ${trafficBadge(bus.last_traffic)}`}>
                      {bus.last_traffic || 'Unknown'}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      <div className="font-semibold text-slate-800">{formatDate(bus.last_seen)}</div>
                      <div className="text-[11px] text-brand-600 font-medium">{formatRelativeTime(bus.last_seen)}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => { setSelectedBus(bus); setModal('edit'); setOpError(''); }}
                          className="text-slate-500 hover:text-brand-600 p-1.5 rounded hover:bg-brand-50 transition cursor-pointer"
                          title={`Edit ${bus.id}`}
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => { setSelectedBus(bus); setModal('delete'); setOpError(''); }}
                          className="text-slate-500 hover:text-red-600 p-1.5 rounded hover:bg-red-50 transition cursor-pointer"
                          title={`Delete ${bus.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Modals ──────────────────────────────────────────────────────────── */}

      {modal === 'create' && (
        <Modal title="Register New Bus" icon={Plus} onClose={closeModal}>
          <BusForm
            onSubmit={handleCreate}
            onCancel={closeModal}
            submitting={submitting}
            apiError={opError}
          />
        </Modal>
      )}

      {modal === 'edit' && selectedBus && (
        <Modal title={`Edit Bus — ${selectedBus.id}`} icon={Pencil} onClose={closeModal}>
          <BusForm
            initial={{
              id: selectedBus.id,
              route: selectedBus.route || '',
              status: selectedBus.status || 'Active',
              camera_status: selectedBus.camera_status || 'Active',
            }}
            isEdit
            onSubmit={handleUpdate}
            onCancel={closeModal}
            submitting={submitting}
            apiError={opError}
          />
        </Modal>
      )}

      {modal === 'delete' && selectedBus && (
        <Modal title={`Delete Bus — ${selectedBus.id}`} icon={Trash2} onClose={closeModal}>
          <DeleteConfirm
            bus={selectedBus}
            onConfirm={handleDelete}
            onCancel={closeModal}
            deleting={submitting}
            apiError={opError}
          />
        </Modal>
      )}
    </div>
  );
}
