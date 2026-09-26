/**
 * Requirements Page – full CRUD with form, filters, status tracking.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';

interface Requirement {
  id: number;
  display_id: string | null;
  material_code: string;
  material_name: string;
  description: string | null;
  quantity: number;
  unit: string;
  plant: string | null;
  required_by_date: string | null;
  budget: number | null;
  currency: string;
  priority: string;
  status: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  LOW: 'bg-surface-100 text-surface-600',
  MEDIUM: 'bg-blue-100 text-blue-700',
  HIGH: 'bg-amber-100 text-amber-700',
  CRITICAL: 'bg-red-100 text-red-700',
};

const STATUSES = ['', 'DRAFT', 'SUBMITTED', 'RFQ_IN_PROGRESS', 'QUOTES_RECEIVED', 'UNDER_REVIEW', 'APPROVAL_PENDING', 'APPROVED', 'REJECTED', 'PO_CREATED', 'COMPLETED', 'CANCELLED'];

const EMPTY_FORM = {
  material_code: '',
  material_name: '',
  description: '',
  quantity: '',
  unit: 'KG',
  plant: 'PLANT-01',
  required_by_date: '',
  budget: '',
  currency: 'INR',
  priority: 'MEDIUM',
};

export default function RequirementsPage() {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [selectedReq, setSelectedReq] = useState<Requirement | null>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [timelineLoading, setTimelineLoading] = useState(false);

  const fetchRequirements = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (priorityFilter) params.set('priority', priorityFilter);
      const res = await api.get<Requirement[]>(`/requirements/?${params}`);
      setRequirements(res.data);
    } catch {
      setError('Failed to load requirements');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRequirements(); }, [statusFilter, priorityFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      await api.post('/requirements/', {
        ...form,
        quantity: parseFloat(form.quantity),
        budget: form.budget ? parseFloat(form.budget) : null,
        required_by_date: form.required_by_date ? new Date(form.required_by_date).toISOString() : null,
      });
      setShowForm(false);
      setForm(EMPTY_FORM);
      await fetchRequirements();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create requirement');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = async (req: Requirement) => {
    try {
      await api.post(`/requirements/${req.id}/submit`);
      await fetchRequirements();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Cannot submit');
    }
  };

  const openTimeline = async (req: Requirement) => {
    setSelectedReq(req);
    setTimelineLoading(true);
    try {
      const res = await api.get(`/requirements/${req.id}/timeline`);
      setTimeline(res.data.timeline || []);
    } catch {
      setTimeline([]);
    } finally {
      setTimelineLoading(false);
    }
  };

  const filtered = requirements.filter(r => {
    if (!search) return true;
    return (
      r.material_name.toLowerCase().includes(search.toLowerCase()) ||
      r.material_code.toLowerCase().includes(search.toLowerCase()) ||
      (r.display_id || '').toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Requirements</h1>
          <p className="text-sm text-surface-500 mt-1">Create and manage procurement requirements</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
        >
          + New Requirement
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-surface-200 p-4 mb-4 flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search material, code, ID..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-48 px-3 py-2 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {STATUSES.map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
        </select>
        <select
          value={priorityFilter}
          onChange={e => setPriorityFilter(e.target.value)}
          className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Priorities</option>
          {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <span className="text-sm text-surface-500 self-center">{filtered.length} results</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="p-6 text-red-600">{error}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-50 border-b border-surface-200">
                <tr>
                  {['ID', 'Material', 'Qty / Unit', 'Plant', 'Required By', 'Budget', 'Priority', 'Status', 'Actions'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {filtered.map(req => (
                  <tr key={req.id} className="hover:bg-surface-50 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-primary-600">{req.display_id || `#${req.id}`}</td>
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-surface-900">{req.material_name}</div>
                      <div className="text-xs text-surface-500">{req.material_code}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-surface-700">{req.quantity.toLocaleString()} {req.unit}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{req.plant || '—'}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">
                      {req.required_by_date ? new Date(req.required_by_date).toLocaleDateString('en-IN') : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-surface-700">
                      {req.budget ? `₹${req.budget.toLocaleString('en-IN')}` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PRIORITY_COLORS[req.priority] || ''}`}>
                        {req.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={req.status} /></td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => openTimeline(req)}
                          className="px-2 py-1 text-xs font-medium text-primary-600 border border-primary-200 rounded hover:bg-primary-50 transition-colors"
                        >
                          Timeline
                        </button>
                        {req.status === 'DRAFT' && (
                          <button
                            onClick={() => handleSubmit(req)}
                            className="px-2 py-1 text-xs font-medium text-green-700 border border-green-200 rounded hover:bg-green-50 transition-colors"
                          >
                            Submit
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-surface-400 text-sm">No requirements found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal isOpen={showForm} onClose={() => { setShowForm(false); setForm(EMPTY_FORM); setFormError(''); }} title="New Procurement Requirement">
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <div className="bg-red-50 text-red-700 text-sm px-4 py-2 rounded-lg border border-red-200">{formError}</div>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Material Code *</label>
              <input required value={form.material_code} onChange={e => setForm({...form, material_code: e.target.value})}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" placeholder="MAT-001" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Material Name *</label>
              <input required value={form.material_name} onChange={e => setForm({...form, material_name: e.target.value})}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" placeholder="Industrial Lubricant XLR-500" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Quantity *</label>
              <input required type="number" min="0.01" step="0.01" value={form.quantity} onChange={e => setForm({...form, quantity: e.target.value})}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Unit</label>
              <select value={form.unit} onChange={e => setForm({...form, unit: e.target.value})}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
                {['KG', 'L', 'PCS', 'M', 'MT', 'BOX', 'SET', 'PAIR', 'UNIT'].map(u => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Plant</label>
              <input value={form.plant} onChange={e => setForm({...form, plant: e.target.value})}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" placeholder="PLANT-01" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Required By Date</label>
              <input type="date" value={form.required_by_date} onChange={e => setForm({...form, required_by_date: e.target.value})}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Budget (INR)</label>
              <input type="number" min="0" step="0.01" value={form.budget} onChange={e => setForm({...form, budget: e.target.value})}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" placeholder="80,00,000" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Priority</label>
              <select value={form.priority} onChange={e => setForm({...form, priority: e.target.value})}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
                {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Description</label>
            <textarea rows={3} value={form.description} onChange={e => setForm({...form, description: e.target.value})}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none resize-none"
              placeholder="Specify quality, grade, standards..." />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => { setShowForm(false); setForm(EMPTY_FORM); setFormError(''); }}
              className="px-4 py-2 text-sm font-medium text-surface-600 border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={submitting}
              className="px-4 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {submitting ? 'Creating...' : 'Create Requirement'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Timeline Modal */}
      {selectedReq && (
        <Modal isOpen={!!selectedReq} onClose={() => { setSelectedReq(null); setTimeline([]); }}
          title={`Timeline — ${selectedReq.display_id || selectedReq.material_name}`}>
          <div>
            <div className="mb-4 p-3 bg-surface-50 rounded-lg text-sm">
              <span className="font-medium">{selectedReq.material_name}</span>
              <span className="mx-2 text-surface-400">·</span>
              <StatusBadge status={selectedReq.status} />
              <span className="mx-2 text-surface-400">·</span>
              <span className="text-surface-500">{selectedReq.quantity.toLocaleString()} {selectedReq.unit}</span>
            </div>
            {timelineLoading ? (
              <div className="flex justify-center py-8">
                <div className="w-6 h-6 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
              </div>
            ) : timeline.length === 0 ? (
              <p className="text-sm text-surface-400 text-center py-8">No timeline events yet</p>
            ) : (
              <div className="relative pl-6">
                <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-surface-200" />
                {timeline.map((event: any, i: number) => (
                  <div key={i} className="mb-4 relative">
                    <div className={`absolute -left-4 w-3 h-3 rounded-full border-2 border-white ${
                      event.status === 'completed' ? 'bg-green-500' :
                      event.status === 'pending' ? 'bg-amber-400' : 'bg-surface-300'
                    }`} />
                    <div className="bg-white border border-surface-100 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-surface-800">{event.step}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          event.status === 'completed' ? 'bg-green-100 text-green-700' :
                          event.status === 'pending' ? 'bg-amber-100 text-amber-700' : 'bg-surface-100 text-surface-500'
                        }`}>{event.status}</span>
                      </div>
                      {event.detail && <p className="text-xs text-surface-500 mt-1">{event.detail}</p>}
                      {event.date && <p className="text-xs text-surface-400 mt-1">{new Date(event.date).toLocaleString('en-IN')}</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
