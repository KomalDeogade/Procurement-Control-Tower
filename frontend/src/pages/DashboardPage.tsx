/**
 * Phase 3 Dashboard – "Good Morning" procurement intelligence hub.
 * Shows: AI daily brief, exceptions feed, activity timeline, NL assistant, KPIs.
 */

import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

// ─── Types ────────────────────────────────────────────────────────
interface KPIs {
  open_requirements: number;
  pending_quotes: number;
  pending_approvals: number;
  active_purchase_orders: number;
  stock_risk: number;
  invoices_due: number;
  overdue_invoices: number;
  payment_pending: number;
  supplier_risk: number;
}

interface DailyBrief {
  greeting: string;
  executive_summary: string;
  critical_items: string[];
  recommended_actions: string[];
  ai_provider: string;
  system_data: {
    pending_approvals: number;
    stock_risk_count: number;
    overdue_invoices_count: number;
    due_3_days_count: number;
    due_7_days_count: number;
    invoice_discrepancies: number;
    high_risk_supplier_count: number;
  };
}

interface Exception {
  category: string;
  type: string;
  title: string;
  detail: string;
  entity_type: string;
  entity_id: number;
  recommended_action: string;
}

interface ActivityItem {
  id: number;
  timestamp: string;
  actor: string;
  action: string;
  message: string;
  icon: string;
}

