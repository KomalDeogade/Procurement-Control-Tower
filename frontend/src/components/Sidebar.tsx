/**
 * Sidebar navigation – Role-Based Navigation filtering (Phase 2).
 */

import { NavLink } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface NavEntry {
  to: string;
  label: string;
  icon: string;
  roles?: string[]; // If omitted, allowed for all roles except SUPPLIER
}

const allNavItems: NavEntry[] = [
  { to: '/',                label: 'Dashboard',        icon: '📊', roles: ['SUPPLIER', 'SCM_USER', 'PROCUREMENT_MANAGER', 'STORE_USER', 'FINANCE_USER', 'ADMIN'] },
  { to: '/requirements',    label: 'Requirements',     icon: '📋', roles: ['SCM_USER', 'PROCUREMENT_MANAGER', 'ADMIN'] },
  { to: '/suppliers',       label: 'Suppliers',        icon: '🏭', roles: ['SCM_USER', 'PROCUREMENT_MANAGER', 'ADMIN'] },
  { to: '/rfqs',            label: 'RFQs',             icon: '📨', roles: ['SUPPLIER', 'SCM_USER', 'PROCUREMENT_MANAGER', 'ADMIN'] },
  { to: '/quotes',          label: 'Quote Comparison', icon: '💰', roles: ['SUPPLIER', 'SCM_USER', 'ADMIN'] },
  { to: '/approvals',       label: 'Approvals',        icon: '✅', roles: ['PROCUREMENT_MANAGER', 'ADMIN'] },
  { to: '/purchase-orders', label: 'Purchase Orders',  icon: '🛒', roles: ['SUPPLIER', 'SCM_USER', 'PROCUREMENT_MANAGER', 'ADMIN'] },
  { to: '/goods-receipts',  label: 'Goods Receipts',   icon: '📫', roles: ['SUPPLIER', 'STORE_USER', 'ADMIN'] },
  { to: '/inventory',       label: 'Inventory',        icon: '📦', roles: ['SCM_USER', 'STORE_USER', 'ADMIN'] },
  { to: '/invoices',        label: 'Invoices',         icon: '🧾', roles: ['FINANCE_USER', 'ADMIN'] },
  { to: '/payments',        label: 'Payments',         icon: '💳', roles: ['FINANCE_USER', 'ADMIN'] },
  { to: '/audit-log',       label: 'Audit Log',        icon: '📜', roles: ['ADMIN'] },
];

const phase3NavItems: NavEntry[] = [
  { to: '/exceptions', label: 'Exceptions',     icon: '🚨', roles: ['SCM_USER', 'PROCUREMENT_MANAGER', 'STORE_USER', 'FINANCE_USER', 'ADMIN'] },
  { to: '/ai',         label: 'AI Features',    icon: '🤖', roles: ['SCM_USER', 'PROCUREMENT_MANAGER', 'ADMIN'] },
  { to: '/reports',    label: 'Reports',        icon: '📄', roles: ['SCM_USER', 'PROCUREMENT_MANAGER', 'FINANCE_USER', 'ADMIN'] },
  { to: '/demo',       label: 'Demo Mode',      icon: '🎯', roles: ['SCM_USER', 'PROCUREMENT_MANAGER', 'ADMIN'] },
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
  const { user } = useAuth();
  const role = user?.role || 'SCM_USER';

  const isAllowed = (item: NavEntry) => {
    if (role === 'ADMIN') return true;
    if (!item.roles) return role !== 'SUPPLIER';
    return item.roles.includes(role);
  };

  const visibleCore = allNavItems.filter(isAllowed);
  const visiblePhase3 = phase3NavItems.filter(isAllowed);

  return (
    <aside className="w-64 bg-surface-900 text-white min-h-screen flex flex-col shadow-lg">
      {/* Brand */}
      <div className="px-6 py-5 border-b border-surface-700">
        <h1 className="text-lg font-bold tracking-tight">SCM Control Tower</h1>
        <p className="text-xs text-surface-400 mt-1">Role: <span className="font-semibold text-blue-400">{role}</span></p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-3 py-1.5 text-xs font-semibold text-surface-500 uppercase tracking-wider">
          Workflow
        </p>
        {visibleCore.map(item => (
          <NavItem key={item.to} {...item} />
        ))}

        {visiblePhase3.length > 0 && (
          <div className="pt-3">
            <p className="px-3 py-1.5 text-xs font-semibold text-surface-500 uppercase tracking-wider">
              AI & Automation
            </p>
            {visiblePhase3.map(item => (
              <NavItem key={item.to} {...item} />
            ))}
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-surface-700 text-xs text-surface-500">
        v0.3.0 · RBAC Active
      </div>
    </aside>
  );
}
