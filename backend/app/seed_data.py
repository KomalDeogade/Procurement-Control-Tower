"""
Seed data – creates realistic dummy data for the prototype.

10 suppliers, 20 materials/inventory, 20 requirements, 50+ quotations,
20 POs, 20 GRNs, 20 invoices, 20 payments + intentional exceptions.
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.database.session import Base, engine, async_session_maker
from app.models import *  # noqa


async def seed():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        # Check if already seeded
        from sqlalchemy import select, func as sqla_func
        count = (await db.execute(select(sqla_func.count()).select_from(Supplier))).scalar()
        if count and count > 0:
            print("Database already seeded. Skipping.")
            return

        now = datetime.now(timezone.utc)

        # ═══════════════════════════════════════════════════
        #  USERS – look up existing (created by startup seed)
        # ═══════════════════════════════════════════════════
        from app.core.security import get_password_hash
        users_spec = [
            ("admin", "admin@scm.local", "System Administrator", "admin123", "ADMIN"),
            ("scm_user", "scm@scm.local", "Rajesh Kumar", "scm123", "SCM_USER"),
            ("proc_manager", "manager@scm.local", "Anita Sharma", "manager123", "PROCUREMENT_MANAGER"),
            ("finance_user", "finance@scm.local", "Vikram Patel", "finance123", "FINANCE_USER"),
        ]
        users = []
        for uname, email, full_name, pwd, role in users_spec:
            result = await db.execute(select(User).where(User.username == uname))
            u = result.scalar_one_or_none()
            if u is None:
                u = User(username=uname, email=email, full_name=full_name,
                         hashed_password=get_password_hash(pwd), role=role)
                db.add(u)
            users.append(u)
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  SUPPLIERS (10)
        # ═══════════════════════════════════════════════════
        suppliers_data = [
            ("SUP-001", "Acme Steel Corporation", "Amit Verma", "amit@acmesteel.in", "+91-22-2456-7890", "General Manager", "CIN-U27100MH", "Raw Materials", "Mumbai, Maharashtra", 88.0, 85.0, 15.0, "NET 30", "APPROVED"),
            ("SUP-002", "Precision Bearings Ltd", "Sunita Rao", "sunita@precisionbearings.in", "+91-44-2345-6789", "Sales Director", "CIN-L29130TN", "Components", "Chennai, Tamil Nadu", 92.0, 90.0, 10.0, "NET 45", "APPROVED"),
            ("SUP-003", "Global Fasteners Inc", "Rahul Deshmukh", "rahul@globalfasteners.in", "+91-20-2567-8901", "VP Sales", "CIN-U28910MH", "Fasteners", "Pune, Maharashtra", 75.0, 70.0, 30.0, "NET 30", "APPROVED"),
            ("SUP-004", "ElectroParts GmbH India", "Klaus Mueller", "klaus@electroparts.de", "+91-80-2678-9012", "Regional Head", "CIN-U31200KA", "Electronics", "Bangalore, Karnataka", 95.0, 88.0, 8.0, "NET 60", "APPROVED"),
            ("SUP-005", "Pacific Polymers Pvt Ltd", "Chen Wei", "chen@pacificpolymers.in", "+91-22-2789-0123", "Export Manager", "CIN-U24200MH", "Polymers", "Navi Mumbai, Maharashtra", 80.0, 82.0, 25.0, "NET 30", "APPROVED"),
            ("SUP-006", "Bharat Hydraulics Ltd", "Pradeep Singh", "pradeep@bharathydraulics.in", "+91-141-2890-1234", "Managing Director", "CIN-U29199RJ", "Hydraulics", "Jaipur, Rajasthan", 70.0, 65.0, 40.0, "NET 15", "APPROVED"),
            ("SUP-007", "TechnoMotors Pvt Ltd", "Deepa Nair", "deepa@technomotors.in", "+91-484-2901-2345", "Sales Head", "CIN-U31100KL", "Motors & Drives", "Kochi, Kerala", 85.0, 78.0, 20.0, "NET 30", "APPROVED"),
            ("SUP-008", "Apex Industrial Supplies", "Manoj Gupta", "manoj@apexindustrial.in", "+91-120-3012-3456", "Director", "CIN-U51900UP", "General Industrial", "Noida, Uttar Pradesh", 60.0, 55.0, 55.0, "NET 15", "PENDING"),
            ("SUP-009", "Southern Lubricants Corp", "Lakshmi Iyer", "lakshmi@southernlub.in", "+91-44-3123-4567", "Chief Sales Officer", "CIN-U24100TN", "Lubricants & Chemicals", "Chennai, Tamil Nadu", 90.0, 92.0, 12.0, "NET 45", "APPROVED"),
            ("SUP-010", "Indo-German Tools GmbH", "Hans Weber", "hans@indogermantools.in", "+91-20-3234-5678", "Country Manager", "CIN-U28999MH", "Cutting Tools", "Pune, Maharashtra", 93.0, 87.0, 5.0, "NET 60", "APPROVED"),
        ]
        suppliers = []
        for sd in suppliers_data:
            s = Supplier(
                supplier_code=sd[0], company_name=sd[1], contact_person=sd[2],
                email=sd[3], phone=sd[4], designation=sd[5], registration_number=sd[6],
                category=sd[7], location=sd[8], quality_score=sd[9], delivery_score=sd[10],
                risk_score=sd[11], payment_terms=sd[12], approval_status=sd[13]
            )
            db.add(s)
            suppliers.append(s)
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  INVENTORY ITEMS (20 materials)
        # ═══════════════════════════════════════════════════
        materials_data = [
            ("MAT-001", "Carbon Steel Sheet 2mm", "KG", "PLANT-01", "WH-A", 5000, 500, 300, 1000, 150, 7),
            ("MAT-002", "Ball Bearing 6205", "PCS", "PLANT-01", "WH-B", 2500, 200, 100, 500, 80, 10),
            ("MAT-003", "Hex Bolt M10x50 SS304", "PCS", "PLANT-01", "WH-A", 15000, 1500, 800, 3000, 500, 5),
            ("MAT-004", "PLC Controller Unit", "PCS", "PLANT-02", "WH-C", 45, 5, 3, 10, 2, 21),
            ("MAT-005", "Nylon 6 Granules", "KG", "PLANT-01", "WH-D", 8000, 800, 500, 2000, 300, 14),
            ("MAT-006", "Hydraulic Cylinder 50mm", "PCS", "PLANT-01", "WH-B", 120, 10, 5, 20, 3, 14),
            ("MAT-007", "Copper Wire 1.5mm", "MTR", "PLANT-02", "WH-A", 3000, 300, 200, 600, 100, 7),
            ("MAT-008", "Servo Motor 2kW", "PCS", "PLANT-02", "WH-C", 30, 3, 2, 8, 1, 28),
            ("MAT-009", "Industrial Lubricant XLR-500", "L", "PLANT-01", "WH-D", 2000, 500, 300, 800, 120, 10),
            ("MAT-010", "Stainless Steel Rod 10mm", "MTR", "PLANT-01", "WH-A", 1500, 150, 100, 300, 50, 7),
            ("MAT-011", "Timing Belt HTD-5M", "PCS", "PLANT-02", "WH-B", 500, 50, 30, 100, 15, 14),
            ("MAT-012", "Industrial Filter Cartridge", "PCS", "PLANT-01", "WH-D", 200, 20, 10, 50, 8, 7),
            ("MAT-013", "Welding Electrode E7018", "KG", "PLANT-01", "WH-A", 800, 80, 50, 200, 40, 5),
            ("MAT-014", "Pneumatic Valve 1/4inch", "PCS", "PLANT-02", "WH-C", 150, 15, 8, 30, 5, 14),
            ("MAT-015", "Cutting Tool Insert CNMG", "PCS", "PLANT-01", "WH-B", 1000, 100, 50, 200, 30, 10),
            ("MAT-016", "Rubber O-Ring Kit", "SET", "PLANT-01", "WH-D", 300, 30, 15, 60, 10, 5),
            ("MAT-017", "Temperature Sensor PT100", "PCS", "PLANT-02", "WH-C", 80, 8, 5, 15, 2, 21),
            ("MAT-018", "Chain Sprocket 12T", "PCS", "PLANT-01", "WH-B", 250, 25, 15, 50, 8, 10),
            ("MAT-019", "Epoxy Resin Industrial", "KG", "PLANT-01", "WH-D", 400, 40, 25, 100, 20, 7),
            ("MAT-020", "Safety Gloves Nitrile", "PAIR", "PLANT-01", "WH-A", 5000, 500, 200, 1000, 150, 3),
        ]
        # Create some with LOW stock to trigger risk alerts
        inv_items = []
        for i, md in enumerate(materials_data):
            qty = md[5]
            # Make some items low stock
            if md[0] in ("MAT-004", "MAT-008", "MAT-009"):
                qty = int(md[7] * 0.8)  # Below safety stock
            elif md[0] == "MAT-017":
                qty = 3  # Critical
            item = InventoryItem(
                material_code=md[0], material_name=md[1], quantity_on_hand=qty,
                unit=md[2], plant=md[3], warehouse=md[4],
                reorder_level=md[8], safety_stock=md[7], minimum_stock=md[6],
                average_daily_consumption=md[9], lead_time_days=md[10],
                reserved_quantity=0,
            )
            db.add(item)
            inv_items.append(item)
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  REQUIREMENTS (20)
        # ═══════════════════════════════════════════════════
        req_statuses = ["DRAFT", "SUBMITTED", "RFQ_IN_PROGRESS", "QUOTES_RECEIVED",
                        "UNDER_REVIEW", "APPROVAL_PENDING", "APPROVED", "PO_CREATED",
                        "COMPLETED"]
        requirements = []
        req_data = [
            ("MAT-009", "Industrial Lubricant XLR-500", 5000, "L", "PLANT-01", 8000000, "HIGH", "APPROVED", "Bulk lubricant for Q3 production"),
            ("MAT-001", "Carbon Steel Sheet 2mm", 2000, "KG", "PLANT-01", 170000, "HIGH", "PO_CREATED", "Steel sheets for body panels"),
            ("MAT-004", "PLC Controller Unit", 10, "PCS", "PLANT-02", 500000, "CRITICAL", "APPROVAL_PENDING", "Replacement PLCs for Line 4"),
            ("MAT-002", "Ball Bearing 6205", 1000, "PCS", "PLANT-01", 15000, "MEDIUM", "SUBMITTED", "Routine bearing replenishment"),
            ("MAT-008", "Servo Motor 2kW", 5, "PCS", "PLANT-02", 500000, "HIGH", "QUOTES_RECEIVED", "Motors for new CNC machine"),
            ("MAT-005", "Nylon 6 Granules", 3000, "KG", "PLANT-01", 10000, "LOW", "DRAFT", "Granules for injection molding"),
            ("MAT-003", "Hex Bolt M10x50 SS304", 5000, "PCS", "PLANT-01", 15000, "MEDIUM", "COMPLETED", "Fastener stock replenishment"),
            ("MAT-007", "Copper Wire 1.5mm", 1000, "MTR", "PLANT-02", 2000, "LOW", "SUBMITTED", "Wiring for control panels"),
            ("MAT-006", "Hydraulic Cylinder 50mm", 20, "PCS", "PLANT-01", 700000, "HIGH", "RFQ_IN_PROGRESS", "Cylinders for press machine"),
            ("MAT-010", "Stainless Steel Rod 10mm", 500, "MTR", "PLANT-01", 75000, "MEDIUM", "SUBMITTED", "Rods for shaft manufacturing"),
            ("MAT-011", "Timing Belt HTD-5M", 100, "PCS", "PLANT-02", 25000, "MEDIUM", "DRAFT", "Belt replacement schedule"),
            ("MAT-012", "Industrial Filter Cartridge", 50, "PCS", "PLANT-01", 12500, "LOW", "SUBMITTED", "Filter maintenance stock"),
            ("MAT-013", "Welding Electrode E7018", 500, "KG", "PLANT-01", 50000, "MEDIUM", "PO_CREATED", "Welding consumables"),
            ("MAT-015", "Cutting Tool Insert CNMG", 200, "PCS", "PLANT-01", 100000, "HIGH", "APPROVED", "Tool inserts for CNC lathe"),
            ("MAT-014", "Pneumatic Valve 1/4inch", 30, "PCS", "PLANT-02", 45000, "MEDIUM", "SUBMITTED", "Valve replacement"),
            ("MAT-016", "Rubber O-Ring Kit", 100, "SET", "PLANT-01", 10000, "LOW", "DRAFT", "Maintenance kit"),
            ("MAT-017", "Temperature Sensor PT100", 20, "PCS", "PLANT-02", 60000, "CRITICAL", "APPROVAL_PENDING", "Sensor upgrade"),
            ("MAT-018", "Chain Sprocket 12T", 50, "PCS", "PLANT-01", 15000, "MEDIUM", "SUBMITTED", "Drive chain parts"),
            ("MAT-019", "Epoxy Resin Industrial", 200, "KG", "PLANT-01", 40000, "MEDIUM", "DRAFT", "Epoxy for assembly"),
            ("MAT-020", "Safety Gloves Nitrile", 2000, "PAIR", "PLANT-01", 30000, "LOW", "COMPLETED", "PPE restocking"),
        ]
        for i, rd in enumerate(req_data):
            req_date = now - timedelta(days=random.randint(5, 30))
            r = Requirement(
                display_id=f"REQ-{1001 + i}",
                material_code=rd[0], material_name=rd[1], quantity=rd[2],
                unit=rd[3], plant=rd[4], budget=rd[5], currency="INR",
                priority=rd[6], status=rd[7], description=rd[8],
                required_by_date=now + timedelta(days=random.randint(7, 45)),
                created_by=users[1].id, created_at=req_date, updated_at=req_date,
            )
            db.add(r)
            requirements.append(r)
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  RFQs
        # ═══════════════════════════════════════════════════
        rfqs = []
        rfq_counter = 3001
        for req in requirements[:10]:
            chosen = random.sample(suppliers[:8], min(3, len(suppliers[:8])))
            for s in chosen:
                rfq = RFQ(
                    display_id=f"RFQ-{rfq_counter}",
                    requirement_id=req.id, supplier_id=s.id,
                    status="RESPONDED" if req.status in ("QUOTES_RECEIVED", "UNDER_REVIEW", "APPROVAL_PENDING", "APPROVED", "PO_CREATED", "COMPLETED") else "SENT",
                    response_deadline=now + timedelta(days=7),
                    created_at=now - timedelta(days=random.randint(3, 20)),
                )
                db.add(rfq)
                rfqs.append(rfq)
                rfq_counter += 1
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  SUPPLIER QUOTES (50+)
        # ═══════════════════════════════════════════════════
        quote_counter = 5001
        quotes = []

        # Demo scenario: REQ-1001 (XLR-500 Lubricant) gets 3 quotes
        demo_req = requirements[0]
        demo_quotes_data = [
            (suppliers[8], 1500, 5000, 350000, 50000, 7900000, "Immediate", 7, "NET 45", "2 years", "SUBMITTED",
             "Premium grade XLR-500", "ISO certified, fastest delivery", "Higher unit price"),
            (suppliers[4], 1400, 5000, 300000, 80000, 7380000, "2 weeks", 14, "NET 30", "1 year", "SUBMITTED",
             "Standard grade", "Competitive pricing", "Longer lead time"),
            (suppliers[5], 1600, 5000, 400000, 60000, 8460000, "1 week", 10, "NET 15", "1 year", "SUBMITTED",
             "High performance grade", "Best quality", "Above budget, short payment terms"),
        ]
        for qd in demo_quotes_data:
            q = SupplierQuote(
                display_id=f"QUOTE-{quote_counter}",
                requirement_id=demo_req.id, supplier_id=qd[0].id,
                unit_price=qd[1], quantity=qd[2], tax=qd[3], freight=qd[4],
                total_price=qd[5], availability=qd[6], lead_time_days=qd[7],
                payment_terms=qd[8], warranty=qd[9], status=qd[10],
                service_details=qd[11], advantages=qd[12], limitations=qd[13],
                delivery_date=now + timedelta(days=qd[7]),
                submitted_at=now - timedelta(days=5),
            )
            db.add(q)
            quotes.append(q)
            quote_counter += 1

        # Generate quotes for other requirements
        for req in requirements[1:10]:
            n_quotes = random.randint(2, 4)
            chosen = random.sample(suppliers[:8], min(n_quotes, len(suppliers[:8])))
            for s in chosen:
                base_price = (req.budget or 100000) / req.quantity * random.uniform(0.8, 1.3)
                qty = req.quantity
                tax = round(base_price * qty * 0.18, 2)
                freight = round(random.uniform(1000, 50000), 2)
                total = round(base_price * qty + tax + freight, 2)
                avail = random.choice(["Immediate", "1 week", "2 weeks", "3 weeks", "1 month"])
                lead = random.randint(5, 30)
                terms = random.choice(["NET 15", "NET 30", "NET 45", "NET 60"])
                q = SupplierQuote(
                    display_id=f"QUOTE-{quote_counter}",
                    requirement_id=req.id, supplier_id=s.id,
                    unit_price=round(base_price, 2), quantity=qty,
                    tax=tax, freight=freight, total_price=total,
                    availability=avail, lead_time_days=lead,
                    payment_terms=terms, warranty=random.choice(["6 months", "1 year", "2 years"]),
                    status="SUBMITTED",
                    delivery_date=now + timedelta(days=lead),
                    submitted_at=now - timedelta(days=random.randint(1, 10)),
                )
                db.add(q)
                quotes.append(q)
                quote_counter += 1
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  APPROVALS
        # ═══════════════════════════════════════════════════
        approval_counter = 7001
        for req in requirements:
            if req.status in ("APPROVED", "PO_CREATED", "COMPLETED"):
                a = Approval(
                    display_id=f"APR-{approval_counter}",
                    entity_type="requirement", entity_id=req.id,
                    approver_id=users[2].id, approval_level=1,
                    status="APPROVED", comments="Approved as per budget.",
                    approved_at=now - timedelta(days=random.randint(1, 10)),
                )
                db.add(a)
                approval_counter += 1
            elif req.status == "APPROVAL_PENDING":
                a = Approval(
                    display_id=f"APR-{approval_counter}",
                    entity_type="requirement", entity_id=req.id,
                    approver_id=users[2].id, approval_level=1, status="PENDING",
                )
                db.add(a)
                approval_counter += 1
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  PURCHASE ORDERS (20)
        # ═══════════════════════════════════════════════════
        po_reqs = [r for r in requirements if r.status in ("PO_CREATED", "COMPLETED")]
        po_counter = 450001
        pos = []
        for req in po_reqs:
            req_quotes = [q for q in quotes if q.requirement_id == req.id]
            chosen_q = req_quotes[0] if req_quotes else None
            sup = suppliers[0]
            up = 85.0
            total = req.quantity * up
            if chosen_q:
                sup_id = chosen_q.supplier_id
                up = chosen_q.unit_price
                total = chosen_q.total_price
                sup = next((s for s in suppliers if s.id == sup_id), suppliers[0])
            po = PurchaseOrder(
                display_id=f"PO-{po_counter}",
                requirement_id=req.id, supplier_id=sup.id,
                quote_id=chosen_q.id if chosen_q else None,
                sap_po_number=str(450001000 + po_counter - 450001),
                material_code=req.material_code, material_name=req.material_name,
                quantity=req.quantity, unit_price=up, total_amount=total,
                currency="INR", delivery_date=now + timedelta(days=random.randint(7, 30)),
                status="COMPLETED" if req.status == "COMPLETED" else "SAP_CREATED",
                payment_terms=chosen_q.payment_terms if chosen_q else "NET 30",
                created_by=users[1].id,
            )
            db.add(po)
            pos.append(po)
            po_counter += 1

        # Add more POs for other approved reqs
        for req in requirements:
            if req.status == "APPROVED" and len(pos) < 20:
                req_quotes = [q for q in quotes if q.requirement_id == req.id]
                chosen_q = req_quotes[0] if req_quotes else None
                s = suppliers[random.randint(0, 7)]
                up = (req.budget or 100000) / req.quantity
                total = up * req.quantity
                if chosen_q:
                    s = next((sup for sup in suppliers if sup.id == chosen_q.supplier_id), s)
                    up = chosen_q.unit_price
                    total = chosen_q.total_price
                po = PurchaseOrder(
                    display_id=f"PO-{po_counter}",
                    requirement_id=req.id, supplier_id=s.id,
                    quote_id=chosen_q.id if chosen_q else None,
                    sap_po_number=str(450001000 + po_counter - 450001),
                    material_code=req.material_code, material_name=req.material_name,
                    quantity=req.quantity, unit_price=up, total_amount=total,
                    currency="INR", delivery_date=now + timedelta(days=14),
                    status="SAP_CREATED", payment_terms="NET 30",
                    created_by=users[1].id,
                )
                db.add(po)
                pos.append(po)
                po_counter += 1
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  GOODS RECEIPTS (20)
        # ═══════════════════════════════════════════════════
        grn_counter = 6001
        grns = []
        for po in pos:
            received_qty = po.quantity
            quality = "PASSED"
            # Intentional mismatch: some GRNs have less quantity
            if random.random() < 0.2:
                received_qty = po.quantity * random.uniform(0.9, 0.98)
                quality = "PARTIAL"
            grn = GoodsReceipt(
                display_id=f"GRN-{grn_counter}",
                po_id=po.id, received_quantity=round(received_qty, 0),
                quality_status=quality, inspector="QA Team",
                remarks="Standard inspection completed" if quality == "PASSED" else "Partial quantity received",
                sap_grn_number=f"GRN-SAP-{grn_counter}",
            )
            db.add(grn)
            grns.append(grn)
            grn_counter += 1
            po.status = "FULLY_RECEIVED" if received_qty >= po.quantity * 0.99 else "PARTIALLY_RECEIVED"
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  INVOICES (20)
        # ═══════════════════════════════════════════════════
        inv_counter = 220001
        invoices = []
        for i, po in enumerate(pos):
            inv_amount = po.total_amount
            tax = round(inv_amount * 0.18, 2)
            total = round(inv_amount + tax, 2)
            inv_date = now - timedelta(days=random.randint(0, 15))
            terms_days = random.choice([15, 30, 45, 60])
            due = inv_date + timedelta(days=terms_days)

            # Intentional mismatches
            status_val = "VALIDATED"
            if i % 5 == 0:  # Every 5th invoice has a mismatch
                inv_amount = po.total_amount * random.uniform(1.06, 1.15)
                total = round(inv_amount + tax, 2)
                status_val = "DISCREPANCY"
            elif i % 7 == 0:
                status_val = "APPROVAL_PENDING"

            # Some already paid
            if po.status == "COMPLETED":
                status_val = "PAID"

            inv = Invoice(
                display_id=f"INV-{inv_counter}",
                po_id=po.id, supplier_id=po.supplier_id,
                invoice_amount=round(inv_amount, 2), tax_amount=tax,
                total_amount=total, invoice_date=inv_date, due_date=due,
                status=status_val,
            )
            db.add(inv)
            invoices.append(inv)
            inv_counter += 1
        await db.flush()

        # ═══════════════════════════════════════════════════
        #  PAYMENTS (20)
        # ═══════════════════════════════════════════════════
        pay_counter = 80001
        for inv in invoices:
            status = "PENDING"
            ref = None
            pay_date = None
            if inv.status == "PAID":
                status = "COMPLETED"
                ref = f"MOCK-TXN-{random.randint(10000, 99999)}"
                pay_date = now - timedelta(days=random.randint(1, 5))
            elif inv.status == "VALIDATED":
                status = "PENDING"
            pay = Payment(
                display_id=f"PAY-{pay_counter}",
                invoice_id=inv.id, amount=inv.total_amount,
                payment_date=pay_date, status=status,
                reference_number=ref,
            )
            db.add(pay)
            pay_counter += 1

        # ═══════════════════════════════════════════════════
        #  AUDIT LOGS
        # ═══════════════════════════════════════════════════
        import json
        audit_entries = [
            ("system", "SEED", "system", "SEED-001", "System seeded with demo data"),
        ]
        for req in requirements[:5]:
            db.add(AuditLog(
                actor="scm_user", action="CREATE", entity_type="requirement",
                entity_id=req.display_id or str(req.id),
                new_value=json.dumps({"material": req.material_name, "quantity": req.quantity}),
            ))
        for po in pos[:3]:
            db.add(AuditLog(
                actor="scm_user", action="CREATE", entity_type="purchase_order",
                entity_id=po.display_id or str(po.id),
                new_value=json.dumps({"supplier_id": po.supplier_id, "total": po.total_amount}),
            ))
            db.add(AuditLog(
                actor="system", action="SAP_SYNC", entity_type="purchase_order",
                entity_id=po.display_id or str(po.id),
                new_value=json.dumps({"sap_po_number": po.sap_po_number, "status": "SYNCHRONIZED"}),
            ))

        await db.commit()
        print(f"[OK] Seed complete: {len(suppliers)} suppliers, {len(inv_items)} materials, "
              f"{len(requirements)} requirements, {len(quotes)} quotes, {len(pos)} POs, "
              f"{len(grns)} GRNs, {len(invoices)} invoices")


if __name__ == "__main__":
    asyncio.run(seed())
