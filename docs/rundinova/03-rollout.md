---
title: RundiNova Tech Rollout
---

# RundiNova Tech Rollout

The rollout is deliberately staged so every stage produces a usable and
verifiable system. Staging the work does not remove any target module.

## Stage 1: infrastructure and identity

- Build the pinned custom image from `apps-rundinova.json`.
- Deploy MariaDB, Redis, workers, scheduler and HTTPS proxy.
- Create the ERP site under the chosen `rundinova.com` hostname.
- Configure company, currency, fiscal year, branches and cost centers.
- Create administrator accounts, roles, two-factor authentication and backups.

## Stage 2: people and operating controls

- Install HRMS and configure employee master data.
- Register the six initial people and their departments.
- Configure leave types, attendance, working hours and expense approvals.
- Create the initial food budget and verify its total against 1,150,000 BIF.
- Configure purchase, payment and budget review workflows.

## Stage 3: engineering delivery

- Configure project templates for software and mobile delivery.
- Configure task statuses, milestones, timesheets and issue escalation.
- Add project budgets, billable status, deliverables and risk reviews.
- Add dashboards for workload, overdue work, delivery and utilization.

## Stage 4: commercial growth

- Configure CRM pipeline, lead sources and opportunity stages.
- Add customers, contacts, proposals, contracts and follow-up activities.
- Configure quotations, sales orders, invoices and payment reconciliation.
- Add growth, communication and community reporting.

## Stage 5: assets, procurement and innovation

- Register laptops, phones, network equipment and software subscriptions.
- Configure suppliers, purchase requests, approvals, receipts and stock.
- Add innovation initiatives, partnerships, experiments and KPI snapshots.
- Add office-level reporting and consolidated management dashboards.

## Stage 6: multi-office operation

- Add each office as a branch, cost center and `RundiNova Office` record.
- Assign managers and restrict records by branch where appropriate.
- Add office-specific budgets and local suppliers.
- Keep group-level accounting and executive reporting consolidated.
- Create a separate site only when legal or security isolation requires it.

## Acceptance checks

Before production use, verify:

- A user can access only the records allowed by their role and branch.
- A food budget cannot exceed its approved ceiling without an explicit override.
- Every purchase and payment has an approver and supporting attachment.
- Employee personal data is unavailable to ordinary employees.
- A project can be traced from opportunity to delivery, invoice and payment.
- Backups restore to a clean test site.
- HTTPS works for every configured hostname.
- Monthly and annual reports reconcile to the accounting ledger.
