/**
 * Quote Comparison Page – supplier scoring, comparison table, "Why this supplier?" 
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import Modal from '../components/ui/Modal';

interface Requirement { id: number; display_id: string | null; material_name: string; material_code: string; budget: number | null; quantity: number; unit: string; status: string; }

interface ScoreBreakdown {
  price: number; delivery: number; quality: number; historical: number;
  payment_terms: number; availability: number; risk: number; total: number;
}

interface ScoredSupplier {
  supplier_id: number;
  supplier_name: string;
  score: number;
  breakdown: ScoreBreakdown;
  reasons: string[];
  is_recommended: boolean;
  quote_display_id: string;
  explanation: string;
}

interface QuoteCompare {
  requirement_id: number;
  quote_count: number;
  scores: ScoredSupplier[];
}

interface Quote {
  id: number;
  display_id: string;
  requirement_id: number;
  supplier_id: number;
  unit_price: number;
  quantity: number;
  tax: number;
  freight: number;
  total_price: number;
  availability: string | null;
  lead_time_days: number | null;
  delivery_date: string | null;
  payment_terms: string | null;
  warranty: string | null;
  advantages: string | null;
  limitations: string | null;
  status: string;
  submitted_at: string;
}

export default function QuotesPage() {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [selectedReq, setSelectedReq] = useState<Requirement | null>(null);
  const [comparison, setComparison] = useState<QuoteCompare | null>(null);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
  const [compareLoading, setCompareLoading] = useState(false);
  const [explainTarget, setExplainTarget] = useState<ScoredSupplier | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [approvalComment, setApprovalComment] = useState('');
  const [approvalSubmitting, setApprovalSubmitting] = useState(false);
  const [approvalSuccess, setApprovalSuccess] = useState('');

  useEffect(() => {
    api.get<Requirement[]>('/requirements/')
      .then(all => {
        const withQuotes = all.data.filter(r =>
          ['QUOTES_RECEIVED', 'UNDER_REVIEW', 'APPROVAL_PENDING'].includes(r.status)
        );
        setRequirements(withQuotes);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const loadComparison = async (req: Requirement) => {
    setSelectedReq(req);
    setComparison(null);
    setCompareLoading(true);
    try {
      const [cmpRes, quotesRes] = await Promise.all([
        api.get<QuoteCompare>(`/quotes/compare/${req.id}`),
        api.get<Quote[]>(`/quotes/?requirement_id=${req.id}`),
      ]);
      setComparison(cmpRes.data);
      setQuotes(quotesRes.data);
    } catch { /* ignore */ }
    finally { setCompareLoading(false); }
  };

  const sendToApproval = async () => {
    if (!selectedReq) return;
    setApprovalSubmitting(true);
    try {
      // Create approval record for the requirement
      await api.post('/approvals/', {
        entity_type: 'requirement',
        entity_id: selectedReq.id,
        approver_id: 1, // admin approver
        approval_level: 1,
        comments: approvalComment || 'Send for manager approval',
      });
      setApprovalSuccess(`Requirement ${selectedReq.display_id} sent for manager approval.`);
      setShowApprovalModal(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create approval request');
    } finally { setApprovalSubmitting(false); }
  };

  const getQuoteForSupplier = (supplierId: number) =>
    quotes.find(q => q.supplier_id === supplierId);

  if (loading) return (
    <div className="flex justify-center py-16">
      <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-surface-900">Quote Comparison</h1>
        <p className="text-sm text-surface-500 mt-1">Compare supplier quotes with deterministic scoring</p>
      </div>

      {approvalSuccess && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 text-green-700 rounded-xl text-sm">
          {approvalSuccess}
          <button onClick={() => setApprovalSuccess('')} className="ml-3 text-green-500 hover:text-green-700">✕</button>
        </div>
      )}

      <div className="grid grid-cols-4 gap-6">
        {/* Requirement list */}
        <div className="col-span-1">
          <h2 className="text-sm font-semibold text-surface-600 mb-3">Requirements with Quotes</h2>
          {requirements.length === 0 ? (
            <div className="bg-white rounded-xl border border-surface-200 p-4 text-sm text-surface-400 text-center">
              No requirements with quotes yet
            </div>
          ) : (
            <div className="space-y-2">
              {requirements.map(req => (
                <button key={req.id} onClick={() => loadComparison(req)}
                  className={`w-full text-left p-3 rounded-xl border transition-all ${
                    selectedReq?.id === req.id
                      ? 'border-primary-300 bg-primary-50'
                      : 'border-surface-200 bg-white hover:border-primary-200'
                  }`}>
                  <div className="text-xs font-mono text-surface-400">{req.display_id}</div>
                  <div className="text-sm font-medium text-surface-800 mt-0.5">{req.material_name}</div>
                  <div className="text-xs text-surface-500 mt-1">{req.quantity} · {req.budget ? `₹${req.budget.toLocaleString('en-IN')}` : 'No budget'}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Comparison panel */}
        <div className="col-span-3">
          {!selectedReq && (
            <div className="bg-white rounded-xl border border-dashed border-surface-300 p-12 text-center">
              <p className="text-surface-400 text-sm">Select a requirement to compare supplier quotes</p>
            </div>
          )}

          {selectedReq && compareLoading && (
            <div className="flex justify-center py-16">
              <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
            </div>
          )}

          {selectedReq && !compareLoading && comparison && (
            <div>
              {/* Requirement summary */}
              <div className="bg-white rounded-xl border border-surface-200 p-4 mb-4 flex items-center justify-between">
                <div>
                  <span className="text-xs font-mono text-surface-400">{selectedReq.display_id}</span>
                  <h3 className="text-lg font-semibold text-surface-900">{selectedReq.material_name}</h3>
                  <p className="text-sm text-surface-500">{selectedReq.quantity} · Budget: {selectedReq.budget ? `₹${selectedReq.budget.toLocaleString('en-IN')}` : 'Not set'}</p>
                </div>
                <div className="flex gap-3">
                  <span className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full font-medium">{comparison.quote_count} Quotes</span>
                  <button onClick={() => setShowApprovalModal(true)}
                    className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
                    Send for Approval
                  </button>
                </div>
              </div>

              {/* Score comparison table */}
              <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden mb-4">
                <div className="px-4 py-3 bg-surface-50 border-b border-surface-200">
                  <h4 className="text-sm font-semibold text-surface-700">Supplier Score Comparison</h4>
                  <p className="text-xs text-surface-400 mt-0.5">Deterministic scoring — Price 30% · Delivery 20% · Quality 15% · Historical 15% · Payment 10% · Availability 5% · Risk 5%</p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-50 border-b border-surface-200">
                      <tr>
                        {['Supplier', 'Total Score', 'Price', 'Delivery', 'Quality', 'Historical', 'Payment', 'Avail.', 'Risk', 'Actions'].map(h => (
                          <th key={h} className="px-3 py-2 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100">
                      {comparison.scores.map((s) => {
                        const q = getQuoteForSupplier(s.supplier_id);
                        return (
                          <tr key={s.supplier_id} className={`hover:bg-surface-50 transition-colors ${s.is_recommended ? 'bg-green-50/50' : ''}`}>
                            <td className="px-3 py-3">
                              <div className="flex items-center gap-2">
                                {s.is_recommended && <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">BEST</span>}
                                <div>
                                  <div className="text-sm font-medium text-surface-900">{s.supplier_name}</div>
                                  {q && <div className="text-xs text-surface-400">₹{q.total_price.toLocaleString('en-IN')} total</div>}
                                </div>
                              </div>
                            </td>
                            <td className="px-3 py-3">
                              <div className={`text-lg font-bold ${s.is_recommended ? 'text-green-600' : 'text-surface-700'}`}>{s.score.toFixed(1)}</div>
                            </td>
                            {['price', 'delivery', 'quality', 'historical', 'payment_terms', 'availability', 'risk'].map(k => (
                              <td key={k} className="px-3 py-3 text-sm text-surface-700">
                                {(s.breakdown as any)[k].toFixed(1)}
                              </td>
                            ))}
                            <td className="px-3 py-3">
                              <button onClick={() => setExplainTarget(s)}
                                className="text-xs text-primary-600 border border-primary-200 px-2 py-1 rounded hover:bg-primary-50 transition-colors whitespace-nowrap">
                                Why?
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Detailed quote comparison */}
              <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
                <div className="px-4 py-3 bg-surface-50 border-b border-surface-200">
                  <h4 className="text-sm font-semibold text-surface-700">Quote Details</h4>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-50 border-b border-surface-200">
                      <tr>
                        {['Supplier', 'Unit Price', 'Qty', 'Tax', 'Freight', 'Total', 'Lead Time', 'Payment', 'Availability', 'Warranty'].map(h => (
                          <th key={h} className="px-3 py-2 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100">
                      {quotes.map(q => {
                        const scored = comparison.scores.find(s => s.supplier_id === q.supplier_id);
                        return (
                          <tr key={q.id} className={`hover:bg-surface-50 ${scored?.is_recommended ? 'bg-green-50/30' : ''}`}>
                            <td className="px-3 py-2 text-sm font-medium text-surface-800">{scored?.supplier_name || `SUP#${q.supplier_id}`}</td>
                            <td className="px-3 py-2 text-sm text-surface-700">₹{q.unit_price.toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2 text-sm text-surface-700">{q.quantity.toLocaleString()}</td>
                            <td className="px-3 py-2 text-sm text-surface-700">₹{q.tax.toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2 text-sm text-surface-700">₹{q.freight.toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2 text-sm font-semibold text-surface-900">₹{q.total_price.toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2 text-sm text-surface-700">{q.lead_time_days ? `${q.lead_time_days}d` : '—'}</td>
                            <td className="px-3 py-2 text-sm text-surface-700">{q.payment_terms || '—'}</td>
                            <td className="px-3 py-2 text-sm text-surface-700">{q.availability || '—'}</td>
                            <td className="px-3 py-2 text-sm text-surface-700">{q.warranty || '—'}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* "Why this supplier?" modal */}
      {explainTarget && (
        <Modal isOpen={!!explainTarget} onClose={() => setExplainTarget(null)} title={`Why ${explainTarget.supplier_name}?`} size="md">
          <div>
            {explainTarget.is_recommended && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 font-medium">
                Recommended Supplier — Highest Overall Score
              </div>
            )}
            <div className="mb-4">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-surface-600">Overall Score</span>
                <span className="text-2xl font-bold text-primary-600">{explainTarget.score.toFixed(1)} / 100</span>
              </div>
              <div className="w-full bg-surface-100 rounded-full h-3">
                <div className="bg-primary-500 h-3 rounded-full" style={{ width: `${explainTarget.score}%` }} />
              </div>
            </div>

            <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">Score Breakdown</h4>
            <div className="space-y-2 mb-4">
              {[
                { k: 'price', label: 'Price', max: 30 },
                { k: 'delivery', label: 'Delivery', max: 20 },
                { k: 'quality', label: 'Quality', max: 15 },
                { k: 'historical', label: 'Historical', max: 15 },
                { k: 'payment_terms', label: 'Payment Terms', max: 10 },
                { k: 'availability', label: 'Availability', max: 5 },
                { k: 'risk', label: 'Risk', max: 5 },
              ].map(({ k, label, max }) => {
                const val = (explainTarget.breakdown as any)[k];
                const pct = (val / max) * 100;
                return (
                  <div key={k}>
                    <div className="flex justify-between text-xs text-surface-600 mb-0.5">
                      <span>{label}</span>
                      <span className="font-medium">{val.toFixed(2)} / {max}</span>
                    </div>
                    <div className="w-full bg-surface-100 rounded-full h-1.5">
                      <div className="bg-primary-400 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>

            <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">Key Factors</h4>
            <ul className="space-y-1.5">
              {explainTarget.reasons.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-surface-700">
                  <span className="text-primary-400 mt-0.5">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        </Modal>
      )}

      {/* Send for Approval Modal */}
      <Modal isOpen={showApprovalModal} onClose={() => setShowApprovalModal(false)} title="Send for Manager Approval">
        <div className="space-y-4">
          {comparison && comparison.scores.length > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm font-medium text-green-800">Recommended Supplier</p>
              <p className="text-lg font-bold text-green-700 mt-0.5">
                {comparison.scores[0].supplier_name}
              </p>
              <p className="text-sm text-green-600">Score: {comparison.scores[0].score.toFixed(1)}/100</p>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-surface-600 mb-1">Comments (optional)</label>
            <textarea rows={3} value={approvalComment} onChange={e => setApprovalComment(e.target.value)}
              className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:outline-none"
              placeholder="Add context for the approver..." />
          </div>
          <div className="flex justify-end gap-3">
            <button onClick={() => setShowApprovalModal(false)}
              className="px-4 py-2 text-sm border border-surface-200 rounded-lg hover:bg-surface-50 transition-colors">Cancel</button>
            <button onClick={sendToApproval} disabled={approvalSubmitting}
              className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {approvalSubmitting ? 'Sending...' : 'Send for Approval'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
