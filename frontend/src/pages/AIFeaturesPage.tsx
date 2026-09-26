/**
 * AI Features Page – AI-assisted procurement tools.
 * - Document extraction (PDF/text → structured quote)
 * - Negotiation email drafter
 * - Email/message summarizer
 * - Inventory risk explainer
 * - AI status check
 */

import { useState } from 'react';
import api from '../services/api';

type Tab = 'extract' | 'negotiate' | 'summarize' | 'status';

interface AIStatus {
  provider: string;
  available: boolean;
  mode: string;
  message: string;
}

interface ExtractResult {
  extracted: Record<string, unknown>;
  status: string;
  confidence: number;
  missing_fields: string[];
  message: string;
  ai_provider: string;
}

interface DraftResult {
  subject: string;
  body: string;
  status: string;
  requires_approval: boolean;
  ai_provider: string;
}

interface SummaryResult {
  summary: {
    summary: string;
    price_mentioned?: string;
    availability?: string;
    delivery?: string;
    payment_terms?: string;
    risks: string[];
    required_action: string;
    sentiment: string;
  };
  ai_provider: string;
}

export default function AIFeaturesPage() {
  const [tab, setTab] = useState<Tab>('extract');
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);

  // Extract
  const [extractText, setExtractText] = useState('');
  const [extractResult, setExtractResult] = useState<ExtractResult | null>(null);
  const [extractLoading, setExtractLoading] = useState(false);

  // Negotiate
  const [negotiateForm, setNegotiateForm] = useState({
    supplier_name: 'Vendor B (Beta Industrial)',
    requirement_id: 'REQ-DEMO',
    material: 'Industrial Lubricant XLR-500',
    quoted_price: 8500000,
    target_budget: 8000000,
    desired_delivery_days: 14,
    preferred_payment_terms: 'NET 30',
    additional_context: '',
  });
  const [draftResult, setDraftResult] = useState<DraftResult | null>(null);
  const [negotiateLoading, setNegotiateLoading] = useState(false);
  const [draftApproved, setDraftApproved] = useState(false);

  // Summarize
  const [emailText, setEmailText] = useState('');
  const [summaryResult, setSummaryResult] = useState<SummaryResult | null>(null);
  const [summarizeLoading, setSummarizeLoading] = useState(false);

  async function checkStatus() {
    setStatusLoading(true);
    try {
      const res = await api.get<AIStatus>('/ai/status');
      setAiStatus(res.data);
    } finally {
      setStatusLoading(false);
    }
  }

  async function extractDocument() {
    if (!extractText.trim()) return;
    setExtractLoading(true);
    setExtractResult(null);
    try {
      const form = new FormData();
      form.append('text', extractText);
      const res = await api.post<ExtractResult>('/ai/extract-quote', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setExtractResult(res.data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail || 'Extraction failed');
    } finally {
      setExtractLoading(false);
    }
  }

  async function draftNegotiation() {
    setNegotiateLoading(true);
    setDraftResult(null);
    setDraftApproved(false);
    try {
      const res = await api.post<DraftResult>('/ai/draft-negotiation', negotiateForm);
      setDraftResult(res.data);
    } finally {
      setNegotiateLoading(false);
    }
  }

  async function summarizeEmail() {
    if (!emailText.trim()) return;
    setSummarizeLoading(true);
    setSummaryResult(null);
    try {
      const res = await api.post<SummaryResult>('/ai/summarize-email', { text: emailText });
      setSummaryResult(res.data);
    } finally {
      setSummarizeLoading(false);
    }
  }

  const sentimentColor = (s?: string) => ({
    positive: 'text-green-600', negative: 'text-red-600', concerning: 'text-amber-600', neutral: 'text-gray-600'
  }[s || 'neutral'] || 'text-gray-600');

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'extract',   label: 'Document Extraction', icon: '📄' },
    { id: 'negotiate', label: 'Negotiation Email',    icon: '✉️' },
    { id: 'summarize', label: 'Email Summarizer',     icon: '📝' },
    { id: 'status',    label: 'AI Status',            icon: '⚙️' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">🤖 AI Features</h1>
        <p className="text-sm text-gray-500 mt-1">
          AI-assisted tools — deterministic business logic remains the source of truth
        </p>
      </div>

      {/* Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
        <strong>ℹ️ How AI is used here:</strong> AI provides explanations, extracts document data, and drafts emails.
        It does <strong>not</strong> make business decisions, recalculate scores, or approve actions.
        All outputs require human review before action.
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition ${tab === t.id ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}`}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Document Extraction ───────────────────────────── */}
      {tab === 'extract' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-1">AI Quotation Extraction</h2>
            <p className="text-xs text-gray-500 mb-4">
              Paste quotation text or upload a PDF. AI extracts structured fields. Missing required fields = NEEDS_REVIEW status.
            </p>

            <textarea
              value={extractText}
              onChange={e => setExtractText(e.target.value)}
              rows={8}
              placeholder={`Paste supplier quotation text here, e.g.:

Dear Procurement Team,

We are pleased to offer our quotation for Industrial Lubricant XLR-500:
- Quantity: 5,000 Liters
- Unit Price: ₹1,680 per Liter
- Total Price: ₹8,400,000
- Tax (18% GST): ₹1,512,000
- Freight: ₹25,000
- Availability: In Stock
- Lead Time: 14 days
- Payment Terms: NET 30
- Warranty: 12 months
...`}
              className="w-full border border-gray-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 font-mono resize-y"
            />

            <button
              onClick={extractDocument}
              disabled={extractLoading || !extractText.trim()}
              className="mt-3 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition disabled:opacity-50"
            >
              {extractLoading ? '⟳ Extracting…' : '🤖 Extract Fields'}
            </button>
          </div>

          {extractResult && (
            <div className={`bg-white rounded-xl border shadow-sm p-6 ${extractResult.status === 'NEEDS_REVIEW' ? 'border-amber-300' : 'border-green-300'}`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Extraction Result</h3>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${extractResult.status === 'NEEDS_REVIEW' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                    {extractResult.status}
                  </span>
                  <span className="text-xs text-gray-500">Confidence: {Math.round(extractResult.confidence * 100)}%</span>
                  <span className="text-xs text-gray-400">Provider: {extractResult.ai_provider}</span>
                </div>
              </div>

              {extractResult.missing_fields.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-xs text-amber-700">
                  ⚠️ Missing required fields: <strong>{extractResult.missing_fields.join(', ')}</strong> — complete these before saving the quote.
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(extractResult.extracted).filter(([k]) => !['confidence','needs_review','missing_fields'].includes(k)).map(([k, v]) => (
                  <div key={k} className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 capitalize">{k.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-medium text-gray-900 mt-0.5">
                      {v === null || v === undefined || v === '' ? <span className="text-gray-300 italic">—</span> : String(v)}
                    </p>
                  </div>
                ))}
              </div>

              <p className="text-xs text-gray-400 mt-4 italic">{extractResult.message}</p>
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Negotiation Email ─────────────────────────────── */}
      {tab === 'negotiate' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-1">AI Negotiation Email Drafter</h2>
            <p className="text-xs text-gray-500 mb-4">
              AI drafts a negotiation email. It is a <strong>DRAFT</strong> — you must review and approve before sending.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { label: 'Supplier Name', key: 'supplier_name', type: 'text' },
                { label: 'Requirement ID', key: 'requirement_id', type: 'text' },
                { label: 'Material', key: 'material', type: 'text' },
                { label: 'Quoted Price (₹)', key: 'quoted_price', type: 'number' },
                { label: 'Target Budget (₹)', key: 'target_budget', type: 'number' },
                { label: 'Desired Delivery (days)', key: 'desired_delivery_days', type: 'number' },
                { label: 'Preferred Payment Terms', key: 'preferred_payment_terms', type: 'text' },
              ].map(({ label, key, type }) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
                  <input
                    type={type}
                    value={(negotiateForm as Record<string, unknown>)[key] as string | number}
                    onChange={e => setNegotiateForm(f => ({ ...f, [key]: type === 'number' ? Number(e.target.value) : e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  />
                </div>
              ))}
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1">Additional Context (optional)</label>
                <textarea rows={2} value={negotiateForm.additional_context}
                  onChange={e => setNegotiateForm(f => ({ ...f, additional_context: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300" />
              </div>
            </div>

            <button onClick={draftNegotiation} disabled={negotiateLoading}
              className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition disabled:opacity-50">
              {negotiateLoading ? '⟳ Drafting…' : '✉️ Draft Negotiation Email'}
            </button>
          </div>

          {draftResult && (
            <div className="bg-white rounded-xl border border-amber-300 shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">📝 Draft Email</h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full">DRAFT — NOT SENT</span>
                  <span className="text-xs text-gray-400">{draftResult.ai_provider}</span>
                </div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-xs text-amber-700">
                ⚠️ This is an AI-generated draft. Review carefully before approving or sending.
              </div>

              <div className="space-y-3 mb-4">
                <div>
                  <p className="text-xs text-gray-500 mb-0.5">Subject</p>
                  <p className="text-sm font-medium text-gray-900 bg-gray-50 rounded-lg px-3 py-2">{draftResult.subject}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-0.5">To</p>
                  <p className="text-sm text-gray-900 bg-gray-50 rounded-lg px-3 py-2">{negotiateForm.supplier_name}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-0.5">Body</p>
                  <pre className="text-sm text-gray-800 bg-gray-50 rounded-lg p-4 whitespace-pre-wrap font-sans border border-gray-100">{draftResult.body}</pre>
                </div>
              </div>

              {!draftApproved ? (
                <div className="flex gap-3">
                  <button onClick={() => setDraftApproved(true)}
                    className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition">
                    ✅ Approve Draft
                  </button>
                  <button onClick={() => setDraftResult(null)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition">
                    ❌ Discard
                  </button>
                </div>
              ) : (
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">
                  ✅ Draft approved. In production, this would trigger email sending via configured SMTP/API. (Demo mode — not sent)
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Email Summarizer ──────────────────────────────── */}
      {tab === 'summarize' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-1">Supplier Email Summarizer</h2>
            <p className="text-xs text-gray-500 mb-4">
              Paste any supplier email or message. AI extracts key procurement information and identifies required actions.
            </p>

            <textarea
              value={emailText}
              onChange={e => setEmailText(e.target.value)}
              rows={8}
              placeholder={`Paste supplier email text here, e.g.:

Dear Procurement Team,

Thank you for your inquiry regarding Industrial Lubricant XLR-500.

We confirm availability for 5,000 liters at ₹1,680 per liter (exclusive of GST).
GST at 18% would be applicable additionally.
Freight: ₹25,000 for delivery to Mumbai.

Please note our stock is limited and will be reserved for 5 business days only.
Lead time: 14 working days from PO confirmation.
Payment Terms: NET 30 days from invoice date.

Best regards,
Vendor A`}
              className="w-full border border-gray-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 resize-y"
            />

            <button onClick={summarizeEmail} disabled={summarizeLoading || !emailText.trim()}
              className="mt-3 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition disabled:opacity-50">
              {summarizeLoading ? '⟳ Summarizing…' : '📝 Summarize Email'}
            </button>
          </div>

          {summaryResult && (
            <div className="bg-white rounded-xl border border-teal-300 shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Email Summary</h3>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium capitalize ${sentimentColor(summaryResult.summary.sentiment)}`}>
                    {summaryResult.summary.sentiment} sentiment
                  </span>
                  <span className="text-xs text-gray-400">{summaryResult.ai_provider}</span>
                </div>
              </div>

              <div className="bg-teal-50 border border-teal-200 rounded-lg p-4 mb-4">
                <p className="text-sm text-teal-900">{summaryResult.summary.summary}</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                {[
                  { label: 'Price Mentioned', value: summaryResult.summary.price_mentioned },
                  { label: 'Availability', value: summaryResult.summary.availability },
                  { label: 'Delivery', value: summaryResult.summary.delivery },
                  { label: 'Payment Terms', value: summaryResult.summary.payment_terms },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="text-sm font-medium text-gray-900 mt-0.5">{value || <span className="text-gray-300 italic">—</span>}</p>
                  </div>
                ))}
              </div>

              {summaryResult.summary.risks.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                  <p className="text-xs font-semibold text-red-700 mb-1">⚠️ Risks Identified</p>
                  <ul className="space-y-0.5">
                    {summaryResult.summary.risks.map((r, i) => (
                      <li key={i} className="text-xs text-red-600">• {r}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-blue-700 mb-1">Required Action</p>
                <p className="text-sm text-blue-900">{summaryResult.summary.required_action}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Tab: AI Status ─────────────────────────────────────── */}
      {tab === 'status' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h2 className="font-semibold text-gray-900 mb-1">AI Provider Status</h2>
            <p className="text-xs text-gray-500 mb-4">Check which AI provider is configured and available.</p>

            <button onClick={checkStatus} disabled={statusLoading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition disabled:opacity-50">
              {statusLoading ? '⟳ Checking…' : '⚙️ Check AI Status'}
            </button>

            {aiStatus && (
              <div className="mt-4 space-y-3">
                <div className={`border rounded-xl p-4 ${aiStatus.available ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${aiStatus.available ? 'bg-green-500' : 'bg-amber-500'}`} />
                    <div>
                      <p className="font-semibold text-sm text-gray-900">{aiStatus.available ? 'AI Connected' : 'Mock/Fallback Mode'}</p>
                      <p className="text-xs text-gray-600 mt-0.5">{aiStatus.message}</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'Provider', value: aiStatus.provider },
                    { label: 'Mode', value: aiStatus.mode },
                    { label: 'Status', value: aiStatus.available ? 'Connected' : 'Fallback' },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">{label}</p>
                      <p className="text-sm font-medium text-gray-900 mt-0.5">{value}</p>
                    </div>
                  ))}
                </div>

                {!aiStatus.available && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                    <p className="font-medium mb-2">To enable live AI:</p>
                    <ol className="space-y-1 list-decimal list-inside text-xs">
                      <li>Edit <code className="bg-blue-100 px-1 rounded">backend/.env</code></li>
                      <li>Set <code className="bg-blue-100 px-1 rounded">AI_PROVIDER=openai</code> (or <code className="bg-blue-100 px-1 rounded">gemini</code>)</li>
                      <li>Set <code className="bg-blue-100 px-1 rounded">AI_API_KEY=your-key</code></li>
                      <li>Restart the backend server</li>
                    </ol>
                    <p className="text-xs text-blue-600 mt-2 italic">The system works fully without AI — mock mode provides realistic demo responses.</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* How AI is used */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-semibold text-gray-900 mb-3">How AI is Used</h3>
            <div className="space-y-3">
              {[
                { title: '✅ AI IS used for', items: ['Document text extraction → structured fields', 'Human-readable score explanations', 'Negotiation email drafting (requires approval)', 'Email/message summarization', 'Daily procurement brief narrative'] },
                { title: '❌ AI is NOT used for', items: ['Supplier scoring (deterministic engine)', '3-Way match calculations (deterministic)', 'Inventory risk levels (deterministic)', 'Payment due categorization (deterministic)', 'Any automatic approvals or payments'] },
              ].map(({ title, items }) => (
                <div key={title} className={`rounded-lg p-4 ${title.startsWith('✅') ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <p className={`text-sm font-semibold mb-2 ${title.startsWith('✅') ? 'text-green-800' : 'text-red-800'}`}>{title}</p>
                  <ul className="space-y-0.5">
                    {items.map((item, i) => (
                      <li key={i} className={`text-xs ${title.startsWith('✅') ? 'text-green-700' : 'text-red-700'}`}>• {item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
