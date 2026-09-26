/**
 * Audit Log Page – full audit trail with filtering.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';

interface AuditLog {
  id: number;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  timestamp: string;
  old_value: string | null;
  new_value: string | null;
}

const ACTION_COLORS: Record<string, string> = {
  CREATE: 'bg-green-100 text-green-700',
  SUBMIT: 'bg-blue-100 text-blue-700',
  UPDATE: 'bg-amber-100 text-amber-700',
  DELETE: 'bg-red-100 text-red-700',
  APPROVED: 'bg-emerald-100 text-emerald-700',
  REJECTED: 'bg-red-100 text-red-700',
  REVISION_REQUIRED: 'bg-amber-100 text-amber-700',
  SAP_SYNC: 'bg-purple-100 text-purple-700',
  THREE_WAY_MATCH: 'bg-indigo-100 text-indigo-700',
  PROCESS_PAYMENT: 'bg-teal-100 text-teal-700',
  GENERATE_RFQS: 'bg-cyan-100 text-cyan-700',
  SUBMIT_QUOTE: 'bg-blue-100 text-blue-700',
  COMPARE_QUOTES: 'bg-violet-100 text-violet-700',
  CREATE_GRN: 'bg-green-100 text-green-700',
  INVENTORY_UPDATE: 'bg-green-100 text-green-700',
  CREATE_APPROVAL: 'bg-amber-100 text-amber-700',
};

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [search, setSearch] = useState('');
  const [expandedLog, setExpandedLog] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  useEffect(() => {
    const params = new URLSearchParams();
    if (actionFilter) params.set('action', actionFilter);
    if (entityFilter) params.set('entity_type', entityFilter);
    api.get<{ value: AuditLog[]; count: number }>(`/audit/?${params}`)
      .then(res => setLogs(res.data.value || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [actionFilter, entityFilter]);

  const filtered = logs.filter(l => {
    if (!search) return true;
    return (
      l.entity_id.toLowerCase().includes(search.toLowerCase()) ||
      l.actor.toLowerCase().includes(search.toLowerCase()) ||
      l.action.toLowerCase().includes(search.toLowerCase()) ||
      l.entity_type.toLowerCase().includes(search.toLowerCase())
    );
  });

  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

  const uniqueActions = [...new Set(logs.map(l => l.action))].sort();
  const uniqueEntities = [...new Set(logs.map(l => l.entity_type))].sort();

  const tryParseJson = (s: string | null) => {
    if (!s) return null;
    try { return JSON.parse(s); } catch { return s; }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Audit Log</h1>
          <p className="text-sm text-surface-500 mt-1">Complete audit trail for all system events</p>
        </div>
        <span className="px-3 py-1 bg-surface-100 text-surface-600 rounded-full text-sm font-medium">
          {filtered.length} events
        </span>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-surface-200 p-4 mb-4 flex flex-wrap gap-3">
        <input type="text" placeholder="Search actor, ID, action..."
          value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 min-w-48 px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
        <select value={actionFilter} onChange={e => { setActionFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
          <option value="">All Actions</option>
          {uniqueActions.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <select value={entityFilter} onChange={e => { setEntityFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none">
          <option value="">All Entities</option>
          {uniqueEntities.map(e => <option key={e} value={e}>{e.replace('_', ' ')}</option>)}
        </select>
      </div>

      {/* Log Table */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          </div>
        ) : (
          <>
            <table className="w-full">
              <thead className="bg-surface-50 border-b border-surface-200">
                <tr>
                  {['Timestamp', 'Actor', 'Action', 'Entity', 'Entity ID', 'Details'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {paginated.map(log => (
                  <>
                    <tr key={log.id}
                      onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                      className="hover:bg-surface-50 transition-colors cursor-pointer">
                      <td className="px-4 py-3 text-xs text-surface-500 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'medium' })}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          log.actor === 'system' ? 'bg-surface-100 text-surface-500' : 'bg-primary-50 text-primary-700'
                        }`}>{log.actor}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${ACTION_COLORS[log.action] || 'bg-surface-100 text-surface-600'}`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-surface-600 capitalize">{log.entity_type.replace('_', ' ')}</td>
                      <td className="px-4 py-3 text-xs font-mono text-surface-700">{log.entity_id}</td>
                      <td className="px-4 py-3 text-xs text-surface-400">{expandedLog === log.id ? '▲ Collapse' : '▼ Expand'}</td>
                    </tr>
                    {expandedLog === log.id && (
                      <tr key={`${log.id}-detail`} className="bg-surface-50">
                        <td colSpan={6} className="px-6 py-3">
                          <div className="grid grid-cols-2 gap-4 text-xs">
                            {log.old_value && (
                              <div>
                                <div className="font-semibold text-surface-600 mb-1">Before</div>
                                <pre className="bg-red-50 border border-red-100 text-red-800 rounded p-2 overflow-auto max-h-24 text-xs">
                                  {typeof tryParseJson(log.old_value) === 'object'
                                    ? JSON.stringify(tryParseJson(log.old_value), null, 2)
                                    : log.old_value}
                                </pre>
                              </div>
                            )}
                            {log.new_value && (
                              <div>
                                <div className="font-semibold text-surface-600 mb-1">After</div>
                                <pre className="bg-green-50 border border-green-100 text-green-800 rounded p-2 overflow-auto max-h-24 text-xs">
                                  {typeof tryParseJson(log.new_value) === 'object'
                                    ? JSON.stringify(tryParseJson(log.new_value), null, 2)
                                    : log.new_value}
                                </pre>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
                {paginated.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-surface-400 text-sm">No audit events found</td>
                  </tr>
                )}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-surface-200">
                <span className="text-xs text-surface-500">
                  Page {page} of {totalPages} · {filtered.length} events
                </span>
                <div className="flex gap-2">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                    className="px-3 py-1 text-xs border border-surface-200 rounded hover:bg-surface-50 disabled:opacity-40 transition-colors">
                    ← Prev
                  </button>
                  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                    className="px-3 py-1 text-xs border border-surface-200 rounded hover:bg-surface-50 disabled:opacity-40 transition-colors">
                    Next →
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
