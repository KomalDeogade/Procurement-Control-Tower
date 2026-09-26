/**
 * RFQ Page – generate and track Request For Quotations.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';

interface RFQ {
  id: number;
  display_id: string | null;
  requirement_id: number;
  supplier_id: number;
  status: string;
  response_deadline: string | null;
  notes: string | null;
  created_at: string;
}

interface Requirement { id: number; display_id: string | null; material_name: string; material_code: string; status: string; }
interface Supplier { id: number; company_name: string; supplier_code: string | null; approval_status: string; }

export default function RFQsPage() {
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGenerate, setShowGenerate] = useState(false);
  const [selectedReqId, setSelectedReqId] = useState('');
  const [selectedSupplierIds, setSelectedSupplierIds] = useState<number[]>([]);
  const [deadline, setDeadline] = useState('');
  const [generating, setGenerating] = useState(false);
  const [filterReqId, setFilterReqId] = useState('');

  const fetchAll = async () => {
    try {
      const [rfqRes, reqRes, supRes] = await Promise.all([
        api.get<RFQ[]>(`/rfqs/${filterReqId ? `?requirement_id=${filterReqId}` : ''}`),
        api.get<Requirement[]>('/requirements/'),
        api.get<Supplier[]>('/suppliers/?status=APPROVED'),
      ]);
      setRfqs(rfqRes.data);
      setRequirements(reqRes.data.filter(r => ['SUBMITTED', 'RFQ_IN_PROGRESS'].includes(r.status)));
      setSuppliers(supRes.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, [filterReqId]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReqId || selectedSupplierIds.length === 0) return;
    setGenerating(true);
    try {
      await api.post(`/rfqs/generate/${selectedReqId}`, selectedSupplierIds);
      setShowGenerate(false);
      setSelectedReqId('');
      setSelectedSupplierIds([]);
      await fetchAll();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate RFQs');
    } finally { setGenerating(false); }
  };

  const toggleSupplier = (id: number) => {
    setSelectedSupplierIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const getReqName = (id: number) =>
    requirements.find(r => r.id === id)?.material_name || `REQ #${id}`;

  const getSupplierName = (id: number) =>
    suppliers.find(s => s.id === id)?.company_name || `SUP #${id}`;

  // Group RFQs by requirement
  const rfqsByReq: Record<number, RFQ[]> = {};
  rfqs.forEach(r => {
    if (!rfqsByReq[r.requirement_id]) rfqsByReq[r.requirement_id] = [];
    rfqsByReq[r.requirement_id].push(r);
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">RFQ Management</h1>
          <p className="text-sm text-surface-500 mt-1">Send and track Request For Quotations to suppliers</p>
        </div>
        <button onClick={() => setShowGenerate(true)}
          className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
          + Generate RFQ
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total RFQs', value: rfqs.length, color: 'text-primary-600' },
          { label: 'Sent', value: rfqs.filter(r => r.status === 'SENT').length, color: 'text-blue-600' },
          { label: 'Responded', value: rfqs.filter(r => r.status === 'RESPONDED').length, color: 'text-green-600' },
          { label: 'Expired', value: rfqs.filter(r => r.status === 'EXPIRED').length, color: 'text-red-600' },
        ].map(stat => (
          <div key={stat.label} className="bg-white border border-surface-200 rounded-xl p-4">
            <p className="text-sm text-surface-500">{stat.label}</p>
            <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="bg-white rounded-xl border border-surface-200 p-4 mb-4">
        <select value={filterReqId} onChange={e => setFilterReqId(e.target.value)}
          className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
          <option value="">All Requirements</option>
          {[...new Set(rfqs.map(r => r.requirement_id))].map(id => (
            <option key={id} value={id}>{getReqName(id)} (#{id})</option>
          ))}
        </select>
      </div>

      {/* RFQ Table */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-surface-50 border-b border-surface-200">
              <tr>
                {['RFQ ID', 'Requirement', 'Supplier', 'Status', 'Deadline', 'Supplier Portal Link'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {rfqs.map(rfq => (
                <tr key={rfq.id} className="hover:bg-surface-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium text-primary-600">{rfq.display_id || `#${rfq.id}`}</td>
                  <td className="px-4 py-3 text-sm text-surface-700">{getReqName(rfq.requirement_id)}</td>
                  <td className="px-4 py-3 text-sm text-surface-700">{getSupplierName(rfq.supplier_id)}</td>
                  <td className="px-4 py-3"><StatusBadge status={rfq.status} /></td>
                  <td className="px-4 py-3 text-sm text-surface-600">
                    {rfq.response_deadline ? new Date(rfq.response_deadline).toLocaleDateString('en-IN') : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <a
                      href={`/supplier/rfq/${rfq.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary-600 underline hover:text-primary-800"
                    >
                      /supplier/rfq/{rfq.id}
                    </a>
                  </td>
                </tr>
              ))}
              {rfqs.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-surface-400 text-sm">No RFQs found. Generate an RFQ to get started.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Generate RFQ Modal */}
      <Modal isOpen={showGenerate} onClose={() => setShowGenerate(false)} title="Generate RFQ" size="lg">
        <form onSubmit={handleGenerate} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Select Requirement *</label>
            <select required value={selectedReqId} onChange={e => setSelectedReqId(e.target.value)}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
              <option value="">— Select a requirement —</option>
              {requirements.map(r => (
                <option key={r.id} value={r.id}>{r.display_id} · {r.material_name}</option>
              ))}
            </select>
            {requirements.length === 0 && (
              <p className="text-xs text-amber-600 mt-1">No submitted requirements available. Submit a requirement first.</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-2">Select Suppliers * ({selectedSupplierIds.length} selected)</label>
            <div className="border border-surface-200 rounded-lg max-h-48 overflow-y-auto divide-y divide-surface-100">
              {suppliers.map(s => (
                <label key={s.id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-surface-50 cursor-pointer">
                  <input type="checkbox" checked={selectedSupplierIds.includes(s.id)} onChange={() => toggleSupplier(s.id)}
                    className="rounded border-surface-300 text-primary-600" />
                  <span className="text-sm text-surface-700">{s.company_name}</span>
                  <span className="text-xs text-surface-400 ml-auto">{s.supplier_code}</span>
                </label>
              ))}
              {suppliers.length === 0 && (
                <p className="px-4 py-3 text-sm text-surface-400">No approved suppliers found.</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Response Deadline</label>
            <input type="date" value={deadline} onChange={e => setDeadline(e.target.value)}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowGenerate(false)}
              className="px-4 py-2 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors">Cancel</button>
            <button type="submit" disabled={generating || !selectedReqId || selectedSupplierIds.length === 0}
              className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {generating ? 'Generating...' : `Generate ${selectedSupplierIds.length} RFQ(s)`}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
