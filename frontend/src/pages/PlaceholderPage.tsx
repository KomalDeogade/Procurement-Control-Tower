/**
 * Placeholder page component for Phase 1 stubs.
 */

interface Props {
  title: string;
  description: string;
  icon: string;
}

export default function PlaceholderPage({ title, description, icon }: Props) {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-surface-900">{title}</h1>
        <p className="text-sm text-surface-500 mt-1">{description}</p>
      </div>

      <div className="bg-white rounded-xl border border-surface-200 p-16 flex flex-col items-center justify-center shadow-sm">
        <span className="text-6xl mb-4">{icon}</span>
        <h2 className="text-xl font-semibold text-surface-700">{title}</h2>
        <p className="text-sm text-surface-400 mt-2 max-w-md text-center">
          This module will be fully implemented in Phase 2.
          The page structure and navigation are ready.
        </p>
        <div className="mt-6 px-4 py-2 bg-primary-50 text-primary-700 text-xs font-medium rounded-lg border border-primary-200">
          Coming in Phase 2
        </div>
      </div>
    </div>
  );
}
