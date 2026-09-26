/**
 * Reports Page – Automated report generation with CSV export.
 * Reports: Daily Summary, Inventory Risk, Payment Due, Supplier Comparison, Process Impact.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';

interface InventoryRisk {
  report_type: string;
  total_items: number;
  summary: Record<string, number>;
  items: Array<{
    material_code: string;
    material_name: string;
    risk_status: string;
    available_stock: number;
    stock_coverage_days: number;
    recommended_reorder_qty: number;
  }>;
}

interface PaymentDue {
  report_type: string;
  total_invoices: number;
  total_amount_due: number;
  overdue_amount: number;
  items: Array<{
    invoice_id: string;
    supplier: string;
    total_amount: number;
    due_date: string;
    days_until_due: number;
    category: string;
    status: string;
  }>;
}

interface DailySummary {
  report_type: string;
  summary: Record<string, unknown>;
  stock_risks: Array<{ material_code: string; material_name: string; risk: string }>;
  pending_approval_details: Array<{ id: string; entity_type: string }>;
  overdue_invoice_details: Array<{ id: string; amount: number }>;
}

interface ProcessImpact {
  workflow_counts: Record<string, number>;
  automation_metrics: {
    total_audit_events: number;
    human_actions: number;
    automated_system_actions: number;
    ai_assisted_actions: number;
    automation_rate_pct: number;
  };
  quality_metrics: Record<string, number>;
  note: string;
}

function riskColor(r: string) {
  return {
    STOCKOUT_RISK: 'text-red-700 bg-red-100 border-red-200',
    CRITICAL: 'text-amber-700 bg-amber-100 border-amber-200',
    LOW: 'text-yellow-700 bg-yellow-100 border-yellow-200',
    NORMAL: 'text-green-700 bg-green-100 border-green-200',
  }[r] || 'text-gray-600 bg-gray-100 border-gray-200';
}

function dueCatColor(c: string) {
  return {
    OVERDUE: 'text-red-700 bg-red-100',
    DUE_TODAY: 'text-orange-700 bg-orange-100',
    DUE_1_3_DAYS: 'text-amber-700 bg-amber-100',
    DUE_4_7_DAYS: 'text-yellow-700 bg-yellow-100',
    DUE_LATER: 'text-green-700 bg-green-100',
  }[c] || 'text-gray-600 bg-gray-100';
}

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<'inventory' | 'payment' | 'daily' | 'impact'>('inventory');
  const [invReport, setInvReport] = useState<InventoryRisk | null>(null);
  const [payReport, setPayReport] = useState<PaymentDue | null>(null);
  const [dailyReport, setDailyReport] = useState<DailySummary | null>(null);
  const [impactReport, setImpactReport] = useState<ProcessImpact | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState('');

  useEffect(() => { fetchReport(activeTab); }, [activeTab]);

  async function fetchReport(tab: string) {
    setLoading(true);
    try {
      if (tab === 'inventory') {
        const res = await api.get<InventoryRisk>('/reports/inventory-risk');
        setInvReport(res.data);
      } else if (tab === 'payment') {
        const res = await api.get<PaymentDue>('/reports/payment-due?days_ahead=30');
        setPayReport(res.data);
      } else if (tab === 'daily') {
        const res = await api.get<DailySummary>('/reports/daily-summary');
        setDailyReport(res.data);
      } else if (tab === 'impact') {
        const res = await api.get<ProcessImpact>('/reports/process-impact');
        setImpactReport(res.data);
      }
    } finally {
      setLoading(false);
    }
  }

  async function exportCSV(reportType: string) {
    setExporting(reportType);
    try {
      const res = await api.get(`/reports/export/${reportType}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data as BlobPart]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `scm_${reportType}_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert('Export failed');
    } finally {
      setExporting('');
    }
  }

  const tabs = [
    { id: 'inventory', label: '📦 Inventory Risk',      exportKey: 'inventory-risk' },
    { id: 'payment',   label: '💳 Payment Due',          exportKey: 'payment-due' },
    { id: 'daily',     label: '📋 Daily Summary',        exportKey: 'daily-summary' },
    { id: 'impact',    label: '📊 Process Impact',       exportKey: null },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📄 Reports</h1>
          <p className="text-sm text-gray-500 mt-1">Automated procurement reports · CSV export available</p>
        </div>
        <button onClick={() => fetchReport(activeTab)}
          className="bg-white border border-gray-200 hover:bg-gray-50 px-4 py-2 rounded-lg text-sm font-medium transition">
          🔄 Refresh
        </button>
      </div>

      {/* Notice */}
      <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-xs text-green-800">
        ✅ All reports are <strong>fully deterministic</strong> — AI is not required for report generation.
        AI may optionally add narrative summaries via the AI Features page.
      </div>

      {/* Tabs + Export Button */}
      <div className="flex items-center gap-3">
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1 flex-1">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id as typeof activeTab)}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition ${activeTab === t.id ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}`}>
              {t.label}
            </button>
          ))}
        </div>
        {tabs.find(t => t.id === activeTab)?.exportKey && (
          <button
            onClick={() => exportCSV(tabs.find(t => t.id === activeTab)!.exportKey!)}
            disabled={!!exporting}
            className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2.5 rounded-xl transition disabled:opacity-50 flex items-center gap-2 whitespace-nowrap">
            {exporting ? '⟳ Exporting…' : '⬇️ Export CSV'}
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
        </div>
      )}

      {/* ── Inventory Risk Report ────────────────────────────── */}
      {!loading && activeTab === 'inventory' && invReport && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(invReport.summary).map(([status, count]) => (
              <div key={status} className={`rounded-xl border p-4 ${riskColor(status)}`}>
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm font-medium mt-1">{status.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>

          {/* Items table */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-sm font-semibold text-gray-900">{invReport.total_items} Inventory Items</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">Material</th>
                    <th className="px-4 py-3 text-right">Available</th>
                    <th className="px-4 py-3 text-right">Coverage</th>
                    <th className="px-4 py-3 text-right">Reorder Qty</th>
                    <th className="px-4 py-3 text-center">Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {invReport.items.map((item, i) => (
                    <tr key={i} className="hover:bg-gray-50 transition">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{item.material_name}</p>
                        <p className="text-xs text-gray-400">{item.material_code}</p>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-gray-900">{item.available_stock.toLocaleString()}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{item.stock_coverage_days.toFixed(0)}d</td>
                      <td className="px-4 py-3 text-right font-mono text-gray-900">{item.recommended_reorder_qty > 0 ? item.recommended_reorder_qty.toLocaleString() : '—'}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${riskColor(item.risk_status)}`}>
                          {item.risk_status.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── Payment Due Report ───────────────────────────────── */}
      {!loading && activeTab === 'payment' && payReport && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Invoices', value: payReport.total_invoices },
              { label: 'Total Amount Due', value: `₹${(payReport.total_amount_due / 100000).toFixed(1)}L` },
              { label: 'Overdue Amount', value: `₹${(payReport.overdue_amount / 100000).toFixed(1)}L`, red: true },
              { label: 'Lookback', value: '30 days' },
            ].map(({ label, value, red }) => (
              <div key={label} className={`bg-white rounded-xl border p-4 ${red ? 'border-red-300' : 'border-gray-200'}`}>
                <p className={`text-2xl font-bold ${red ? 'text-red-600' : 'text-gray-900'}`}>{value}</p>
                <p className="text-sm text-gray-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">Invoice</th>
                    <th className="px-4 py-3 text-left">Supplier</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                    <th className="px-4 py-3 text-center">Due Date</th>
                    <th className="px-4 py-3 text-center">Days</th>
                    <th className="px-4 py-3 text-center">Category</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {payReport.items.map((item, i) => (
                    <tr key={i} className="hover:bg-gray-50 transition">
                      <td className="px-4 py-3 font-medium text-gray-900">{item.invoice_id}</td>
                      <td className="px-4 py-3 text-gray-600">{item.supplier}</td>
                      <td className="px-4 py-3 text-right font-mono text-gray-900">₹{item.total_amount.toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-center text-gray-600">{item.due_date}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={item.days_until_due < 0 ? 'text-red-600 font-bold' : item.days_until_due <= 3 ? 'text-amber-600 font-semibold' : 'text-gray-600'}>
                          {item.days_until_due < 0 ? `${Math.abs(item.days_until_due)}d overdue` : `${item.days_until_due}d`}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${dueCatColor(item.category)}`}>
                          {item.category.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {payReport.items.length === 0 && (
                    <tr><td colSpan={6} className="text-center py-8 text-gray-400">No invoices due in the next 30 days</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── Daily Summary Report ─────────────────────────────── */}
      {!loading && activeTab === 'daily' && dailyReport && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(dailyReport.summary).filter(([, v]) => typeof v === 'number').slice(0, 8).map(([k, v]) => (
              <div key={k} className="bg-white rounded-xl border border-gray-200 p-4">
                <p className="text-2xl font-bold text-gray-900">{String(v)}</p>
                <p className="text-xs text-gray-500 mt-0.5 capitalize">{k.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>

          {dailyReport.stock_risks.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="font-semibold text-amber-800 mb-2">⚠️ Stock Risks ({dailyReport.stock_risks.length})</p>
              <div className="space-y-1">
                {dailyReport.stock_risks.map((r, i) => (
                  <p key={i} className="text-sm text-amber-700">• {r.material_name} ({r.material_code}) — {r.risk}</p>
                ))}
              </div>
            </div>
          )}

          {dailyReport.overdue_invoice_details.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="font-semibold text-red-800 mb-2">🚨 Overdue Invoices ({dailyReport.overdue_invoice_details.length})</p>
              <div className="space-y-1">
                {dailyReport.overdue_invoice_details.map((inv, i) => (
                  <p key={i} className="text-sm text-red-700">• {inv.id} — ₹{inv.amount.toLocaleString('en-IN')}</p>
                ))}
              </div>
            </div>
          )}

          {dailyReport.pending_approval_details.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="font-semibold text-blue-800 mb-2">✅ Pending Approvals ({dailyReport.pending_approval_details.length})</p>
              <div className="space-y-1">
                {dailyReport.pending_approval_details.map((a, i) => (
                  <p key={i} className="text-sm text-blue-700">• {a.id} — {a.entity_type}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Process Impact Report ────────────────────────────── */}
      {!loading && activeTab === 'impact' && impactReport && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs text-blue-800">
            <strong>Note:</strong> {impactReport.note}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h3 className="font-semibold text-gray-900 mb-3 text-sm">🔄 Workflow Counts</h3>
              <div className="space-y-2">
                {Object.entries(impactReport.workflow_counts).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className="font-semibold text-gray-900">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h3 className="font-semibold text-gray-900 mb-3 text-sm">⚡ Automation Metrics</h3>
              <div className="space-y-2">
                {Object.entries(impactReport.automation_metrics).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className={`font-semibold ${k === 'automation_rate_pct' ? 'text-green-600' : 'text-gray-900'}`}>
                      {k === 'automation_rate_pct' ? `${v}%` : v}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h3 className="font-semibold text-gray-900 mb-3 text-sm">🏆 Quality Metrics</h3>
              <div className="space-y-2">
                {Object.entries(impactReport.quality_metrics).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className="font-semibold text-gray-900">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Automation gauge */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-semibold text-gray-900 mb-4 text-sm">Automation Rate</h3>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all"
                    style={{ width: `${impactReport.automation_metrics.automation_rate_pct}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>Human actions: {impactReport.automation_metrics.human_actions}</span>
                  <span>Automated: {impactReport.automation_metrics.automated_system_actions}</span>
                </div>
              </div>
              <div className="text-3xl font-bold text-green-600 shrink-0">
                {impactReport.automation_metrics.automation_rate_pct}%
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">Calculated from actual system events — not estimated</p>
          </div>
        </div>
      )}
    </div>
  );
}
