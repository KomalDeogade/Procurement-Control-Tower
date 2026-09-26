/**
 * Inventory Page – stock levels, risk analysis, replenishment recommendations.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';

interface InventoryItem {
  id: number;
  material_code: string;
  material_name: string;
  quantity_on_hand: number;
  unit: string;
  reorder_level: number;
  safety_stock: number;
  minimum_stock: number;
  average_daily_consumption: number;
  lead_time_days: number;
  reserved_quantity: number;
  last_updated: string | null;
}

interface InventoryAnalysis {
  material_code: string;
  material_name: string;
  quantity_on_hand: number;
  reserved_quantity: number;
  available_stock: number;
  safety_stock: number;
  minimum_stock: number;
  reorder_level: number;
  average_daily_consumption: number;
  lead_time_days: number;
  stock_coverage_days: number | null;
  projected_stockout_date: string | null;
  risk_status: string;
  risk_message: string;
  open_po_quantity: number;
  recommended_reorder_qty: number;
  reorder_reason: string;
}

interface InventoryAnalysisSummary {
  summary: { total_materials: number; normal: number; low: number; critical: number; stockout_risk: number };
  items: InventoryAnalysis[];
}

const RISK_STYLE: Record<string, { badge: string; row: string }> = {
  NORMAL: { badge: 'bg-green-100 text-green-700', row: '' },
  LOW: { badge: 'bg-amber-100 text-amber-700', row: 'bg-amber-50/30' },
  CRITICAL: { badge: 'bg-red-100 text-red-700', row: 'bg-red-50/30' },
  STOCKOUT_RISK: { badge: 'bg-red-200 text-red-800', row: 'bg-red-50/50' },
};

export default function InventoryPage() {
  const [view, setView] = useState<'list' | 'analysis'>('analysis');
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [analysis, setAnalysis] = useState<InventoryAnalysisSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    Promise.all([
      api.get<InventoryItem[]>('/inventory/'),
      api.get<InventoryAnalysisSummary>('/inventory/analysis'),
    ]).then(([itemsRes, analysisRes]) => {
      setItems(itemsRes.data);
      setAnalysis(analysisRes.data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const filteredItems = (analysis?.items || []).filter(item => {
    const matchesRisk = !riskFilter || item.risk_status === riskFilter;
    const matchesSearch = !search || 
      item.material_name.toLowerCase().includes(search.toLowerCase()) ||
      item.material_code.toLowerCase().includes(search.toLowerCase());
    return matchesRisk && matchesSearch;
  });

  if (loading) return (
    <div className="flex justify-center py-16">
      <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Inventory</h1>
          <p className="text-sm text-surface-500 mt-1">Stock levels, risk monitoring, and replenishment planning</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setView('analysis')}
            className={`px-4 py-2 text-sm rounded-lg font-medium transition-colors ${view === 'analysis' ? 'bg-primary-600 text-white' : 'border border-surface-200 text-surface-600 hover:bg-surface-50'}`}>
            Risk Analysis
          </button>
          <button onClick={() => setView('list')}
            className={`px-4 py-2 text-sm rounded-lg font-medium transition-colors ${view === 'list' ? 'bg-primary-600 text-white' : 'border border-surface-200 text-surface-600 hover:bg-surface-50'}`}>
            Stock List
          </button>
        </div>
      </div>

      {/* Summary KPIs */}
      {analysis && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          {[
            { label: 'Total Materials', value: analysis.summary.total_materials, color: 'text-surface-700', bg: 'bg-white' },
            { label: 'Normal', value: analysis.summary.normal, color: 'text-green-600', bg: 'bg-green-50' },
            { label: 'Low Stock', value: analysis.summary.low, color: 'text-amber-600', bg: 'bg-amber-50' },
            { label: 'Critical', value: analysis.summary.critical, color: 'text-red-600', bg: 'bg-red-50' },
            { label: 'Stockout Risk', value: analysis.summary.stockout_risk, color: 'text-red-800', bg: 'bg-red-100' },
          ].map(stat => (
            <div key={stat.label} className={`${stat.bg} border border-surface-200 rounded-xl p-4`}>
              <p className="text-xs text-surface-500">{stat.label}</p>
              <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-surface-200 p-4 mb-4 flex gap-3 flex-wrap">
        <input type="text" placeholder="Search material..."
          value={search} onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-48 px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:outline-none" />
        {['', 'STOCKOUT_RISK', 'CRITICAL', 'LOW', 'NORMAL'].map(r => (
          <button key={r} onClick={() => setRiskFilter(r)}
            className={`px-3 py-1.5 text-xs rounded-full font-medium transition-colors ${
              riskFilter === r ? 'bg-primary-600 text-white' : 'text-surface-600 hover:bg-surface-100 border border-surface-200'
            }`}>
            {r || 'All Risks'}
          </button>
        ))}
      </div>

      {view === 'analysis' && analysis && (
        <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-50 border-b border-surface-200">
                <tr>
                  {['Material', 'Available Stock', 'Safety Stock', 'Reorder Lvl', 'Coverage Days', 'Stockout Date', 'Open PO', 'Risk', 'Recommendation'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {filteredItems.map(item => {
                  const style = RISK_STYLE[item.risk_status] || RISK_STYLE.NORMAL;
                  return (
                    <tr key={item.material_code} className={`hover:bg-surface-50 transition-colors ${style.row}`}>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-surface-900">{item.material_name}</div>
                        <div className="text-xs text-surface-500">{item.material_code}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm font-semibold text-surface-900">{item.available_stock.toLocaleString()}</div>
                        <div className="text-xs text-surface-400">On hand: {item.quantity_on_hand.toLocaleString()}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-surface-700">{item.safety_stock.toLocaleString()}</td>
                      <td className="px-4 py-3 text-sm text-surface-700">{item.reorder_level.toLocaleString()}</td>
                      <td className="px-4 py-3">
                        {item.stock_coverage_days !== null ? (
                          <span className={`text-sm font-medium ${
                            item.stock_coverage_days <= 3 ? 'text-red-600' :
                            item.stock_coverage_days <= 7 ? 'text-amber-600' : 'text-green-600'
                          }`}>{item.stock_coverage_days}d</span>
                        ) : <span className="text-surface-400">—</span>}
                      </td>
                      <td className="px-4 py-3 text-sm text-surface-600">
                        {item.projected_stockout_date || '—'}
                      </td>
                      <td className="px-4 py-3 text-sm text-surface-700">{item.open_po_quantity.toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${style.badge}`}>
                          {item.risk_status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {item.recommended_reorder_qty > 0 ? (
                          <div>
                            <div className="text-xs font-medium text-primary-700">Reorder {item.recommended_reorder_qty.toLocaleString()} units</div>
                            <div className="text-xs text-surface-400 mt-0.5 max-w-xs truncate" title={item.reorder_reason}>{item.reorder_reason}</div>
                          </div>
                        ) : (
                          <span className="text-xs text-green-600">No action needed</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {filteredItems.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-surface-400 text-sm">No items match the filter</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {view === 'list' && (
        <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-50 border-b border-surface-200">
                <tr>
                  {['Material', 'On Hand', 'Reserved', 'Unit', 'Reorder Lvl', 'Safety Stock', 'Daily Consumption', 'Lead Time'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {items.filter(i => !search || i.material_name.toLowerCase().includes(search.toLowerCase()) || i.material_code.toLowerCase().includes(search.toLowerCase())).map(item => (
                  <tr key={item.id} className="hover:bg-surface-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-surface-900">{item.material_name}</div>
                      <div className="text-xs text-surface-500">{item.material_code}</div>
                    </td>
                    <td className="px-4 py-3 text-sm font-semibold text-surface-900">{item.quantity_on_hand.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{item.reserved_quantity.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{item.unit}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{item.reorder_level.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{item.safety_stock.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{item.average_daily_consumption}/day</td>
                    <td className="px-4 py-3 text-sm text-surface-600">{item.lead_time_days}d</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
