/**
 * Application root – routing configuration (Phase 3).
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import AppLayout from './layouts/AppLayout';

// Core pages (Phase 1 & 2)
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import RequirementsPage from './pages/RequirementsPage';
import SuppliersPage from './pages/SuppliersPage';
import RFQsPage from './pages/RFQsPage';
import QuotesPage from './pages/QuotesPage';
import ApprovalsPage from './pages/ApprovalsPage';
import PurchaseOrdersPage from './pages/PurchaseOrdersPage';
import GoodsReceiptsPage from './pages/GoodsReceiptsPage';
import InventoryPage from './pages/InventoryPage';
import InvoicesPage from './pages/InvoicesPage';
import PaymentsPage from './pages/PaymentsPage';
import AuditLogPage from './pages/AuditLogPage';
import SupplierPortalPage from './pages/SupplierPortalPage';

// Phase 3 pages
import AIFeaturesPage from './pages/AIFeaturesPage';
import ExceptionsPage from './pages/ExceptionsPage';
import ReportsPage from './pages/ReportsPage';
import DemoPage from './pages/DemoPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/supplier/rfq/:rfqId" element={<SupplierPortalPage />} />

          {/* Protected (AppLayout handles auth guard) */}
          <Route element={<AppLayout />}>
            {/* Core */}
            <Route path="/"                element={<DashboardPage />} />
            <Route path="/requirements"    element={<RequirementsPage />} />
            <Route path="/suppliers"       element={<SuppliersPage />} />
            <Route path="/rfqs"            element={<RFQsPage />} />
            <Route path="/quotes"          element={<QuotesPage />} />
            <Route path="/approvals"       element={<ApprovalsPage />} />
            <Route path="/purchase-orders" element={<PurchaseOrdersPage />} />
            <Route path="/goods-receipts"  element={<GoodsReceiptsPage />} />
            <Route path="/inventory"       element={<InventoryPage />} />
            <Route path="/invoices"        element={<InvoicesPage />} />
            <Route path="/payments"        element={<PaymentsPage />} />
            <Route path="/audit-log"       element={<AuditLogPage />} />

            {/* Phase 3 */}
            <Route path="/ai"              element={<AIFeaturesPage />} />
            <Route path="/exceptions"      element={<ExceptionsPage />} />
            <Route path="/reports"         element={<ReportsPage />} />
            <Route path="/demo"            element={<DemoPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
