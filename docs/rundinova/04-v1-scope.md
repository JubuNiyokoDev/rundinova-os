---
title: RundiNova OS V1 scope
---

# RundiNova OS V1 scope

This is the approved starting scope for the five-person RundiNova team. It is
the checklist for configuration and acceptance before production deployment.

## Status meanings

- **Available**: supplied by Frappe, ERPNext, HRMS, CRM, or the custom app;
- **Configure**: available, but roles, fields, workflows, branding, or data
  still need to be set up;
- **Build**: a custom integration or feature is still required.

## Approved V1 modules

| Module | Purpose | Current status | First acceptance test |
| --- | --- | --- | --- |
| Users, team and roles | Five named users with least-privilege access | Configure | Each user sees only their workspace |
| Projects and tasks | Daily work, owners, deadlines, status, progress | Configure | A project shows completed and remaining work |
| GitHub integration | Repositories, issues, pull requests, commits | Build | A repository activity is linked to a project |
| Food budget and purchases | Monthly budget of 1,150,000 FBu and itemized purchases | Available + Configure | Every purchase updates the remaining balance |
| General expenses | Non-food operating costs and approvals | Configure | A submitted expense has evidence and an approver |
| Treasury and basic accounting | Cash, bank, income, payments, debts and receivables | Configure | Cash movement reconciles to a report |
| Assets and equipment | Computers, furniture, software and ownership | Configure | Every asset has a custodian and status |
| CRM | Clients, prospects, partners, opportunities and activities | Available + Configure | A contact has a complete activity history |
| Internal communication | Announcements, meetings, decisions and notifications | Configure | A decision is searchable and linked to a project |
| Documents and files | Contracts, invoices, reports, media and templates | Configure | A document has an owner, category and project |
| KPI, goals and impact | Objectives, indicators, progress and outcomes | Available + Configure | A monthly KPI snapshot is reviewable |
| Executive dashboard | Money, work, risks, assets, opportunities and progress | Configure | A director can review the monthly position |
| Security, audit and backups | Permissions, history, recovery and accountability | Configure | A change is attributable and a backup restores |

## Food budget rule

The budget is a monthly envelope of **1,150,000 FBu**. Purchases are recorded
one by one. The plan is not a fixed shopping list: meat can be replaced by fish,
and quantities can change while the historical purchases remain unchanged.
Each record must include date, category, item, quantity, amount, supplier or
seller, payer, payment account, receipt, and approver where required.

## What is not in the first production cut

Do not activate every ERPNext workspace. Manufacturing, stock operations,
payroll, advanced marketing, multi-company accounting, and other unused areas
remain hidden until a real business need is approved.

## Configuration versus development

Most V1 work is configuration: company data, users, roles, workspaces,
accounts, workflows, naming, branding, reports, and permissions. Development
is reserved for the GitHub integration, missing RundiNova-specific rules, and
any workflow that cannot be represented by standard configuration.

## Production gate

Deploy only after these checks pass:

1. The five users and their roles are approved.
2. The first project and GitHub repositories are identified.
3. The food-budget calculation is tested with real sample purchases.
4. Expense approval and evidence rules are approved.
5. Cash and accounting opening balances are verified.
6. The document structure and retention rules are approved.
7. Dashboards show only validated data.
8. Backups, restoration, HTTPS, and audit access are tested.

This document is a scope and acceptance contract; it does not authorize
production deployment or the import of real data by itself.
