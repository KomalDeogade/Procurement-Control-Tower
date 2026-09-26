/**
 * KPI card – dashboard metric display.
 */

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

export default function KPICard({ title, value, subtitle, icon, trend, trendValue }: Props) {
  const trendColors = {
    up: 'text-success',
    down: 'text-danger',
    neutral: 'text-surface-500',
  };

  return (
    <div className="bg-white rounded-xl border border-surface-200 p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-surface-500">{title}</p>
          <p className="text-2xl font-bold text-surface-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-surface-400 mt-1">{subtitle}</p>}
          {trend && trendValue && (
            <p className={`text-xs mt-2 font-medium ${trendColors[trend]}`}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
            </p>
          )}
        </div>
        {icon && <span className="text-3xl">{icon}</span>}
      </div>
    </div>
  );
}
