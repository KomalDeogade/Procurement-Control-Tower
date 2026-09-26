/**
 * Invoices Page – invoice management, 3-way match, payment due monitoring.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';

interface Invoice {
  id: number;
  display_id: string | null;
  po_id: number;
  supplier_id: number;
  invoice_amount: number;
  tax_amount: number;
  total_amount: number;
  invoice_date: string | null;
  due_date: string | null;
  status: string;
  sap_invoice_number: string | null;
  notes: string | null;
  created_at: string;
}

interface MatchResult {
  invoice_id: string;
  match_result: {
    status: string;
    exceptions: string[];
    po: { quantity: number; unit_price: number; total: number };
    grn_quantity: number;
    invoice: { quantity: number; unit_price: number; total: number };
    discrepancies: string[];
  };
  po: any;
  grn_total_quantity: number;
}

interface PaymentDue {
  invoice_id: string;
  supplier_name: string;
  amount: number;
  invoice_date: string;
  due_date: string;
  days_until_due: number;
  category: string;
}

interface PO { id: number; display_id: string | null; total_amount: number; quantity: number; unit_price: number; payment_terms: string | null; }

const EMPTY_INVOICE = { po_id: '', supplier_id: '', invoice_amount: '', tax_amount: '0', total_amount: '', invoice_date: '', due_date: '', notes: '' };

const DUE_COLORS: Record<string, string> = {
  OVERDUE: 'bg-red-50 border-red-200 text-red-700',
  DUE_TODAY: 'bg-red-50 border-red-200 text-red-600',
  DUE_1_3_DAYS: 'bg-amber-50 border-amber-200 text-amber-700',
  DUE_4_7_DAYS: 'bg-yellow-50 border-yellow-200 text-yellow-700',
  DUE_LATER: 'bg-green-50 border-green-200 text-green-700',
};

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(EMPTY_INVOICE);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [matching, setMatching] = useState<number | null>(null);
  const [paymentDue, setPaymentDue] = useState<any | null>(null);
  const [duePanelOpen, setDuePanelOpen] = useState(false);
  const [pos, setPOs] = useState<PO[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);

  const fetchAll = async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const [invRes, poRes, supRes] = await Promise.all([
        api.get<Invoice[]>(`/invoices/${params}`),
        api.get<PO[]>('/purchase-orders/'),
        api.get<any[]>('/suppliers/'),
      ]);
      setInvoices(invRes.data);
      setPOs(poRes.data);
      setSuppliers(supRes.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, [statusFilter]);

  const loadPaymentDue = async () => {
    try {
      const res = await api.get('/invoices/payment-due/monitor');
      setPaymentDue(res.data);
      setDuePanelOpen(true);
    } catch { /* ignore */ }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      await api.post('/invoices/', {
        po_id: parseInt(form.po_id),
        supplier_id: parseInt(form.supplier_id),
        invoice_amount: parseFloat(form.invoice_amount),
        tax_amount: parseFloat(form.tax_amount) || 0,
        total_amount: parseFloat(form.total_amount),
        invoice_date: form.invoice_date ? new Date(form.invoice_date).toISOString() : null,
        due_date: form.due_date ? new Date(form.due_date).toISOString() : null,
        notes: form.notes || null,
      });
      setShowCreate(false);
      setForm(EMPTY_INVOICE);
      await fetchAll();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create invoice');
    } finally { setSubmitting(false); }
  };

  const handleThreeWayMatch = async (inv: Invoice) => {
    setMatching(inv.id);
    setMatchResult(null);
    try {
      const res = await api.post<MatchResult>(`/invoices/${inv.id}/three-way-match`);
      setMatchResult(res.data);
      await fetchAll();
    } catch (err: any) {
      alert(err.response?.data?.detail || '3-way match failed');
    } finally { setMatching(null); }
  };

  const onPoChange = (poId: string) => {
    const po = pos.find(p => p.id === parseInt(poId));
    if (po) {
      setForm(f => ({ ...f, po_id: poId, invoice_amount: String(po.total_amount), total_amount: String(po.total_amount) }));
    } else {
      setForm(f => ({ ...f, po_id: poId }));
    }
  };

  const getSupplierName = (id: number) => suppliers.find(s => s.id === id)?.company_name || `SUP#${id}`;
  const getPODisplay = (id: number) => pos.find(p => p.id === id)?.display_id || `PO#${id}`;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Invoices</h1>
          <p className="text-sm text-surface-500 mt-1">Invoice management with 3-way matching and payment monitoring</p>
        </div>
        <div className="flex gap-3">
          <button onClick={loadPaymentDue}
            className="px-4 py-2 text-sm font-medium text-amber-700 border border-amber-200 bg-amber-50 rounded-lg hover:bg-amber-100 transition-colors">
            Payment Due Monitor
          </button>
          <button onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
            + New Invoice
          </button>
        </div>
      </div>

      {/* Match result banner */}
      {matchResult && (
        <div className={`mb-4 p-4 rounded-xl border ${matchResult.match_result.status === 'MATCHED' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center justify-between">
            <div>
              <span className={`font-semibold text-sm ${matchResult.match_result.status === 'MATCHED' ? 'text-green-700' : 'text-red-700'}`}>
                3-Way Match: {matchResult.match_result.status}
              </span>
              {matchResult.match_result.exceptions?.length > 0 && (
                <ul className="mt-1 space-y-0.5">
                  {matchResult.match_result.exceptions.map((ex: string, i: number) => (
                    <li key={i} className="text-xs text-red-600">• {ex}</li>
                  ))}
                </ul>
              )}
            </div>
            <button onClick={() => setMatchResult(null)} className="opacity-60 hover:opacity-100 text-sm">✕</button>
          </div>
        </div>
      )}

      {/* Status tabs */}
      <div className="bg-white rounded-xl border border-surface-200 p-3 mb-4 flex gap-2 flex-wrap">
        {['', 'SUBMITTED', 'VALIDATED', 'DISCREPANCY', 'APPROVED', 'PAYMENT_PENDING', 'PAID', 'BLOCKED'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${
              statusFilter === s ? 'bg-primary-600 text-white' : 'text-surface-600 hover:bg-surface-100'
            }`}>
            {s || 'All'} {s === '' && `(${invoices.length})`}
          </button>
        ))}
      </div>

      {/* Invoice table */}
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
                  {['Invoice', 'PO', 'Supplier', 'Amount', 'Tax', 'Total', 'Invoice Date', 'Due Date', 'Status', 'Actions'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {invoices.map(inv => (
                  <tr key={inv.id} className={`hover:bg-surface-50 transition-colors ${inv.status === 'DISCREPANCY' ? 'bg-red-50/30' : ''}`}>
                    <td className="px-4 py-3 text-sm font-medium text-primary-600">{inv.display_id}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{getPODisplay(inv.po_id)}</td>
                    <td className="px-4 py-3 text-sm text-surface-700">{getSupplierName(inv.supplier_id)}</td>
                    <td className="px-4 py-3 text-sm text-surface-700">₹{inv.invoice_amount.toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">₹{inv.tax_amount.toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-surface-900">₹{inv.total_amount.toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">
                      {inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString('en-IN') : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-surface-600">
                      {inv.due_date ? new Date(inv.due_date).toLocaleDateString('en-IN') : '—'}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={inv.status} /></td>
                    <td className="px-4 py-3">
                      {['SUBMITTED', 'DISCREPANCY'].includes(inv.status) && (
                        <button onClick={() => handleThreeWayMatch(inv)} disabled={matching === inv.id}
                          className="px-2 py-1 text-xs font-medium text-purple-600 border border-purple-200 rounded hover:bg-purple-50 disabled:opacity-50 transition-colors whitespace-nowrap">
                          {matching === inv.id ? 'Matching...' : '3-Way Match'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {invoices.length === 0 && (
                  <tr>
                    <td colSpan={10} className="px-4 py-12 text-center text-surface-400 text-sm">No invoices found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Payment Due Monitor Modal */}
      <Modal isOpen={duePanelOpen} onClose={() => setDuePanelOpen(false)} title="Payment Due Monitor" size="lg">
        {paymentDue && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-red-700">{paymentDue.overdue_count}</div>
                <div className="text-xs text-red-500 mt-0.5">Overdue</div>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-amber-700">{paymentDue.due_today_count}</div>
                <div className="text-xs text-amber-500 mt-0.5">Due Today</div>
              </div>
            </div>
            {Object.entries(paymentDue.categories || {}).map(([cat, items]: [string, any]) =>
              (items as PaymentDue[]).length > 0 && (
                <div key={cat}>
                  <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${
                    cat === 'OVERDUE' ? 'text-red-600' : cat.includes('1_3') ? 'text-amber-600' : 'text-surface-500'
                  }`}>{cat.replace(/_/g, ' ')}</h4>
                  {(items as PaymentDue[]).map((item, i) => (
                    <div key={i} className={`p-3 rounded-lg border mb-2 text-sm ${DUE_COLORS[cat] || 'bg-surface-50 border-surface-200'}`}>
                      <div className="flex justify-between">
                        <span className="font-medium">{item.invoice_id}</span>
                        <span className="font-bold">₹{Number(item.amount).toLocaleString('en-IN')}</span>
                      </div>
                      <div className="flex justify-between text-xs mt-1 opacity-80">
                        <span>{item.supplier_name}</span>
                        <span>Due: {item.due_date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}
          </div>
        )}
      </Modal>

      {/* Create Invoice Modal */}
      <Modal isOpen={showCreate} onClose={() => { setShowCreate(false); setForm(EMPTY_INVOICE); setFormError(''); }}
        title="New Invoice" size="lg">
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <div className="bg-red-50 text-red-700 text-sm px-4 py-2 rounded-lg border border-red-200">{formError}</div>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Purchase Order *</label>
              <select required value={form.po_id} onChange={e => onPoChange(e.target.value)}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
                <option value="">— Select PO —</option>
                {pos.map(p => <option key={p.id} value={p.id}>{p.display_id} · ₹{p.total_amount.toLocaleString('en-IN')}</option>)}
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
              <label className="block text-xs font-semibold text-surface-600 mb-1">Invoice Amount *</label>
              <input required type="number" step="0.01" value={form.invoice_amount}
                onChange={e => { const amt = parseFloat(e.target.value)||0; const tax = parseFloat(form.tax_amount)||0; setForm(f=>({...f, invoice_amount:e.target.value, total_amount:String(amt+tax)})); }}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Tax Amount</label>
              <input type="number" step="0.01" value={form.tax_amount}
                onChange={e => { const tax = parseFloat(e.target.value)||0; const amt = parseFloat(form.invoice_amount)||0; setForm(f=>({...f, tax_amount:e.target.value, total_amount:String(amt+tax)})); }}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Total Amount *</label>
              <input required type="number" step="0.01" value={form.total_amount} onChange={e => setForm(f => ({ ...f, total_amount: e.target.value }))}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Invoice Date</label>
              <input type="date" value={form.invoice_date} onChange={e => setForm(f => ({ ...f, invoice_date: e.target.value }))}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-surface-600 mb-1">Due Date</label>
              <input type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))}
                className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Notes</label>
            <textarea rows={2} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:outline-none" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => { setShowCreate(false); setForm(EMPTY_INVOICE); setFormError(''); }}
              className="px-4 py-2 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors">Cancel</button>
            <button type="submit" disabled={submitting}
              className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {submitting ? 'Creating...' : 'Create Invoice'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
