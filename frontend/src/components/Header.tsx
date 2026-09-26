/**
 * Top header bar with user info and logout.
 */

import { useAuth } from '../hooks/useAuth';

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-surface-200 flex items-center justify-between px-6 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold text-surface-800">
          Procurement Control Tower
        </h2>
      </div>

      <div className="flex items-center gap-4">
        {/* Notification bell (placeholder) */}
        <button className="relative p-2 text-surface-500 hover:text-surface-700 transition-colors">
          🔔
          <span className="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full" />
        </button>

        {/* User */}
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-surface-800">{user.full_name}</p>
              <p className="text-xs text-surface-500">{user.role.replace('_', ' ')}</p>
            </div>
            <button
              onClick={logout}
              className="px-3 py-1.5 text-xs font-medium text-danger border border-danger/30 rounded-lg hover:bg-danger/5 transition-colors"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
