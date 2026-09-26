/**
 * Payments Page – finance approval, mock payment processing, payment detail.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';

interface Payment {
  id: number;
  display_id: string | null;
  invoice_id: number;
  amount: number;
  payment_date: string | null;
  payment_method: string;
  status: string;
  reference_number: string | null;
  created_at: string;
}

interface PaymentResult {
  payment_id: string;
  amount: number;
  supplier_name: string;
  status: string;
  transaction_reference: string;
  processed_at: string;
  disclaimer: string;
}

interface FinanceDetail {
  payment: Payment;
  invoice: { display_id: string; amount: number; status: string; due_date: string };
  purchase_order: { display_id: string; total: number; payment_terms: string };
  supplier: { name: string };
  grn_total_received: number;
  three_way_match: { status: string; exceptions: string[] };
}

const EMPTY_PAYMENT = { invoice_id: '', amount: '', payment_method: 'BANK_TRANSFER' };

export default function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState(EMPTY_PAYMENT);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [processing, setProcessing] = useState<number | null>(null);
  const [paymentResult, setPaymentResult] = useState<PaymentResult | null>(null);
  const [financeDetail, setFinanceDetail] = useState<FinanceDetail | null>(null);

  const fetchAll = async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const [payRes, invRes] = await Promise.all([
        api.get<Payment[]>(`/payments/${params}`),
        api.get<any[]>('/invoices/?status=VALIDATED'),
      ]);
      setPayments(payRes.data);
      setInvoices(invRes.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, [statusFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      await api.post('/payments/', {
        invoice_id: parseInt(form.invoice_id),
        amount: parseFloat(form.amount),
        payment_method: form.payment_method,
      });
      setShowCreate(false);
      setForm(EMPTY_PAYMENT);
      await fetchAll();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create payment');
    } finally { setSubmitting(false); }
  };

  const handleProcess = async (payment: Payment) => {
    setProcessing(payment.id);
    setPaymentResult(null);
    try {
      const res = await api.post<PaymentResult>(`/payments/${payment.id}/process`);
      setPaymentResult(res.data);
      await fetchAll();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Payment processing failed');
    } finally { setProcessing(null); }
  };

  const openFinanceDetail = async (payment: Payment) => {
    try {
      const res = await api.get<FinanceDetail>(`/payments/${payment.id}/finance-detail`);
      setFinanceDetail(res.data);
    } catch { /* ignore */ }
  };

  const onInvoiceChange = (invId: string) => {
    const inv = invoices.find(i => i.id === parseInt(invId));
    setForm(f => ({ ...f, invoice_id: invId, amount: inv ? String(inv.total_amount) : '' }));
  };

  const totalPaid = payments.filter(p => p.status === 'COMPLETED').reduce((s, p) => s + p.amount, 0);
  const totalPending = payments.filter(p => p.status === 'PENDING').reduce((s, p) => s + p.amount, 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Payments</h1>
          <p className="text-sm text-surface-500 mt-1">Finance approval and mock payment processing</p>
        </div>
        <button onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
          + Create Payment
        </button>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white border border-surface-200 rounded-xl p-4">
          <p className="text-sm text-surface-500">Total Paid</p>
          <p className="text-2xl font-bold text-green-600 mt-1">₹{totalPaid.toLocaleString('en-IN')}</p>
          <p className="text-xs text-surface-400 mt-0.5">{payments.filter(p => p.status === 'COMPLETED').length} transactions</p>
        </div>
        <div className="bg-white border border-surface-200 rounded-xl p-4">
          <p className="text-sm text-surface-500">Pending Amount</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">₹{totalPending.toLocaleString('en-IN')}</p>
          <p className="text-xs text-surface-400 mt-0.5">{payments.filter(p => p.status === 'PENDING').length} pending</p>
        </div>
        <div className="bg-white border border-surface-200 rounded-xl p-4">
          <p className="text-sm text-surface-500">Failed Payments</p>
          <p className="text-2xl font-bold text-red-600 mt-1">{payments.filter(p => p.status === 'FAILED').length}</p>
          <p className="text-xs text-surface-400 mt-0.5">Require attention</p>
        </div>
      </div>

      {/* Mock Payment result banner */}
      {paymentResult && (
        <div className={`mb-4 p-4 rounded-xl border ${paymentResult.status === 'SUCCESS' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-start justify-between">
            <div>
              <div className={`text-sm font-bold ${paymentResult.status === 'SUCCESS' ? 'text-green-700' : 'text-red-700'}`}>
                Mock Payment {paymentResult.status}
              </div>
              <div className="text-xs text-surface-500 mt-1 space-y-0.5">
                <div>Payment ID: <span className="font-mono">{paymentResult.payment_id}</span></div>
                <div>Amount: <span className="font-semibold">₹{Number(paymentResult.amount).toLocaleString('en-IN')}</span></div>
                <div>Ref: <span className="font-mono">{paymentResult.transaction_reference}</span></div>
                <div className="text-amber-600 font-medium mt-1">⚠ {paymentResult.disclaimer}</div>
              </div>
            </div>
            <button onClick={() => setPaymentResult(null)} className="text-surface-400 hover:text-surface-600">✕</button>
          </div>
        </div>
      )}

      {/* Status tabs */}
      <div className="bg-white rounded-xl border border-surface-200 p-3 mb-4 flex gap-2">
        {['', 'PENDING', 'COMPLETED', 'FAILED'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${
              statusFilter === s ? 'bg-primary-600 text-white' : 'text-surface-600 hover:bg-surface-100'
            }`}>
            {s || 'All'} {s === '' && `(${payments.length})`}
          </button>
        ))}
      </div>

      {/* Payments table */}
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
                  {['Payment ID', 'Invoice', 'Amount', 'Method', 'Payment Date', 'Reference', 'Status', 'Actions'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {payments.map(pay => (
                  <tr key={pay.id} className="hover:bg-surface-50 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-primary-600">{pay.display_id}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">INV #{pay.invoice_id}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-surface-900">₹{pay.amount.toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{pay.payment_method.replace('_', ' ')}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">
                      {pay.payment_date ? new Date(pay.payment_date).toLocaleDateString('en-IN') : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-surface-600">{pay.reference_number || '—'}</td>
                    <td className="px-4 py-3"><StatusBadge status={pay.status} /></td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button onClick={() => openFinanceDetail(pay)}
                          className="px-2 py-1 text-xs font-medium text-surface-600 border border-surface-200 rounded hover:bg-surface-50 transition-colors">
                          Detail
                        </button>
                        {pay.status === 'PENDING' && (
                          <button onClick={() => handleProcess(pay)} disabled={processing === pay.id}
                            className="px-2 py-1 text-xs font-medium text-green-700 border border-green-200 rounded hover:bg-green-50 disabled:opacity-50 transition-colors whitespace-nowrap">
                            {processing === pay.id ? 'Processing...' : 'Process'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {payments.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-surface-400 text-sm">No payments found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Finance Detail Modal */}
      {financeDetail && (
        <Modal isOpen={!!financeDetail} onClose={() => setFinanceDetail(null)} title="Finance Payment Detail" size="lg">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {/* Invoice info */}
              <div className="bg-surface-50 rounded-xl p-4">
                <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Invoice</h4>
                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between"><span className="text-surface-500">ID</span><span className="font-medium">{financeDetail.invoice?.display_id}</span></div>
                  <div className="flex justify-between"><span className="text-surface-500">Amount</span><span className="font-semibold text-surface-900">₹{Number(financeDetail.invoice?.amount).toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between"><span className="text-surface-500">Status</span><StatusBadge status={financeDetail.invoice?.status || ''} /></div>
                  <div className="flex justify-between"><span className="text-surface-500">Due Date</span><span>{financeDetail.invoice?.due_date || '—'}</span></div>
                </div>
              </div>

              {/* PO info */}
              <div className="bg-surface-50 rounded-xl p-4">
                <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Purchase Order</h4>
                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between"><span className="text-surface-500">PO Number</span><span className="font-medium">{financeDetail.purchase_order?.display_id}</span></div>
                  <div className="flex justify-between"><span className="text-surface-500">PO Total</span><span className="font-semibold">₹{Number(financeDetail.purchase_order?.total).toLocaleString('en-IN')}</span></div>
                  <div className="flex justify-between"><span className="text-surface-500">Payment Terms</span><span>{financeDetail.purchase_order?.payment_terms}</span></div>
                  <div className="flex justify-between"><span className="text-surface-500">Supplier</span><span>{financeDetail.supplier?.name}</span></div>
                </div>
              </div>
            </div>

            {/* GRN info */}
            <div className="bg-surface-50 rounded-xl p-4">
              <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">Goods Receipt</h4>
              <p className="text-sm text-surface-700">Total Received: <span className="font-semibold">{financeDetail.grn_total_received?.toLocaleString()}</span> units</p>
            </div>

            {/* 3-Way Match */}
            <div className={`rounded-xl p-4 border ${financeDetail.three_way_match?.status === 'MATCHED' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${financeDetail.three_way_match?.status === 'MATCHED' ? 'text-green-600' : 'text-red-600'}`}>
                3-Way Match: {financeDetail.three_way_match?.status}
              </h4>
              {financeDetail.three_way_match?.exceptions?.length > 0 && (
                <ul className="space-y-1">
                  {financeDetail.three_way_match.exceptions.map((ex: string, i: number) => (
                    <li key={i} className="text-xs text-red-600">• {ex}</li>
                  ))}
                </ul>
              )}
              {financeDetail.three_way_match?.status === 'MATCHED' && (
                <p className="text-sm text-green-700">All quantities and amounts verified. Payment can proceed.</p>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Create Payment Modal */}
      <Modal isOpen={showCreate} onClose={() => { setShowCreate(false); setForm(EMPTY_PAYMENT); setFormError(''); }}
        title="Create Payment">
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <div className="bg-red-50 text-red-700 text-sm px-4 py-2 rounded-lg border border-red-200">{formError}</div>}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700">
            <strong>Simulation Only:</strong> This creates a mock payment record. No real bank transaction will occur.
          </div>
          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Invoice (Validated) *</label>
            <select required value={form.invoice_id} onChange={e => onInvoiceChange(e.target.value)}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
              <option value="">— Select validated invoice —</option>
              {invoices.map(inv => <option key={inv.id} value={inv.id}>{inv.display_id} · ₹{inv.total_amount.toLocaleString('en-IN')}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Amount *</label>
            <input required type="number" step="0.01" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Payment Method</label>
            <select value={form.payment_method} onChange={e => setForm(f => ({ ...f, payment_method: e.target.value }))}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
              {['BANK_TRANSFER', 'CHEQUE', 'NEFT', 'RTGS', 'DD'].map(m => <option key={m} value={m}>{m.replace('_', ' ')}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => { setShowCreate(false); setForm(EMPTY_PAYMENT); setFormError(''); }}
              className="px-4 py-2 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors">Cancel</button>
            <button type="submit" disabled={submitting}
              className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {submitting ? 'Creating...' : 'Create Payment'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
