/**
 * Status badge with color-coded variants.
 */

const colorMap: Record<string, string> = {
  DRAFT:              'bg-surface-100 text-surface-600',
  SUBMITTED:          'bg-blue-100 text-blue-700',
  RFQ_IN_PROGRESS:    'bg-indigo-100 text-indigo-700',
  QUOTES_RECEIVED:    'bg-purple-100 text-purple-700',
  UNDER_REVIEW:       'bg-yellow-100 text-yellow-700',
  APPROVAL_PENDING:   'bg-amber-100 text-amber-700',
  APPROVED:           'bg-green-100 text-green-700',
  REJECTED:           'bg-red-100 text-red-700',
  PO_CREATED:         'bg-teal-100 text-teal-700',
  COMPLETED:          'bg-emerald-100 text-emerald-700',
  CANCELLED:          'bg-surface-200 text-surface-500',
  PENDING:            'bg-yellow-100 text-yellow-700',
  ACTIVE:             'bg-green-100 text-green-700',
  PROCESSING:         'bg-blue-100 text-blue-700',
  FAILED:             'bg-red-100 text-red-700',
  PAID:               'bg-emerald-100 text-emerald-700',
};

interface Props {
  status: string;
  className?: string;
}

export default function StatusBadge({ status, className = '' }: Props) {
  const colors = colorMap[status] ?? 'bg-surface-100 text-surface-600';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors} ${className}`}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
}
