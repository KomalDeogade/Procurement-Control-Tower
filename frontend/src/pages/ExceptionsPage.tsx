/**
 * Exceptions Monitor Page – Exception-first automation dashboard.
 * Shows: current exceptions, payment watchdog, advance payment alerts, activity feed.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';

interface Exception {
  category: string;
  type: string;
  title: string;
  detail: string;
  entity_type: string;
  entity_id: number;
  recommended_action: string;
  timestamp: string;
}

interface ExceptionsData {
  count: number;
  critical: number;
  high: number;
  warning: number;
  exceptions: Exception[];
}

interface WatchdogItem {
  invoice_id: string;
  supplier_name: string;
  amount: number;
  due_date: string;
  days_until_due: number;
  category: string;
}

interface WatchdogData {
  total_monitored: number;
  total_exposure: number;
  overdue_count: number;
  overdue_amount: number;
  due_today_count: number;
  categories: Record<string, WatchdogItem[]>;
}

interface ActivityItem {
  id: number;
  timestamp: string;
  actor: string;
  message: string;
  icon: string;
  action: string;
}

function catColor(cat: string) {
  return {
    CRITICAL: 'bg-red-50 border-red-300 text-red-700',
    HIGH:     'bg-amber-50 border-amber-300 text-amber-700',
    WARNING:  'bg-yellow-50 border-yellow-300 text-yellow-700',
    NORMAL:   'bg-green-50 border-green-300 text-green-700',
  }[cat] || 'bg-gray-50 border-gray-200 text-gray-700';
}

function catDot(cat: string) {
  return {
    CRITICAL: 'bg-red-500',
    HIGH:     'bg-amber-500',
    WARNING:  'bg-yellow-500',
    NORMAL:   'bg-green-500',
  }[cat] || 'bg-gray-400';
}

function watchdogColor(cat: string) {
  return {
    OVERDUE:       'text-red-700 bg-red-100',
    DUE_TODAY:     'text-orange-700 bg-orange-100',
    DUE_1_3_DAYS:  'text-amber-700 bg-amber-100',
    DUE_4_7_DAYS:  'text-yellow-700 bg-yellow-100',
    DUE_LATER:     'text-green-700 bg-green-100',
  }[cat] || 'text-gray-600 bg-gray-100';
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

export default function ExceptionsPage() {
  const [excData, setExcData] = useState<ExceptionsData | null>(null);
  const [watchdog, setWatchdog] = useState<WatchdogData | null>(null);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'exceptions' | 'watchdog' | 'activity'>('exceptions');
  const [filterCat, setFilterCat] = useState<string>('ALL');

  useEffect(() => { fetchAll(); }, []);

  async function fetchAll() {
    setLoading(true);
    try {
      const [excRes, wdRes, actRes] = await Promise.all([
        api.get<ExceptionsData>('/exceptions/'),
        api.get<WatchdogData>('/exceptions/watchdog'),
        api.get<{ activities: ActivityItem[] }>('/exceptions/activity?limit=50'),
      ]);
      setExcData(excRes.data);
      setWatchdog(wdRes.data);
      setActivities(actRes.data.activities || []);
    } finally {
      setLoading(false);
    }
  }

  const filteredExc = excData?.exceptions.filter(e => filterCat === 'ALL' || e.category === filterCat) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-4 border-red-200 border-t-red-600 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🚨 Exceptions & Monitoring</h1>
          <p className="text-sm text-gray-500 mt-1">
            Exception-first automation — normal cases proceed automatically, exceptions surface here
          </p>
        </div>
        <button onClick={fetchAll} className="bg-white border border-gray-200 hover:bg-gray-50 px-4 py-2 rounded-lg text-sm font-medium transition">
          🔄 Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Exceptions', value: excData?.count ?? 0, bg: 'bg-gray-900 text-white', desc: 'across all categories' },
          { label: 'Critical', value: excData?.critical ?? 0, bg: 'bg-red-600 text-white', desc: 'immediate action required' },
          { label: 'High Priority', value: excData?.high ?? 0, bg: 'bg-amber-500 text-white', desc: 'action within 24h' },
          { label: 'Warnings', value: excData?.warning ?? 0, bg: 'bg-yellow-400 text-gray-900', desc: 'review recommended' },
        ].map(({ label, value, bg, desc }) => (
          <div key={label} className={`rounded-xl p-4 shadow-sm ${bg}`}>
            <div className="text-3xl font-bold">{value}</div>
            <div className="font-semibold text-sm mt-1">{label}</div>
            <div className="text-xs opacity-75 mt-0.5">{desc}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
        {[
          { id: 'exceptions', label: '🚨 Active Exceptions', count: excData?.count },
          { id: 'watchdog', label: '👁️ Payment Watchdog', count: watchdog?.overdue_count },
          { id: 'activity', label: '⚡ Activity Feed', count: activities.length },
        ].map(({ id, label, count }) => (
          <button key={id} onClick={() => setActiveTab(id as typeof activeTab)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition ${activeTab === id ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}`}>
            {label}
            {count !== undefined && count > 0 && (
              <span className="bg-red-100 text-red-700 text-xs font-bold px-1.5 py-0.5 rounded-full">{count}</span>
            )}
          </button>
        ))}
      </div>

      {/* ── Exceptions Tab ─────────────────────────────────────── */}
      {activeTab === 'exceptions' && (
        <div className="space-y-4">
          {/* Filter */}
          <div className="flex gap-2">
            {['ALL', 'CRITICAL', 'HIGH', 'WARNING'].map(cat => (
              <button key={cat} onClick={() => setFilterCat(cat)}
                className={`text-xs font-medium px-3 py-1.5 rounded-full border transition ${filterCat === cat ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'}`}>
                {cat} {cat === 'ALL' ? `(${excData?.count ?? 0})` : cat === 'CRITICAL' ? `(${excData?.critical ?? 0})` : cat === 'HIGH' ? `(${excData?.high ?? 0})` : `(${excData?.warning ?? 0})`}
              </button>
            ))}
          </div>

          {filteredExc.length === 0 ? (
            <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
              <div className="text-4xl mb-3">✅</div>
              <p className="font-semibold text-green-700">No exceptions in this category</p>
              <p className="text-sm text-green-600 mt-1">Normal flow — the system is operating within parameters</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredExc.map((exc, i) => (
                <div key={i} className={`border rounded-xl p-4 ${catColor(exc.category)}`}>
                  <div className="flex items-start gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full mt-1 shrink-0 ${catDot(exc.category)}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-xs font-bold uppercase">{exc.category}</span>
                        <span className="text-xs bg-black/10 px-2 py-0.5 rounded-full font-mono">{exc.type}</span>
                        <h3 className="text-sm font-semibold">{exc.title}</h3>
                      </div>
                      <p className="text-xs opacity-80 mb-2">{exc.detail}</p>
                      {exc.recommended_action && (
                        <div className="text-xs font-medium flex items-center gap-1">
                          <span>→</span>
                          <span>{exc.recommended_action}</span>
                        </div>
                      )}
                    </div>
                    <div className="text-xs opacity-60 shrink-0">
                      {exc.entity_type} #{exc.entity_id}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Payment Watchdog Tab ──────────────────────────────── */}
      {activeTab === 'watchdog' && watchdog && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Monitored', value: watchdog.total_monitored, sub: '' },
              { label: 'Overdue', value: watchdog.overdue_count, sub: `₹${(watchdog.overdue_amount/100000).toFixed(1)}L`, bold: true, red: true },
              { label: 'Due Today', value: watchdog.due_today_count, sub: '' },
              { label: 'Total Exposure', value: `₹${(watchdog.total_exposure/100000).toFixed(1)}L`, sub: 'all unpaid invoices', isText: true },
            ].map(({ label, value, sub, red }) => (
              <div key={label} className={`bg-white rounded-xl border p-4 ${red ? 'border-red-300' : 'border-gray-200'}`}>
                <p className={`text-2xl font-bold ${red ? 'text-red-600' : 'text-gray-900'}`}>{value}</p>
                <p className="text-sm text-gray-500 mt-0.5">{label}</p>
                {sub && <p className={`text-xs mt-0.5 ${red ? 'text-red-500' : 'text-gray-400'}`}>{sub}</p>}
              </div>
            ))}
          </div>

          {Object.entries(watchdog.categories).filter(([, items]) => items.length > 0).map(([cat, items]) => (
            <div key={cat} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className={`px-4 py-2 font-semibold text-sm flex items-center gap-2 ${watchdogColor(cat)}`}>
                <span>{cat.replace(/_/g, ' ')}</span>
                <span className="text-xs font-normal">({items.length})</span>
              </div>
              <div className="divide-y divide-gray-50">
                {items.map((item, i) => (
                  <div key={i} className="px-4 py-3 flex items-center justify-between text-sm">
                    <div>
                      <p className="font-medium text-gray-900">{item.invoice_id}</p>
                      <p className="text-xs text-gray-500">{item.supplier_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">₹{item.amount.toLocaleString('en-IN')}</p>
                      <p className="text-xs text-gray-500">Due: {item.due_date} ({item.days_until_due < 0 ? Math.abs(item.days_until_due) + 'd overdue' : item.days_until_due + 'd'})</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {Object.values(watchdog.categories).every(items => items.length === 0) && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
              <div className="text-4xl mb-3">✅</div>
              <p className="font-semibold text-green-700">No payment due monitoring items</p>
              <p className="text-sm text-green-600 mt-1">All invoices are within normal payment windows</p>
            </div>
          )}
        </div>
      )}

      {/* ── Activity Feed Tab ─────────────────────────────────── */}
      {activeTab === 'activity' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-sm font-semibold text-gray-900">{activities.length} recent system events</p>
          </div>
          <div className="divide-y divide-gray-50 max-h-[600px] overflow-y-auto">
            {activities.length === 0 ? (
              <div className="text-center py-12 text-gray-400">No recent activity</div>
            ) : (
              activities.map((a, i) => (
                <div key={i} className="flex items-start gap-3 px-4 py-3 hover:bg-gray-50 transition">
                  <span className="text-lg mt-0.5 shrink-0">{a.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800 leading-snug">{a.message}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-400">{a.actor}</span>
                      <span className="text-gray-300">·</span>
                      <span className="text-xs text-gray-400">{timeAgo(a.timestamp)}</span>
                      <span className="text-gray-300">·</span>
                      <span className="text-xs font-mono text-gray-300">{a.action}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
