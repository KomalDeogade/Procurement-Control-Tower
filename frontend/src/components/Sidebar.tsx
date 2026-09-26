/**
 * Sidebar navigation – Phase 3 (with AI, Exceptions, Reports, Demo sections).
 */

import { NavLink } from 'react-router-dom';

const coreNav = [
  { to: '/',                label: 'Dashboard',        icon: '📊' },
  { to: '/requirements',    label: 'Requirements',     icon: '📋' },
  { to: '/suppliers',       label: 'Suppliers',        icon: '🏭' },
  { to: '/rfqs',            label: 'RFQs',             icon: '📨' },
  { to: '/quotes',          label: 'Quote Comparison', icon: '💰' },
  { to: '/approvals',       label: 'Approvals',        icon: '✅' },
  { to: '/purchase-orders', label: 'Purchase Orders',  icon: '🛒' },
  { to: '/goods-receipts',  label: 'Goods Receipts',   icon: '📫' },
  { to: '/inventory',       label: 'Inventory',        icon: '📦' },
  { to: '/invoices',        label: 'Invoices',         icon: '🧾' },
  { to: '/payments',        label: 'Payments',         icon: '💳' },
  { to: '/audit-log',       label: 'Audit Log',        icon: '📜' },
];

const phase3Nav = [
  { to: '/exceptions', label: 'Exceptions',     icon: '🚨' },
  { to: '/ai',         label: 'AI Features',    icon: '🤖' },
  { to: '/reports',    label: 'Reports',        icon: '📄' },
  { to: '/demo',       label: 'Demo Mode',      icon: '🎯' },
];

function NavItem({ to, label, icon }: { to: string; label: string; icon: string }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? 'bg-primary-600 text-white'
            : 'text-surface-300 hover:bg-surface-800 hover:text-white'
        }`
      }
    >
      <span className="text-base shrink-0">{icon}</span>
      <span className="truncate">{label}</span>
    </NavLink>
  );
}

export default function Sidebar() {
  return (
    <aside className="w-64 bg-surface-900 text-white min-h-screen flex flex-col shadow-lg">
      {/* Brand */}
      <div className="px-6 py-5 border-b border-surface-700">
        <h1 className="text-lg font-bold tracking-tight">SCM Control Tower</h1>
        <p className="text-xs text-surface-400 mt-1">Procurement Intelligence</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {/* Core workflow */}
        <p className="px-3 py-1.5 text-xs font-semibold text-surface-500 uppercase tracking-wider">
          Workflow
        </p>
        {coreNav.map(item => (
          <NavItem key={item.to} {...item} />
        ))}

        {/* Phase 3 — AI & Automation */}
        <div className="pt-3">
          <p className="px-3 py-1.5 text-xs font-semibold text-surface-500 uppercase tracking-wider">
            AI & Automation
          </p>
          {phase3Nav.map(item => (
            <NavItem key={item.to} {...item} />
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-surface-700 text-xs text-surface-500">
        v0.3.0 · Phase 3
      </div>
    </aside>
  );
}