interface AssistantMessage {
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

// ─── Helper components ────────────────────────────────────────────

function KPICard({ title, value, icon, color = 'blue', onClick }: {
  title: string; value: number; icon: string; color?: string; onClick?: () => void;
}) {
  const colors: Record<string, string> = {
    blue:   'bg-blue-50 border-blue-200 text-blue-600',
    red:    'bg-red-50 border-red-200 text-red-600',
    amber:  'bg-amber-50 border-amber-200 text-amber-600',
    green:  'bg-green-50 border-green-200 text-green-600',
    purple: 'bg-purple-50 border-purple-200 text-purple-600',
  };
  return (
    <div
      onClick={onClick}
      className={`rounded-xl border p-4 shadow-sm ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''} bg-white`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className={`text-2xl font-bold ${colors[color]?.split(' ')[2] || 'text-gray-700'}`}>{value}</span>
      </div>
      <p className="text-xs text-gray-500 font-medium">{title}</p>
    </div>
  );
}

function ExcBadge({ cat }: { cat: string }) {
  const cls: Record<string, string> = {
    CRITICAL: 'bg-red-100 text-red-700 border-red-200',
    HIGH:     'bg-amber-100 text-amber-700 border-amber-200',
    WARNING:  'bg-yellow-100 text-yellow-700 border-yellow-200',
  };
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${cls[cat] || 'bg-gray-100 text-gray-600'}`}>
      {cat}
    </span>
  );
}

function timeAgo(ts: string) {
  const diff = Date.now() - new Date(ts).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ─── Main Dashboard ───────────────────────────────────────────────

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [brief, setBrief] = useState<DailyBrief | null>(null);
  const [exceptions, setExceptions] = useState<Exception[]>([]);
  const [excCount, setExcCount] = useState(0);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [briefLoading, setBriefLoading] = useState(false);
  const [filter, setFilter] = useState<'today' | '7d' | '30d'>('today');

  // NL Assistant
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [asstLoading, setAsstLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';

  useEffect(() => {
    fetchAll();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function fetchAll() {
    setLoading(true);
    try {
      const [kpisRes, excRes, actRes] = await Promise.all([
        api.get<KPIs>('/dashboard/kpis'),
        api.get<{ count: number; exceptions: Exception[] }>('/exceptions/'),
        api.get<{ count: number; activities: ActivityItem[] }>('/exceptions/activity?limit=20'),
      ]);
      setKpis(kpisRes.data);
      setExceptions(excRes.data.exceptions || []);
      setExcCount(excRes.data.count || 0);
      setActivities(actRes.data.activities || []);
    } catch {
      // silently degrade
    } finally {
      setLoading(false);
    }
  }

  async function generateBrief() {
    setBriefLoading(true);
    try {
      const res = await api.post<DailyBrief>('/ai/daily-brief');
      setBrief(res.data);
    } catch {
      // ignore
    } finally {
      setBriefLoading(false);
    }
  }

  async function askAssistant(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    const q = question.trim();
    setQuestion('');
    const ts = new Date().toISOString();
    setMessages(m => [...m, { role: 'user', text: q, timestamp: ts }]);
    setAsstLoading(true);
    try {
      const res = await api.post<{ answer: string }>('/ai/assistant', { question: q });
      setMessages(m => [...m, { role: 'assistant', text: res.data.answer, timestamp: new Date().toISOString() }]);
    } catch {
      setMessages(m => [...m, { role: 'assistant', text: 'Unable to retrieve data. Please try again.', timestamp: new Date().toISOString() }]);
    } finally {
      setAsstLoading(false);
    }
  }

  const QUICK_Qs = [
    "What are today's critical issues?",
    "Which invoices are due this week?",
    "Which materials have stockout risk?",
    "How many approvals are pending?",
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{greeting} 👋</h1>
          <p className="text-sm text-gray-500 mt-1">
            {new Date().toLocaleDateString('en-IN', { weekday:'long', year:'numeric', month:'long', day:'numeric' })}
            {' '}· {excCount > 0 ? <span className="text-red-600 font-semibold">{excCount} exception{excCount !== 1 ? 's' : ''} require attention</span> : <span className="text-green-600">No critical exceptions</span>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-gray-100 rounded-lg p-1 text-xs">
            {(['today','7d','30d'] as const).map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-md font-medium transition ${filter===f ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
                {f === 'today' ? 'Today' : f === '7d' ? '7 Days' : '30 Days'}
              </button>
            ))}
          </div>
          <button onClick={fetchAll} className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-sm">🔄</button>
        </div>
      </div>

      {/* ── KPI Grid ───────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <KPICard title="Open Requirements"    value={kpis?.open_requirements ?? 0}      icon="📋" color="blue"   />
        <KPICard title="Pending Approvals"    value={kpis?.pending_approvals ?? 0}      icon="✅" color="amber"  />
        <KPICard title="Stock Risk Items"     value={kpis?.stock_risk ?? 0}             icon="⚠️" color="red"    />
        <KPICard title="Overdue Invoices"     value={kpis?.overdue_invoices ?? 0}       icon="🚨" color="red"    />
        <KPICard title="Invoices Due (7d)"    value={kpis?.invoices_due ?? 0}           icon="🧾" color="amber"  />
        <KPICard title="Active POs"           value={kpis?.active_purchase_orders ?? 0} icon="🛒" color="blue"   />
        <KPICard title="Pending Quotes"       value={kpis?.pending_quotes ?? 0}         icon="📨" color="purple" />
        <KPICard title="Payments Pending"     value={kpis?.payment_pending ?? 0}        icon="💳" color="amber"  />
        <KPICard title="Supplier Risk"        value={kpis?.supplier_risk ?? 0}          icon="🏭" color="red"    />
        <div className="rounded-xl border border-dashed border-gray-200 p-4 flex items-center justify-center">
          <Link to="/exceptions" className="text-xs text-blue-600 hover:underline font-medium text-center">
            📋 View All<br/>Exceptions
          </Link>
        </div>
      </div>

      {/* ── Main 3-column layout ──────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left: AI Daily Brief + Exceptions */}
        <div className="lg:col-span-2 space-y-6">

          {/* AI Daily Brief */}
          <div className="bg-gradient-to-br from-indigo-900 to-blue-800 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🤖</span>
                <div>
                  <h2 className="font-semibold text-lg">AI Procurement Brief</h2>
                  <p className="text-blue-200 text-xs">Powered by deterministic data · AI-summarized</p>
                </div>
              </div>
              <button
                onClick={generateBrief}
                disabled={briefLoading}
                className="bg-white/10 hover:bg-white/20 text-white text-xs font-medium px-3 py-1.5 rounded-lg border border-white/20 transition disabled:opacity-50"
              >
                {briefLoading ? '⟳ Generating…' : '✨ Generate Brief'}
              </button>
            </div>

            {brief ? (
              <div className="space-y-3">
                <p className="text-blue-100 text-sm leading-relaxed">{brief.executive_summary}</p>

                {brief.recommended_actions.length > 0 && (
                  <div className="bg-white/10 rounded-lg p-3">
                    <p className="text-xs font-semibold text-blue-200 mb-2">RECOMMENDED ACTIONS</p>
                    <ol className="space-y-1">
                      {brief.recommended_actions.map((a, i) => (
                        <li key={i} className="text-sm flex gap-2">
                          <span className="font-bold text-blue-300">{i+1}.</span>
                          <span className="text-blue-100">{a}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-2 text-center mt-2">
                  <div className="bg-white/10 rounded-lg p-2">
                    <div className="text-xl font-bold">{brief.system_data.pending_approvals}</div>
                    <div className="text-xs text-blue-200">Approvals</div>
                  </div>
                  <div className="bg-white/10 rounded-lg p-2">
                    <div className="text-xl font-bold">{brief.system_data.stock_risk_count}</div>
                    <div className="text-xs text-blue-200">Stock Risks</div>
                  </div>
                  <div className="bg-white/10 rounded-lg p-2">
                    <div className="text-xl font-bold">{brief.system_data.overdue_invoices_count}</div>
                    <div className="text-xs text-blue-200">Overdue</div>
                  </div>
                </div>

                <p className="text-blue-300 text-xs">
                  {brief.ai_provider === 'mock' ? '⚡ Mock AI mode — set AI_PROVIDER in .env for live AI' : `✓ Generated by ${brief.ai_provider}`}
                </p>
              </div>
            ) : (
              <div className="text-center py-6 text-blue-200">
                <div className="text-4xl mb-2">☀️</div>
                <p className="text-sm">Click "Generate Brief" to get your AI procurement summary</p>
                <p className="text-xs text-blue-300 mt-1">Summarizes verified system data — never invents metrics</p>
              </div>
            )}
          </div>

          {/* Exceptions Feed */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                🚨 Live Exceptions
                {excCount > 0 && <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-0.5 rounded-full">{excCount}</span>}
              </h2>
              <Link to="/exceptions" className="text-xs text-blue-600 hover:underline">View All →</Link>
            </div>
            <div className="divide-y divide-gray-50 max-h-80 overflow-y-auto">
              {exceptions.length === 0 ? (
                <div className="text-center py-8 text-gray-400 text-sm">✅ No exceptions — all clear!</div>
              ) : (
                exceptions.slice(0, 6).map((exc, i) => (
                  <div key={i} className="p-4 hover:bg-gray-50 transition">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <ExcBadge cat={exc.category} />
                          <p className="text-sm font-medium text-gray-900 truncate">{exc.title}</p>
                        </div>
                        <p className="text-xs text-gray-500 truncate">{exc.detail}</p>
                        {exc.recommended_action && (
                          <p className="text-xs text-blue-600 mt-1">→ {exc.recommended_action}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Activity Timeline */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">⚡ Activity Feed</h2>
              <span className="text-xs text-gray-400">{activities.length} events</span>
            </div>
            <div className="divide-y divide-gray-50 max-h-72 overflow-y-auto">
              {activities.length === 0 ? (
                <div className="text-center py-8 text-gray-400 text-sm">No recent activity</div>
              ) : (
                activities.map((a, i) => (
                  <div key={i} className="flex items-start gap-3 px-4 py-3 hover:bg-gray-50 transition">
                    <span className="text-base mt-0.5 shrink-0">{a.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 leading-snug">{a.message}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{a.actor} · {timeAgo(a.timestamp)}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right: NL Assistant + Quick Stats */}
        <div className="space-y-6">

          {/* Quick Stats panel */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
            <h3 className="font-semibold text-gray-900 mb-3 text-sm">📊 Quick Actions</h3>
            <div className="space-y-2">
              <Link to="/approvals" className="flex items-center justify-between p-2.5 rounded-lg hover:bg-amber-50 border border-transparent hover:border-amber-200 transition group">
                <span className="text-sm text-gray-700 group-hover:text-amber-700">✅ Pending Approvals</span>
                <span className="bg-amber-100 text-amber-700 text-xs font-bold px-2 py-0.5 rounded-full">{kpis?.pending_approvals ?? 0}</span>
              </Link>
              <Link to="/invoices" className="flex items-center justify-between p-2.5 rounded-lg hover:bg-red-50 border border-transparent hover:border-red-200 transition group">
                <span className="text-sm text-gray-700 group-hover:text-red-700">🧾 Overdue Invoices</span>
                <span className="bg-red-100 text-red-700 text-xs font-bold px-2 py-0.5 rounded-full">{kpis?.overdue_invoices ?? 0}</span>
              </Link>
              <Link to="/inventory" className="flex items-center justify-between p-2.5 rounded-lg hover:bg-orange-50 border border-transparent hover:border-orange-200 transition group">
                <span className="text-sm text-gray-700 group-hover:text-orange-700">⚠️ Stock Risk Items</span>
                <span className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-0.5 rounded-full">{kpis?.stock_risk ?? 0}</span>
              </Link>
              <Link to="/payments" className="flex items-center justify-between p-2.5 rounded-lg hover:bg-blue-50 border border-transparent hover:border-blue-200 transition group">
                <span className="text-sm text-gray-700 group-hover:text-blue-700">💳 Payments Pending</span>
                <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded-full">{kpis?.payment_pending ?? 0}</span>
              </Link>
              <Link to="/demo" className="flex items-center justify-between p-2.5 rounded-lg hover:bg-purple-50 border border-transparent hover:border-purple-200 transition group">
                <span className="text-sm text-gray-700 group-hover:text-purple-700">🎯 Demo Mode</span>
                <span className="text-purple-600 text-xs">XLR-500 →</span>
              </Link>
              <Link to="/reports" className="flex items-center justify-between p-2.5 rounded-lg hover:bg-green-50 border border-transparent hover:border-green-200 transition group">
                <span className="text-sm text-gray-700 group-hover:text-green-700">📄 Export Reports</span>
                <span className="text-green-600 text-xs">CSV →</span>
              </Link>
            </div>
          </div>

          {/* NL Assistant */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col" style={{ height: '460px' }}>
            <div className="p-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-900 text-sm flex items-center gap-2">
                🤖 Procurement Assistant
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">Ask about requirements, suppliers, invoices, stock…</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {messages.length === 0 && (
                <div className="text-center py-4">
                  <div className="text-2xl mb-2">💬</div>
                  <p className="text-xs text-gray-400 mb-3">Ask a question about your procurement data</p>
                  <div className="space-y-1.5">
                    {QUICK_Qs.map((q, i) => (
                      <button key={i} onClick={() => { setQuestion(q); }}
                        className="w-full text-left text-xs bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-lg px-3 py-2 text-gray-600 hover:text-blue-700 transition">
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-sm'
                      : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                  }`}>
                    {m.text}
                  </div>
                </div>
              ))}
              {asstLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-xl rounded-bl-sm px-3 py-2">
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={askAssistant} className="p-3 border-t border-gray-100 flex gap-2">
              <input
                type="text"
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder="Ask about procurement data…"
                disabled={asstLoading}
                className="flex-1 text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:opacity-50"
              />
              <button type="submit" disabled={asstLoading || !question.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium px-3 py-2 rounded-lg transition disabled:opacity-50">
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
