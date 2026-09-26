/**
 * Demo Mode Page – One-click XLR-500 scenario loader with step-by-step walkthrough.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface DemoStatus {
  loaded: boolean;
  requirement?: { id: string; status: string };
  quotes?: number;
  purchase_orders?: number;
  invoices?: number;
  exceptions_active?: boolean;
}

interface DemoStep {
  step: number;
  name: string;
  status: string;
  detail: string;
}

interface DemoResult {
  status: string;
  message: string;
  scenario: {
    requirement: string;
    material: string;
    quantity: string;
    budget: string;
    suppliers: string[];
  };
  exceptions_demonstrated: string[];
  steps: DemoStep[];
  next_steps: string[];
}

export default function DemoPage() {
  const [demoStatus, setDemoStatus] = useState<DemoStatus | null>(null);
  const [demoResult, setDemoResult] = useState<DemoResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => { checkStatus(); }, []);

  async function checkStatus() {
    setChecking(true);
    try {
      const res = await api.get<DemoStatus>('/demo/status');
      setDemoStatus(res.data);
    } finally {
      setChecking(false);
    }
  }

  async function loadDemo() {
    setLoading(true);
    try {
      const res = await api.post<DemoResult>('/demo/reset');
      setDemoResult(res.data);
      await checkStatus();
    } catch {
      alert('Demo reset failed. Please check the backend logs.');
    } finally {
      setLoading(false);
    }
  }

  const stepIcon = (status: string) => ({
    CREATED: '✅',
    OK: '✅',
    EXISTING: '♻️',
    SKIPPED: '⏭️',
  }[status] || '⏳');

  const demoWorkflow = [
    { step: 1, label: 'Requirement Created', link: '/requirements', desc: 'REQ-DEMO: Industrial Lubricant XLR-500, 5000L, ₹80L budget', icon: '📋' },
    { step: 2, label: 'RFQs Sent', link: '/rfqs', desc: '3 RFQs sent to Vendor A, B, and C', icon: '📨' },
    { step: 3, label: 'Quotes Received', link: '/quotes', desc: 'A: ₹1,680/L (14d), B: ₹1,520/L (45d ⚠️), C: ₹1,950/L (ADVANCE)', icon: '💰' },
    { step: 4, label: 'Supplier Scoring', link: '/quotes', desc: 'Deterministic scoring — Vendor A ranked #1 despite higher price', icon: '📊' },
    { step: 5, label: 'Approval Required', link: '/approvals', desc: 'Manager must approve Vendor A selection', icon: '✅' },
    { step: 6, label: 'Purchase Order', link: '/purchase-orders', desc: 'PO-DEMO-1 created for Vendor A, SAP sync done', icon: '🛒' },
    { step: 7, label: 'Invoice Exception', link: '/invoices', desc: '⚠️ INV-DEMO-1: 4800L vs PO 5000L — 3-Way Match FAILED', icon: '🚨' },
    { step: 8, label: 'Payment Alert', link: '/payments', desc: '⚠️ Invoice due in 4 days — Payment Watchdog active', icon: '💳' },
  ];

  const exceptions = [
    { label: 'Vendor B Delay', desc: 'Lower price (₹1,520/L) but 45-day delivery exceeds 30-day requirement window', severity: 'HIGH', icon: '⏰' },
    { label: 'Vendor C Advance Payment', desc: 'Requires advance payment before delivery — approval gate created', severity: 'WARNING', icon: '💰' },
    { label: 'Invoice Quantity Mismatch', desc: 'INV-DEMO-1 invoiced 4,800L but PO was for 5,000L — 3-Way Match FAILED', severity: 'CRITICAL', icon: '⚖️' },
    { label: 'Payment Due Soon', desc: 'INV-DEMO-1 due in 4 days — Payment Watchdog flagged DUE_4_7_DAYS', severity: 'HIGH', icon: '🚨' },
  ];

  if (checking) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🎯 Demo Mode</h1>
          <p className="text-sm text-gray-500 mt-1">
            One-click scenario: Industrial Lubricant XLR-500 — complete end-to-end procurement workflow
          </p>
        </div>
        <div className="flex items-center gap-2">
          {demoStatus?.loaded && (
            <span className="flex items-center gap-1.5 bg-green-100 text-green-700 text-xs font-semibold px-3 py-1.5 rounded-full border border-green-200">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Demo Active
            </span>
          )}
          <button onClick={checkStatus} className="bg-white border border-gray-200 hover:bg-gray-50 px-3 py-2 rounded-lg text-sm transition">🔄</button>
        </div>
      </div>

      {/* Scenario Card */}
      <div className="bg-gradient-to-br from-purple-900 to-indigo-800 rounded-2xl p-6 text-white shadow-xl">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="text-xs text-purple-300 font-semibold uppercase tracking-wider mb-1">Demo Scenario</div>
            <h2 className="text-xl font-bold">Industrial Lubricant XLR-500</h2>
            <p className="text-purple-200 text-sm mt-1">Full end-to-end procurement lifecycle with intentional exception scenarios</p>
          </div>
          <span className="text-4xl">🧴</span>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-5">
          <div className="bg-white/10 rounded-xl p-3">
            <p className="text-xs text-purple-300">Requirement</p>
            <p className="font-bold text-lg">REQ-DEMO</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3">
            <p className="text-xs text-purple-300">Quantity</p>
            <p className="font-bold text-lg">5,000 L</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3">
            <p className="text-xs text-purple-300">Budget</p>
            <p className="font-bold text-lg">₹80 Lakhs</p>
          </div>
        </div>

        <div className="mb-5">
          <p className="text-xs text-purple-300 mb-2 font-semibold">THREE SUPPLIERS</p>
          <div className="grid grid-cols-3 gap-2">
            {[
              { name: 'Vendor A', price: '₹1,680/L', delivery: '14 days', tag: '⭐ Recommended', tagClass: 'bg-green-500' },
              { name: 'Vendor B', price: '₹1,520/L', delivery: '45 days', tag: '⚠️ Delayed', tagClass: 'bg-amber-500' },
              { name: 'Vendor C', price: '₹1,950/L', delivery: '21 days', tag: '💰 Advance Req.', tagClass: 'bg-red-500' },
            ].map(({ name, price, delivery, tag, tagClass }) => (
              <div key={name} className="bg-white/10 rounded-xl p-3">
                <p className="font-semibold text-sm">{name}</p>
                <p className="text-xs text-purple-200">{price} · {delivery}</p>
                <span className={`text-xs font-bold mt-1.5 inline-block px-2 py-0.5 rounded-full text-white ${tagClass}`}>{tag}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={loadDemo}
            disabled={loading}
            className="bg-white text-purple-900 hover:bg-purple-50 font-semibold px-6 py-2.5 rounded-xl transition disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? '⟳ Loading demo…' : demoStatus?.loaded ? '🔄 Reload Demo' : '🚀 Load Demo Scenario'}
          </button>
          {demoStatus?.loaded && (
            <Link to="/exceptions" className="bg-white/10 hover:bg-white/20 text-white font-medium px-4 py-2.5 rounded-xl transition text-sm">
              🚨 View Exceptions →
            </Link>
          )}
        </div>
      </div>

      {/* Demo Status Bar */}
      {demoStatus?.loaded && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Demo Scenario Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { label: 'Requirement', value: demoStatus.requirement?.id || 'REQ-DEMO', status: demoStatus.requirement?.status },
              { label: 'Quotes', value: `${demoStatus.quotes} received`, status: 'OK' },
              { label: 'Purchase Orders', value: `${demoStatus.purchase_orders} active`, status: 'OK' },
              { label: 'Invoices', value: `${demoStatus.invoices} created`, status: 'OK' },
              { label: 'Exceptions', value: demoStatus.exceptions_active ? 'Active 🚨' : 'None ✅', status: demoStatus.exceptions_active ? 'EXCEPTION' : 'OK' },
            ].map(({ label, value, status }) => (
              <div key={label} className={`rounded-lg p-3 border ${status === 'EXCEPTION' ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-100'}`}>
                <p className="text-xs text-gray-500">{label}</p>
                <p className={`text-sm font-semibold mt-0.5 ${status === 'EXCEPTION' ? 'text-red-700' : 'text-gray-900'}`}>{value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step-by-step result */}
      {demoResult && (
        <div className="bg-white rounded-xl border border-green-300 shadow-sm p-6">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            ✅ Demo Loaded — Setup Steps
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-4">
            {demoResult.steps.map((step) => (
              <div key={step.step} className="flex items-start gap-3 bg-gray-50 rounded-lg px-3 py-2">
                <span className="text-base shrink-0 mt-0.5">{stepIcon(step.status)}</span>
                <div>
                  <p className="text-sm font-medium text-gray-800">Step {step.step}: {step.name}</p>
                  <p className="text-xs text-gray-500">{step.detail}</p>
                </div>
                <span className={`text-xs ml-auto px-1.5 py-0.5 rounded font-mono shrink-0 ${step.status === 'CREATED' ? 'bg-green-100 text-green-700' : step.status === 'EXISTING' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>{step.status}</span>
              </div>
            ))}
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-blue-800 mb-2">Next Steps</p>
            <ol className="space-y-1">
              {demoResult.next_steps.map((s, i) => (
                <li key={i} className="text-xs text-blue-700">{s}</li>
              ))}
            </ol>
          </div>
        </div>
      )}

      {/* Workflow walkthrough */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-4">📋 Demo Workflow Walkthrough</h3>
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />
          <div className="space-y-4">
            {demoWorkflow.map(({ step, label, link, desc, icon }) => (
              <div key={step} className="flex items-start gap-4 pl-2">
                <div className="w-8 h-8 rounded-full bg-purple-100 border-2 border-purple-300 flex items-center justify-center shrink-0 z-10 text-sm">
                  {icon}
                </div>
                <div className="flex-1 pb-2">
                  <div className="flex items-center gap-3">
                    <p className="font-medium text-sm text-gray-900">
                      Step {step}: {label}
                    </p>
                    <Link to={link} className="text-xs text-blue-600 hover:underline">Go →</Link>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Exception scenarios */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-1">🎭 Intentional Exception Scenarios</h3>
        <p className="text-xs text-gray-500 mb-4">These demonstrate that the system handles real-world exceptions — not just happy-path transactions.</p>
        <div className="space-y-3">
          {exceptions.map(({ label, desc, severity, icon }) => (
            <div key={label} className={`flex items-start gap-3 rounded-xl border p-4 ${
              severity === 'CRITICAL' ? 'bg-red-50 border-red-200' :
              severity === 'HIGH' ? 'bg-amber-50 border-amber-200' :
              'bg-yellow-50 border-yellow-200'
            }`}>
              <span className="text-2xl shrink-0">{icon}</span>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-semibold text-sm text-gray-900">{label}</p>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    severity === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                    severity === 'HIGH' ? 'bg-amber-100 text-amber-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>{severity}</span>
                </div>
                <p className="text-xs text-gray-600">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
