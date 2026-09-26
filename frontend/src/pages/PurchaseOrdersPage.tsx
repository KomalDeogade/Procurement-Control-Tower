/**
 * Purchase Orders Page – create POs, SAP sync, GRN tracking.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import Modal from '../components/ui/Modal';

interface PurchaseOrder {
  id: number;
  display_id: string | null;
  requirement_id: number;
  supplier_id: number;
  quote_id: number | null;
  sap_po_number: string | null;
  material_code: string;
  material_name: string | null;
  quantity: number;
  unit_price: number;
  total_amount: number;
  currency: string;
  delivery_date: string | null;
  payment_terms: string | null;
  status: string;
  notes: string | null;
  created_by: number | null;
  created_at: string;
}

interface Requirement { id: number; display_id: string | null; material_name: string; material_code: string; quantity: number; unit: string; status: string; }
interface Supplier { id: number; company_name: string; supplier_code: string | null; }
interface Quote { id: number; display_id: string; supplier_id: number; unit_price: number; total_price: number; payment_terms: string | null; delivery_date: string | null; }

const PO_STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-surface-100 text-surface-600',
  SAP_CREATED: 'bg-blue-100 text-blue-700',
  PARTIALLY_RECEIVED: 'bg-amber-100 text-amber-700',
  FULLY_RECEIVED: 'bg-green-100 text-green-700',
  CLOSED: 'bg-emerald-100 text-emerald-700',
  CANCELLED: 'bg-red-100 text-red-700',
};

const EMPTY_PO_FORM = {
  requirement_id: '', supplier_id: '', quote_id: '',
  material_code: '', material_name: '', quantity: '',
  unit_price: '', total_amount: '', currency: 'INR',
  delivery_date: '', payment_terms: 'NET 30', notes: '',
};

export default function PurchaseOrdersPage() {
  const [pos, setPOs] = useState<PurchaseOrder[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(EMPTY_PO_FORM);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [sapSyncing, setSapSyncing] = useState<number | null>(null);
  const [sapResult, setSapResult] = useState<any>(null);
  const [availableQuotes, setAvailableQuotes] = useState<Quote[]>([]);

  const fetchAll = async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const [poRes, reqRes, supRes] = await Promise.all([
        api.get<PurchaseOrder[]>(`/purchase-orders/${params}`),
        api.get<Requirement[]>('/requirements/?status=APPROVED'),
        api.get<Supplier[]>('/suppliers/'),
      ]);
      setPOs(poRes.data);
      setRequirements(reqRes.data);
      setSuppliers(supRes.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, [statusFilter]);

  const onRequirementChange = async (reqId: string) => {
    setForm(f => ({ ...f, requirement_id: reqId, quote_id: '', supplier_id: '', unit_price: '', total_amount: '' }));
    if (!reqId) return;
    try {
      const res = await api.get<Quote[]>(`/quotes/?requirement_id=${reqId}`);
      setAvailableQuotes(res.data);
      const req = requirements.find(r => r.id === parseInt(reqId));
      if (req) setForm(f => ({ ...f, material_code: req.material_code, material_name: req.material_name, quantity: String(req.quantity) }));
    } catch { setAvailableQuotes([]); }
  };

  const onQuoteChange = (quoteId: string) => {
    const q = availableQuotes.find(q => q.id === parseInt(quoteId));
    if (q) {
      setForm(f => ({
        ...f, quote_id: quoteId, supplier_id: String(q.supplier_id),
        unit_price: String(q.unit_price), total_amount: String(q.total_price),
        payment_terms: q.payment_terms || 'NET 30',
        delivery_date: q.delivery_date ? q.delivery_date.split('T')[0] : '',
      }));
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      await api.post('/purchase-orders/', {
        requirement_id: parseInt(form.requirement_id),
        supplier_id: parseInt(form.supplier_id),
        quote_id: form.quote_id ? parseInt(form.quote_id) : null,
        material_code: form.material_code,
        material_name: form.material_name,
        quantity: parseFloat(form.quantity),
        unit_price: parseFloat(form.unit_price),
        total_amount: parseFloat(form.total_amount),
        currency: form.currency,
        delivery_date: form.delivery_date ? new Date(form.delivery_date).toISOString() : null,
        payment_terms: form.payment_terms,
        notes: form.notes || null,
      });
      setShowCreate(false);
      setForm(EMPTY_PO_FORM);
      await fetchAll();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create PO');
    } finally { setSubmitting(false); }
  };

  const handleSapSync = async (po: PurchaseOrder) => {
    setSapSyncing(po.id);
    setSapResult(null);
    try {
      const res = await api.post(`/purchase-orders/${po.id}/sync-sap`);
      setSapResult(res.data);
      await fetchAll();
    } catch (err: any) {
      setSapResult({ error: err.response?.data?.detail || 'SAP sync failed' });
    } finally { setSapSyncing(null); }
  };

  const getSupplierName = (id: number) => suppliers.find(s => s.id === id)?.company_name || `SUP#${id}`;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Purchase Orders</h1>
          <p className="text-sm text-surface-500 mt-1">Create and manage procurement purchase orders</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
          + Create PO
        </button>
      </div>

      {sapResult && (
        <div className={`mb-4 p-4 rounded-xl border text-sm ${sapResult.error ? 'bg-red-50 border-red-200 text-red-700' : 'bg-blue-50 border-blue-200 text-blue-700'}`}>
          {sapResult.error ? sapResult.error : (
            <div>
              <span className="font-semibold">Mock SAP Sync:</span>{' '}
              <span>{sapResult.po_id}</span> →{' '}
              <span className="font-mono">SAP PO: {sapResult.sap_po_number}</span>{' '}
              <span className="text-blue-500 text-xs ml-2">({sapResult.disclaimer})</span>
            </div>
          )}
          <button onClick={() => setSapResult(null)} className="ml-3 opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Status filter tabs */}
      <div className="bg-white rounded-xl border border-surface-200 p-3 mb-4 flex gap-2 flex-wrap">
        {['', 'DRAFT', 'SAP_CREATED', 'PARTIALLY_RECEIVED', 'FULLY_RECEIVED', 'CLOSED', 'CANCELLED'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${
              statusFilter === s ? 'bg-primary-600 text-white' : 'text-surface-600 hover:bg-surface-100'
            }`}>
            {s || 'All'} {s === '' && `(${pos.length})`}
          </button>
        ))}
      </div>

      {/* PO Table */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-50 border-b border-surface-200">
                <tr>
                  {['PO Number', 'Material', 'Supplier', 'Qty', 'Total Amount', 'SAP PO', 'Delivery', 'Payment', 'Status', 'Actions'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {pos.map(po => (
                  <tr key={po.id} className="hover:bg-surface-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-primary-600">{po.display_id}</div>
                      <div className="text-xs text-surface-400">REQ #{po.requirement_id}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-surface-900">{po.material_name || po.material_code}</div>
                      <div className="text-xs text-surface-500">{po.material_code}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-surface-700">{getSupplierName(po.supplier_id)}</td>
                    <td className="px-4 py-3 text-sm text-surface-700">{po.quantity.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-surface-900">
                      ₹{po.total_amount.toLocaleString('en-IN')}
                    </td>
                    <td className="px-4 py-3">
                      {po.sap_po_number ? (
                        <div>
                          <div className="text-xs font-mono text-blue-600">{po.sap_po_number}</div>
                          <div className="text-xs text-green-500">SYNC'd</div>
                        </div>
                      ) : <span className="text-surface-300 text-xs">—</span>}
                    </td>
                    <td className="px-4 py-3 text-sm text-surface-600">
                      {po.delivery_date ? new Date(po.delivery_date).toLocaleDateString('en-IN') : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-surface-600">{po.payment_terms || '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PO_STATUS_COLORS[po.status] || 'bg-surface-100 text-surface-600'}`}>
                        {po.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {po.status === 'DRAFT' && (
                        <button onClick={() => handleSapSync(po)} disabled={sapSyncing === po.id}
                          className="px-2 py-1 text-xs font-medium text-blue-600 border border-blue-200 rounded hover:bg-blue-50 disabled:opacity-50 transition-colors whitespace-nowrap">
                          {sapSyncing === po.id ? 'Syncing...' : 'SAP Sync'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {pos.length === 0 && (
                  <tr>
                    <td colSpan={10} className="px-4 py-12 text-center text-surface-400 text-sm">No purchase orders found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create PO Modal */}
      <Modal isOpen={showCreate} onClose={() => { setShowCreate(false); setForm(EMPTY_PO_FORM); setFormError(''); }}
        title="Create Purchase Order" size="lg">
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <div className="bg-red-50 text-red-700 text-sm px-4 py-2 rounded-lg border border-red-200">{formError}</div>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Requirement *</label>
              <select required value={form.requirement_id} onChange={e => onRequirementChange(e.target.value)}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
                <option value="">— Select requirement —</option>
                {requirements.map(r => <option key={r.id} value={r.id}>{r.display_id} · {r.material_name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Select Quote</label>
              <select value={form.quote_id} onChange={e => onQuoteChange(e.target.value)}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
                <option value="">— Select from quotes —</option>
                {availableQuotes.map(q => <option key={q.id} value={q.id}>{q.display_id} · ₹{q.total_price.toLocaleString('en-IN')}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Supplier *</label>
              <select required value={form.supplier_id} onChange={e => setForm(f => ({ ...f, supplier_id: e.target.value }))}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
                <option value="">— Select supplier —</option>
                {suppliers.map(s => <option key={s.id} value={s.id}>{s.company_name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Material Code *</label>
              <input required value={form.material_code} onChange={e => setForm(f => ({ ...f, material_code: e.target.value }))}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Quantity *</label>
              <input required type="number" value={form.quantity} onChange={e => {
                const q = parseFloat(e.target.value) || 0;
                const up = parseFloat(form.unit_price) || 0;
                setForm(f => ({ ...f, quantity: e.target.value, total_amount: up > 0 ? String(q * up) : f.total_amount }));
              }}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Unit Price *</label>
              <input required type="number" step="0.01" value={form.unit_price} onChange={e => {
                const up = parseFloat(e.target.value) || 0;
                const q = parseFloat(form.quantity) || 0;
                setForm(f => ({ ...f, unit_price: e.target.value, total_amount: q > 0 ? String(q * up) : f.total_amount }));
              }}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Total Amount *</label>
              <input required type="number" step="0.01" value={form.total_amount} onChange={e => setForm(f => ({ ...f, total_amount: e.target.value }))}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Payment Terms</label>
              <select value={form.payment_terms} onChange={e => setForm(f => ({ ...f, payment_terms: e.target.value }))}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
                {['NET 15', 'NET 30', 'NET 45', 'NET 60', 'ADVANCE', 'COD'].map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Delivery Date</label>
              <input type="date" value={form.delivery_date} onChange={e => setForm(f => ({ ...f, delivery_date: e.target.value }))}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Notes</label>
            <textarea rows={2} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:outline-none" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => { setShowCreate(false); setForm(EMPTY_PO_FORM); setFormError(''); }}
              className="px-4 py-2 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors">Cancel</button>
            <button type="submit" disabled={submitting}
              className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {submitting ? 'Creating...' : 'Create PO'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
