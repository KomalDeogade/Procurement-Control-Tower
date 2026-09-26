/**
 * Goods Receipts (GRN) Page – receive goods, auto-update inventory.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import Modal from '../components/ui/Modal';

interface GRN {
  id: number;
  display_id: string | null;
  po_id: number;
  received_quantity: number;
  received_date: string | null;
  quality_status: string;
  inspector: string | null;
  remarks: string | null;
  sap_grn_number: string | null;
  created_at: string;
}

interface PO {
  id: number;
  display_id: string | null;
  material_name: string | null;
  material_code: string;
  quantity: number;
  supplier_id: number;
  status: string;
}

const EMPTY_GRN = { po_id: '', received_quantity: '', quality_status: 'PASSED', inspector: '', remarks: '' };

export default function GoodsReceiptsPage() {
  const [grns, setGrns] = useState<GRN[]>([]);
  const [pos, setPOs] = useState<PO[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(EMPTY_GRN);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const fetchAll = async () => {
    try {
      const [grnRes, poRes] = await Promise.all([
        api.get<GRN[]>('/goods-receipts/'),
        api.get<PO[]>('/purchase-orders/'),
      ]);
      setGrns(grnRes.data);
      setPOs(poRes.data.filter(p => ['SAP_CREATED', 'PARTIALLY_RECEIVED'].includes(p.status)));
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const getSelectedPO = () => pos.find(p => p.id === parseInt(form.po_id));

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      const res = await api.post<GRN>('/goods-receipts/', {
        po_id: parseInt(form.po_id),
        received_quantity: parseFloat(form.received_quantity),
        quality_status: form.quality_status,
        inspector: form.inspector || null,
        remarks: form.remarks || null,
      });
      setShowCreate(false);
      setForm(EMPTY_GRN);
      setSuccessMsg(`GRN ${res.data.display_id} created. Inventory updated automatically.`);
      await fetchAll();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create GRN');
    } finally { setSubmitting(false); }
  };

  const getPODisplay = (id: number) => pos.find(p => p.id === id)?.display_id || `PO#${id}`;
  const getPOMaterial = (id: number) => {
    const po = pos.find(p => p.id === id);
    return po ? (po.material_name || po.material_code) : `Material for PO#${id}`;
  };

  const QUALITY_COLORS: Record<string, string> = {
    PASSED: 'bg-green-100 text-green-700',
    FAILED: 'bg-red-100 text-red-700',
    PENDING_INSPECTION: 'bg-amber-100 text-amber-700',
    PARTIAL: 'bg-yellow-100 text-yellow-700',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Goods Receipts (GRN)</h1>
          <p className="text-sm text-surface-500 mt-1">Record received goods and automatically update inventory</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
          + New GRN
        </button>
      </div>

      {successMsg && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 text-green-700 rounded-xl text-sm flex justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg('')} className="text-green-500 hover:text-green-700">✕</button>
        </div>
      )}

      {/* GRN Table */}
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
                  {['GRN Number', 'Purchase Order', 'Material', 'Received Qty', 'Quality', 'Inspector', 'Received Date', 'Remarks'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {grns.map(grn => (
                  <tr key={grn.id} className="hover:bg-surface-50 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-primary-600">{grn.display_id}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{getPODisplay(grn.po_id)}</td>
                    <td className="px-4 py-3 text-sm text-surface-700">{getPOMaterial(grn.po_id)}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-surface-900">{grn.received_quantity.toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${QUALITY_COLORS[grn.quality_status] || 'bg-surface-100 text-surface-600'}`}>
                        {grn.quality_status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-surface-600">{grn.inspector || '—'}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">
                      {grn.received_date ? new Date(grn.received_date).toLocaleDateString('en-IN') :
                        grn.created_at ? new Date(grn.created_at).toLocaleDateString('en-IN') : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-surface-500 max-w-xs truncate">{grn.remarks || '—'}</td>
                  </tr>
                ))}
                {grns.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-surface-400 text-sm">
                      No GRNs recorded yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info banner */}
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-700">
        <strong>Auto-Inventory Update:</strong> When a GRN is created, inventory is updated automatically.
        The system creates an inventory transaction record and increases the available stock.
      </div>

      {/* Create GRN Modal */}
      <Modal isOpen={showCreate} onClose={() => { setShowCreate(false); setForm(EMPTY_GRN); setFormError(''); }}
        title="Record Goods Receipt (GRN)">
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <div className="bg-red-50 text-red-700 text-sm px-4 py-2 rounded-lg border border-red-200">{formError}</div>}

          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Purchase Order *</label>
            <select required value={form.po_id} onChange={e => setForm(f => ({ ...f, po_id: e.target.value, received_quantity: String(pos.find(p => p.id === parseInt(e.target.value))?.quantity || '') }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
              <option value="">— Select PO (SAP Created / Partially Received) —</option>
              {pos.map(p => (
                <option key={p.id} value={p.id}>{p.display_id} · {p.material_name || p.material_code} · {p.quantity} units</option>
              ))}
            </select>
            {pos.length === 0 && (
              <p className="text-xs text-amber-600 mt-1">No POs available for GRN. Create and SAP-sync a PO first.</p>
            )}
          </div>

          {getSelectedPO() && (
            <div className="bg-surface-50 rounded-lg p-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div><span className="text-surface-500">PO Quantity:</span> <strong>{getSelectedPO()?.quantity.toLocaleString()}</strong></div>
                <div><span className="text-surface-500">Material:</span> <strong>{getSelectedPO()?.material_name || getSelectedPO()?.material_code}</strong></div>
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Received Quantity *</label>
            <input required type="number" step="0.01" value={form.received_quantity}
              onChange={e => setForm(f => ({ ...f, received_quantity: e.target.value }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none"
              placeholder="Enter received quantity" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Quality Status</label>
            <select value={form.quality_status} onChange={e => setForm(f => ({ ...f, quality_status: e.target.value }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
              <option value="PASSED">PASSED – Goods accepted</option>
              <option value="FAILED">FAILED – Goods rejected</option>
              <option value="PARTIAL">PARTIAL – Partial acceptance</option>
              <option value="PENDING_INSPECTION">PENDING INSPECTION</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Inspector Name</label>
            <input value={form.inspector} onChange={e => setForm(f => ({ ...f, inspector: e.target.value }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none"
              placeholder="e.g. Rajesh Kumar" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Remarks</label>
            <textarea rows={2} value={form.remarks} onChange={e => setForm(f => ({ ...f, remarks: e.target.value }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:outline-none"
              placeholder="Inspection notes, condition of goods..." />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => { setShowCreate(false); setForm(EMPTY_GRN); setFormError(''); }}
              className="px-4 py-2 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors">Cancel</button>
            <button type="submit" disabled={submitting}
              className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {submitting ? 'Recording...' : 'Record GRN'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
