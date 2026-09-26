/**
 * Suppliers Page – list, search, filter, detail panel with scores.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';

interface Supplier {
  id: number;
  supplier_code: string | null;
  company_name: string;
  contact_person: string | null;
  email: string | null;
  phone: string | null;
  designation: string | null;
  registration_number: string | null;
  category: string | null;
  location: string | null;
  quality_score: number;
  delivery_score: number;
  risk_score: number;
  payment_terms: string | null;
  approval_status: string;
  created_at: string;
}

const RISK_COLOR = (score: number) =>
  score >= 60 ? 'text-red-600' : score >= 30 ? 'text-amber-600' : 'text-green-600';

const SCORE_BAR = (score: number, color: string) => (
  <div className="flex items-center gap-2">
    <div className="flex-1 bg-surface-100 rounded-full h-2">
      <div className={`${color} rounded-full h-2 transition-all`} style={{ width: `${score}%` }} />
    </div>
    <span className="text-xs font-medium text-surface-600 w-8 text-right">{score.toFixed(0)}</span>
  </div>
);

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState<Supplier | null>(null);

  const fetchSuppliers = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (categoryFilter) params.set('category', categoryFilter);
      if (statusFilter) params.set('status', statusFilter);
      const res = await api.get<Supplier[]>(`/suppliers/?${params}`);
      setSuppliers(res.data);
    } catch {
      setError('Failed to load suppliers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSuppliers(); }, [categoryFilter, statusFilter]);

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); fetchSuppliers(); };

  const categories = [...new Set(suppliers.map(s => s.category).filter(Boolean))];

  const getRiskLabel = (score: number) =>
    score >= 60 ? 'HIGH RISK' : score >= 30 ? 'MEDIUM' : 'LOW RISK';

  const handleApprove = async (supplier: Supplier) => {
    try {
      await api.patch(`/suppliers/${supplier.id}`, { approval_status: 'APPROVED' });
      await fetchSuppliers();
      if (selected?.id === supplier.id) setSelected({ ...selected, approval_status: 'APPROVED' });
    } catch { alert('Failed to update supplier'); }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Suppliers</h1>
          <p className="text-sm text-surface-500 mt-1">Manage supplier relationships and performance</p>
        </div>
        <div className="flex gap-2 text-sm">
          <span className="px-3 py-1 bg-green-50 text-green-700 rounded-full font-medium">
            {suppliers.filter(s => s.approval_status === 'APPROVED').length} Approved
          </span>
          <span className="px-3 py-1 bg-amber-50 text-amber-700 rounded-full font-medium">
            {suppliers.filter(s => s.approval_status === 'PENDING').length} Pending
          </span>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-xl border border-surface-200 p-4 mb-4 flex flex-wrap gap-3">
        <form onSubmit={handleSearch} className="flex flex-1 min-w-60 gap-2">
          <input
            type="text"
            placeholder="Search company, code, location..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 px-3 py-2 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button type="submit" className="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors">
            Search
          </button>
        </form>
        <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}
          className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
          <option value="">All Categories</option>
          {categories.map(c => <option key={c!} value={c!}>{c}</option>)}
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
          <option value="">All Statuses</option>
          <option value="APPROVED">Approved</option>
          <option value="PENDING">Pending</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>

      {/* Supplier Grid */}
      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">{error}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {suppliers.map(supplier => (
            <div key={supplier.id}
              onClick={() => setSelected(supplier)}
              className="bg-white rounded-xl border border-surface-200 p-5 hover:shadow-md hover:border-primary-200 transition-all cursor-pointer">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-surface-400">{supplier.supplier_code}</span>
                    <StatusBadge status={supplier.approval_status} />
                  </div>
                  <h3 className="text-sm font-semibold text-surface-900 mt-1">{supplier.company_name}</h3>
                  <p className="text-xs text-surface-500">{supplier.category} · {supplier.location}</p>
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                  supplier.risk_score >= 60 ? 'bg-red-50 text-red-600' :
                  supplier.risk_score >= 30 ? 'bg-amber-50 text-amber-600' : 'bg-green-50 text-green-600'
                }`}>
                  {getRiskLabel(supplier.risk_score)}
                </span>
              </div>

              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs text-surface-500 mb-1">
                    <span>Quality</span>
                  </div>
                  {SCORE_BAR(supplier.quality_score, 'bg-blue-500')}
                </div>
                <div>
                  <div className="flex justify-between text-xs text-surface-500 mb-1">
                    <span>Delivery</span>
                  </div>
                  {SCORE_BAR(supplier.delivery_score, 'bg-green-500')}
                </div>
                <div>
                  <div className="flex justify-between text-xs text-surface-500 mb-1">
                    <span>Risk</span>
                  </div>
                  {SCORE_BAR(supplier.risk_score, supplier.risk_score >= 60 ? 'bg-red-500' : supplier.risk_score >= 30 ? 'bg-amber-500' : 'bg-green-500')}
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-surface-100 flex items-center justify-between">
                <span className="text-xs text-surface-500">{supplier.payment_terms || 'No payment terms'}</span>
                <span className="text-xs text-primary-600 font-medium">View Details →</span>
              </div>
            </div>
          ))}
          {suppliers.length === 0 && (
            <div className="col-span-3 text-center py-16 text-surface-400 text-sm">No suppliers found</div>
          )}
        </div>
      )}

      {/* Supplier Detail Modal */}
      {selected && (
        <Modal isOpen={!!selected} onClose={() => setSelected(null)} title={selected.company_name} size="lg">
          <div className="grid grid-cols-2 gap-6">
            {/* Left column */}
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">Company Info</h4>
                <div className="space-y-2">
                  {[
                    ['Supplier Code', selected.supplier_code],
                    ['Category', selected.category],
                    ['Location', selected.location],
                    ['Registration No.', selected.registration_number],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between text-sm">
                      <span className="text-surface-500">{label}</span>
                      <span className="font-medium text-surface-800">{value || '—'}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">Contact</h4>
                <div className="space-y-2">
                  {[
                    ['Name', selected.contact_person],
                    ['Designation', selected.designation],
                    ['Email', selected.email],
                    ['Phone', selected.phone],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between text-sm">
                      <span className="text-surface-500">{label}</span>
                      <span className="font-medium text-surface-800">{value || '—'}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">Commercial</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-surface-500">Payment Terms</span>
                    <span className="font-medium text-surface-800">{selected.payment_terms || '—'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-surface-500">Approval Status</span>
                    <StatusBadge status={selected.approval_status} />
                  </div>
                </div>
              </div>
            </div>

            {/* Right column – scores */}
            <div>
              <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Performance Scores</h4>
              <div className="space-y-4">
                <div className="bg-surface-50 rounded-xl p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-surface-700">Quality Score</span>
                    <span className="text-2xl font-bold text-blue-600">{selected.quality_score.toFixed(0)}</span>
                  </div>
                  {SCORE_BAR(selected.quality_score, 'bg-blue-500')}
                </div>
                <div className="bg-surface-50 rounded-xl p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-surface-700">Delivery Score</span>
                    <span className="text-2xl font-bold text-green-600">{selected.delivery_score.toFixed(0)}</span>
                  </div>
                  {SCORE_BAR(selected.delivery_score, 'bg-green-500')}
                </div>
                <div className="bg-surface-50 rounded-xl p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-surface-700">Risk Score</span>
                    <span className={`text-2xl font-bold ${RISK_COLOR(selected.risk_score)}`}>{selected.risk_score.toFixed(0)}</span>
                  </div>
                  {SCORE_BAR(selected.risk_score, selected.risk_score >= 60 ? 'bg-red-500' : selected.risk_score >= 30 ? 'bg-amber-500' : 'bg-green-500')}
                  <p className="text-xs text-surface-400 mt-1">Lower is better</p>
                </div>
              </div>

              {selected.approval_status === 'PENDING' && (
                <button
                  onClick={() => handleApprove(selected)}
                  className="w-full mt-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors">
                  Approve Supplier
                </button>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
