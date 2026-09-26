/**
 * Supplier Portal – public page for suppliers to submit quotes via RFQ link.
 * Route: /supplier/rfq/:rfqId
 */

import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';

interface RFQInfo {
  id: number;
  display_id: string | null;
  requirement_id: number;
  supplier_id: number;
  status: string;
  response_deadline: string | null;
  notes: string | null;
}

interface RequirementInfo {
  id: number;
  display_id: string | null;
  material_code: string;
  material_name: string;
  description: string | null;
  quantity: number;
  unit: string;
  required_by_date: string | null;
  budget: number | null;
}

const EMPTY_FORM = {
  company_name: '', contact_person: '', designation: '',
  email: '', phone: '', registration_number: '',
  unit_price: '', quantity: '', tax: '0', freight: '0', total_price: '',
  availability: 'In Stock', lead_time_days: '14', delivery_date: '',
  payment_terms: 'NET 30', warranty: '12 months', service_details: '',
  advantages: '', limitations: '',
};

export default function SupplierPortalPage() {
  const { rfqId } = useParams<{ rfqId: string }>();
  const [rfq, setRfq] = useState<RFQInfo | null>(null);
  const [requirement, setRequirement] = useState<RequirementInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    if (!rfqId) return;
    api.get<RFQInfo>(`/rfqs/public/${rfqId}`)
      .then(async res => {
        setRfq(res.data);
        setForm(f => ({ ...f, quantity: '' }));
        try {
          const reqRes = await api.get<RequirementInfo>(`/requirements/${res.data.requirement_id}`);
          setRequirement(reqRes.data);
          setForm(f => ({ ...f, quantity: String(reqRes.data.quantity) }));
        } catch { /* ignore */ }
      })
      .catch(() => setError('RFQ not found or has expired.'))
      .finally(() => setLoading(false));
  }, [rfqId]);

  const recalcTotal = (unit: string, qty: string, tax: string, freight: string) => {
    const u = parseFloat(unit) || 0;
    const q = parseFloat(qty) || 0;
    const t = parseFloat(tax) || 0;
    const f = parseFloat(freight) || 0;
    return String(u * q + t + f);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rfq) return;
    setSubmitError('');
    setSubmitting(true);
    try {
      await api.post('/quotes/supplier-portal', {
        requirement_id: rfq.requirement_id,
        supplier_id: rfq.supplier_id,
        unit_price: parseFloat(form.unit_price),
        quantity: parseFloat(form.quantity),
        tax: parseFloat(form.tax) || 0,
        freight: parseFloat(form.freight) || 0,
        total_price: parseFloat(form.total_price),
        availability: form.availability,
        lead_time_days: parseInt(form.lead_time_days),
        delivery_date: form.delivery_date ? new Date(form.delivery_date).toISOString() : null,
        payment_terms: form.payment_terms,
        warranty: form.warranty,
        service_details: form.service_details || null,
        advantages: form.advantages || null,
        limitations: form.limitations || null,
      });
      setSubmitted(true);
    } catch (err: any) {
      setSubmitError(err.response?.data?.detail || 'Failed to submit quote. Please try again.');
    } finally { setSubmitting(false); }
  };

  if (loading) return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center">
      <div className="bg-white border border-surface-200 rounded-2xl shadow-sm p-8 max-w-md text-center">
        <div className="text-4xl mb-4">🔗</div>
        <h2 className="text-xl font-bold text-surface-900 mb-2">RFQ Not Found</h2>
        <p className="text-surface-500">{error}</p>
      </div>
    </div>
  );

  if (submitted) return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center">
      <div className="bg-white border border-surface-200 rounded-2xl shadow-sm p-10 max-w-md text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-surface-900 mb-2">Quote Submitted!</h2>
        <p className="text-surface-500 text-sm">Your quotation has been received and will be reviewed by the procurement team.</p>
        <p className="text-surface-400 text-xs mt-4">RFQ: {rfq?.display_id}</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-surface-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-surface-900">Supplier Quotation Portal</h1>
              <p className="text-surface-500 text-sm mt-1">SCM Procurement Control Tower</p>
            </div>
            <div className="text-right">
              <div className="text-xs font-mono text-surface-400">{rfq?.display_id}</div>
              <div className="text-sm font-medium text-blue-600 mt-0.5">RFQ Active</div>
            </div>
          </div>

          {requirement && (
            <div className="mt-4 p-4 bg-primary-50 border border-primary-100 rounded-xl">
              <h3 className="text-sm font-semibold text-primary-900 mb-2">Requirement Details</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-primary-600">Material:</span> <strong className="text-primary-900">{requirement.material_name}</strong></div>
                <div><span className="text-primary-600">Code:</span> <span className="font-mono text-primary-800">{requirement.material_code}</span></div>
                <div><span className="text-primary-600">Quantity Required:</span> <strong className="text-primary-900">{requirement.quantity.toLocaleString()} {requirement.unit}</strong></div>
                <div><span className="text-primary-600">Required By:</span> <span className="text-primary-800">{requirement.required_by_date ? new Date(requirement.required_by_date).toLocaleDateString('en-IN') : '—'}</span></div>
              </div>
              {requirement.description && (
                <p className="text-sm text-primary-700 mt-2 pt-2 border-t border-primary-200">{requirement.description}</p>
              )}
            </div>
          )}

          {rfq?.response_deadline && (
            <div className="mt-3 text-xs text-amber-600">
              Response Deadline: <strong>{new Date(rfq.response_deadline).toLocaleDateString('en-IN')}</strong>
            </div>
          )}
        </div>

        {/* Quote Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
          {submitError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{submitError}</div>
          )}

          {/* Company Info */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-surface-700 mb-3 pb-2 border-b border-surface-100">Company Information</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                { key: 'company_name', label: 'Company Name', required: true },
                { key: 'contact_person', label: 'Contact Person', required: true },
                { key: 'designation', label: 'Designation', required: false },
                { key: 'email', label: 'Email', required: true, type: 'email' },
                { key: 'phone', label: 'Phone', required: false },
                { key: 'registration_number', label: 'Registration Number (CIN/GST)', required: false },
              ].map(field => (
                <div key={field.key}>
                  <label className="block text-xs font-semibold text-surface-600 mb-1">
                    {field.label}{field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type={(field as any).type || 'text'}
                    required={field.required}
                    value={(form as any)[field.key]}
                    onChange={e => setForm(f => ({ ...f, [field.key]: e.target.value }))}
                    className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Pricing */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-surface-700 mb-3 pb-2 border-b border-surface-100">Pricing & Delivery</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Unit Price (₹) *</label>
                <input required type="number" step="0.01" value={form.unit_price}
                  onChange={e => { const v = e.target.value; setForm(f => ({ ...f, unit_price: v, total_price: recalcTotal(v, f.quantity, f.tax, f.freight) })); }}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Quantity *</label>
                <input required type="number" step="0.01" value={form.quantity}
                  onChange={e => { const v = e.target.value; setForm(f => ({ ...f, quantity: v, total_price: recalcTotal(f.unit_price, v, f.tax, f.freight) })); }}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Tax (₹)</label>
                <input type="number" step="0.01" value={form.tax}
                  onChange={e => { const v = e.target.value; setForm(f => ({ ...f, tax: v, total_price: recalcTotal(f.unit_price, f.quantity, v, f.freight) })); }}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Freight (₹)</label>
                <input type="number" step="0.01" value={form.freight}
                  onChange={e => { const v = e.target.value; setForm(f => ({ ...f, freight: v, total_price: recalcTotal(f.unit_price, f.quantity, f.tax, v) })); }}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-surface-600 mb-1">Total Price (₹) *</label>
                <input required type="number" step="0.01" value={form.total_price}
                  onChange={e => setForm(f => ({ ...f, total_price: e.target.value }))}
                  className="w-full px-3 py-2 border-2 border-primary-200 rounded-lg text-sm font-semibold text-primary-700 focus:ring-2 focus:ring-primary-500 focus:outline-none bg-primary-50" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Availability</label>
                <select value={form.availability} onChange={e => setForm(f => ({ ...f, availability: e.target.value }))}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
                  <option>In Stock</option>
                  <option>Within 1 week</option>
                  <option>Within 2 weeks</option>
                  <option>Within 1 month</option>
                  <option>Made to Order</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Lead Time (days)</label>
                <input type="number" value={form.lead_time_days} onChange={e => setForm(f => ({ ...f, lead_time_days: e.target.value }))}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Delivery Date</label>
                <input type="date" value={form.delivery_date} onChange={e => setForm(f => ({ ...f, delivery_date: e.target.value }))}
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
                <label className="block text-xs font-semibold text-surface-600 mb-1">Warranty</label>
                <input value={form.warranty} onChange={e => setForm(f => ({ ...f, warranty: e.target.value }))}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none"
                  placeholder="e.g. 12 months" />
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="mb-6">
            <h3 className="text-sm font-bold text-surface-700 mb-3 pb-2 border-b border-surface-100">Additional Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Service & Support Details</label>
                <textarea rows={2} value={form.service_details} onChange={e => setForm(f => ({ ...f, service_details: e.target.value }))}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:outline-none"
                  placeholder="Describe after-sales service, technical support..." />
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Advantages of Our Offer</label>
                <textarea rows={2} value={form.advantages} onChange={e => setForm(f => ({ ...f, advantages: e.target.value }))}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:outline-none"
                  placeholder="Key differentiators, quality certifications..." />
              </div>
              <div>
                <label className="block text-xs font-semibold text-surface-600 mb-1">Limitations / Exceptions</label>
                <textarea rows={2} value={form.limitations} onChange={e => setForm(f => ({ ...f, limitations: e.target.value }))}
                  className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:outline-none"
                  placeholder="Any conditions, exclusions..." />
              </div>
            </div>
          </div>

          <button type="submit" disabled={submitting}
            className="w-full py-3 bg-primary-600 text-white font-semibold rounded-xl hover:bg-primary-700 disabled:opacity-50 transition-colors">
            {submitting ? 'Submitting...' : 'Submit Quotation'}
          </button>
          <p className="text-xs text-surface-400 text-center mt-2">
            By submitting, your quotation will be immediately available to the procurement team.
          </p>
        </form>
      </div>
    </div>
  );
}
