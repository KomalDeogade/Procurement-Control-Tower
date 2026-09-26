/**
 * Approvals Page – manager approval workflow with full context panel.
 */

import { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/ui/StatusBadge';
import Modal from '../components/ui/Modal';

interface Approval {
  id: number;
  display_id: string | null;
  entity_type: string;
  entity_id: number;
  approver_id: number;
  approval_level: number;
  status: string;
  comments: string | null;
  approved_at: string | null;
  created_at: string;
}

interface ApprovalDetail {
  approval: Approval;
  requirement?: any;
  quotes?: any[];
  scores?: any[];
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [selectedApproval, setSelectedApproval] = useState<ApprovalDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionComment, setActionComment] = useState('');
  const [actioning, setActioning] = useState(false);

  const fetchApprovals = async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const res = await api.get<Approval[]>(`/approvals/${params}`);
      setApprovals(res.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchApprovals(); }, [statusFilter]);

  const openDetail = async (approval: Approval) => {
    setDetailLoading(true);
    try {
      const res = await api.get<ApprovalDetail>(`/approvals/${approval.id}/detail`);
      setSelectedApproval(res.data);
      setActionComment('');
    } catch { setSelectedApproval({ approval }); }
    finally { setDetailLoading(false); }
  };

  const handleAction = async (action: 'APPROVED' | 'REJECTED' | 'REVISION_REQUIRED') => {
    if (!selectedApproval) return;
    setActioning(true);
    try {
      await api.patch(`/approvals/${selectedApproval.approval.id}`, {
        status: action,
        comments: actionComment,
      });
      setSelectedApproval(null);
      await fetchApprovals();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Action failed');
    } finally { setActioning(false); }
  };

  const recommendedSupplier = selectedApproval?.scores?.[0];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Approvals</h1>
          <p className="text-sm text-surface-500 mt-1">Manager and finance approval workflows</p>
        </div>
        <div className="flex gap-2 text-sm">
          <span className="px-3 py-1 bg-amber-50 text-amber-700 rounded-full font-medium">
            {approvals.filter(a => a.status === 'PENDING').length} Pending
          </span>
        </div>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-xl border border-surface-200 p-4 mb-4 flex gap-3">
        {['', 'PENDING', 'APPROVED', 'REJECTED', 'REVISION_REQUIRED'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            className={`px-4 py-1.5 text-sm rounded-full font-medium transition-colors ${
              statusFilter === s ? 'bg-primary-600 text-white' : 'text-surface-600 hover:bg-surface-100'
            }`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Approval list */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-surface-50 border-b border-surface-200">
              <tr>
                {['Approval ID', 'Type', 'Entity', 'Level', 'Status', 'Created', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-surface-600 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {approvals.map(a => (
                <tr key={a.id} className="hover:bg-surface-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium text-primary-600">{a.display_id || `#${a.id}`}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-surface-100 text-surface-600 text-xs rounded font-medium capitalize">
                      {a.entity_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-surface-700">#{a.entity_id}</td>
                  <td className="px-4 py-3 text-sm text-surface-600">Level {a.approval_level}</td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                  <td className="px-4 py-3 text-sm text-surface-500">
                    {new Date(a.created_at).toLocaleDateString('en-IN')}
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => openDetail(a)}
                      className="px-3 py-1 text-xs font-medium text-primary-600 border border-primary-200 rounded hover:bg-primary-50 transition-colors">
                      {a.status === 'PENDING' ? 'Review & Act' : 'View'}
                    </button>
                  </td>
                </tr>
              ))}
              {approvals.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-surface-400 text-sm">
                    No approvals found for the selected filter
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Detail Modal */}
      {selectedApproval && (
        <Modal isOpen={!!selectedApproval} onClose={() => setSelectedApproval(null)}
          title={`Approval ${selectedApproval.approval.display_id || `#${selectedApproval.approval.id}`}`} size="lg">
          {detailLoading ? (
            <div className="flex justify-center py-8">
              <div className="w-6 h-6 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-5">
              {/* Status badge + context */}
              <div className="flex items-center gap-3">
                <StatusBadge status={selectedApproval.approval.status} />
                <span className="text-sm text-surface-500">
                  {selectedApproval.approval.entity_type.replace('_', ' ')} · Entity #{selectedApproval.approval.entity_id}
                </span>
              </div>

              {/* Requirement Details */}
              {selectedApproval.requirement && (
                <div className="bg-surface-50 rounded-xl p-4">
                  <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Requirement Details</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {[
                      ['ID', selectedApproval.requirement.display_id],
                      ['Material', selectedApproval.requirement.material_name],
                      ['Quantity', `${selectedApproval.requirement.quantity} ${selectedApproval.requirement.unit}`],
                      ['Budget', selectedApproval.requirement.budget ? `₹${Number(selectedApproval.requirement.budget).toLocaleString('en-IN')}` : '—'],
                      ['Priority', selectedApproval.requirement.priority],
                      ['Plant', selectedApproval.requirement.plant || '—'],
                    ].map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-surface-500">{k}</span>
                        <span className="font-medium text-surface-800">{v}</span>
                      </div>
                    ))}
                  </div>
                  {selectedApproval.requirement.description && (
                    <p className="text-sm text-surface-600 mt-3 pt-3 border-t border-surface-200">
                      {selectedApproval.requirement.description}
                    </p>
                  )}
                </div>
              )}

              {/* Recommended Supplier */}
              {recommendedSupplier && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                  <h4 className="text-xs font-semibold text-green-600 uppercase tracking-wider mb-2">Recommended Supplier</h4>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-base font-bold text-green-800">{recommendedSupplier.supplier_name}</p>
                      <ul className="mt-2 space-y-0.5">
                        {recommendedSupplier.reasons.slice(0, 4).map((r: string, i: number) => (
                          <li key={i} className="text-xs text-green-700">• {r}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-green-700">{recommendedSupplier.score.toFixed(1)}</div>
                      <div className="text-xs text-green-500">Overall Score</div>
                    </div>
                  </div>
                </div>
              )}

              {/* All scores */}
              {selectedApproval.scores && selectedApproval.scores.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">All Supplier Scores</h4>
                  <div className="space-y-2">
                    {selectedApproval.scores.map((s: any) => (
                      <div key={s.supplier_id} className="flex items-center gap-3 p-2 bg-surface-50 rounded-lg">
                        <div className="flex-1">
                          <span className="text-sm font-medium text-surface-800">{s.supplier_name}</span>
                        </div>
                        <div className="w-32 bg-surface-200 rounded-full h-2">
                          <div className={`h-2 rounded-full ${s.is_recommended ? 'bg-green-500' : 'bg-blue-400'}`}
                            style={{ width: `${s.score}%` }} />
                        </div>
                        <span className={`text-sm font-bold w-12 text-right ${s.is_recommended ? 'text-green-600' : 'text-surface-600'}`}>
                          {s.score.toFixed(1)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action section */}
              {selectedApproval.approval.status === 'PENDING' && (
                <div className="border-t border-surface-200 pt-4">
                  <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2">Your Decision</h4>
                  <textarea rows={2} value={actionComment} onChange={e => setActionComment(e.target.value)}
                    placeholder="Add comments (optional)..."
                    className="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:outline-none mb-3" />
                  <div className="flex gap-3">
                    <button onClick={() => handleAction('APPROVED')} disabled={actioning}
                      className="flex-1 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
                      Approve
                    </button>
                    <button onClick={() => handleAction('REVISION_REQUIRED')} disabled={actioning}
                      className="flex-1 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors">
                      Request Revision
                    </button>
                    <button onClick={() => handleAction('REJECTED')} disabled={actioning}
                      className="flex-1 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors">
                      Reject
                    </button>
                  </div>
                </div>
              )}

              {/* Already actioned */}
              {selectedApproval.approval.status !== 'PENDING' && selectedApproval.approval.comments && (
                <div className="border-t border-surface-200 pt-4">
                  <h4 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-1">Decision Comments</h4>
                  <p className="text-sm text-surface-700">{selectedApproval.approval.comments}</p>
                  {selectedApproval.approval.approved_at && (
                    <p className="text-xs text-surface-400 mt-1">
                      {new Date(selectedApproval.approval.approved_at).toLocaleString('en-IN')}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </Modal>
      )}
    </div>
  );
}
