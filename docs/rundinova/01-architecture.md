---
title: RundiNova Tech ERP Architecture
---

# RundiNova Tech ERP Architecture

This document defines the target operating platform for RundiNova Tech. The
public static website remains a separate project. The ERP is exposed through
one or more subdomains such as `erp.rundinova.com`.

## Platform layers

| Layer                 | Responsibility                                       | Initial implementation                                     |
| --------------------- | ---------------------------------------------------- | ---------------------------------------------------------- |
| Docker infrastructure | Containers, networking, persistence, TLS             | This repository                                            |
| Frappe Framework      | Users, permissions, workflows, audit, REST API       | Custom image                                               |
| ERPNext               | Accounting, selling, buying, projects, assets, stock | Installed app                                              |
| HRMS                  | Employees, leave, attendance, payroll, appraisals    | Installed app                                              |
| CRM                   | Leads, opportunities, activities and sales pipeline  | Installed app                                              |
| RundiNova application | Company-specific data, dashboards and controls       | `apps/rundinova_tech/` in this same self-hosted repository |
| Static website        | Marketing and public content                         | Existing website repository                                |

## Sites and offices

The first production site is the RundiNova company ERP site. Offices are
represented as ERPNext branches and cost centers, not as separate databases.
This keeps consolidated accounting and group reporting possible while still
allowing office-specific permissions and budgets.

Create separate Frappe sites only when there is a hard isolation requirement,
for example a legally independent entity or a customer-facing tenant. The
deployment already supports multiple hostnames and can be expanded later.

Recommended initial hostname:

- `erp.rundinova.com`: internal ERP and management platform

Potential later hostnames:

- `hr.rundinova.com`: dedicated HR entry point, if needed
- `crm.rundinova.com`: dedicated CRM entry point, if needed
- `office-name.rundinova.com`: isolated office or legal entity, if required

## Functional modules

The target platform includes these modules:

- Company and organization administration
- Human resources and employee records
- Recruitment, onboarding, leave and attendance
- Projects, tasks, milestones, timesheets and delivery
- CRM, leads, opportunities, quotations and contracts
- Accounting, budgets, cost centers, payments and reporting
- Procurement, suppliers, purchase orders and receipts
- Stock, assets, equipment and software subscriptions
- Communication, campaigns, events and community relations
- Innovation initiatives, ideas, experiments and partnerships
- Monthly operating budgets, including the food budget
- Executive dashboards and audit reporting

ERPNext, HRMS and CRM provide the standard processes. The RundiNova app must
provide only the company-specific objects and rules that should not be hidden
inside generic configuration.

## Progressive framework boundary

RundiNova owns its business rules even while Frappe owns the current database,
permissions, workflow engine, and web interface. Framework-independent rules
live in the separately installable `rundinova-core` package under
`apps/rundinova_tech/rundinova_core/` and operate on plain Python values.
Frappe DocType controllers act as adapters: they load and save records, apply
the caller's permissions, translate rule codes into localized messages, and
call the core functions. Core code must not import Frappe or issue database or
HTTP requests. The former nested `domain` import path remains as a compatibility
layer while adapters transition. Food-budget calculations, food-item progress
aggregation, food-purchase limits, food-expense policy validation, cash-movement
validation, account-balance arithmetic, general expense validation, document and decision governance,
asset controls, goal validation and progress, dashboard currency semantics,
and the food-purchase use case now use this boundary. Frappe adapters own
document reads, permission checks, role context, date conversion, and writes;
the food-expense policy port supplies period and aggregate snapshots while core
decides the applicable rules. The pure purchase service owns the
budget-item/progress relationship and expense command mapping. The Purchase
Invoice bridge also maps invoice
lines to food expenses and handles idempotent updates and cancellation through
a persistence port. Frappe continues to own the invoice and expense documents,
while the synchronization decisions and mapping are independently tested.
Automatic association of an expense with its budget/item progress record also
uses a core policy and a narrow Frappe lookup/create adapter.
Future modules can follow this boundary without changing existing DocTypes or
stored records.

## Security baseline

- Use a private production environment file; never commit credentials.
- Use HTTPS for every public hostname.
- Use role-based access rather than shared accounts.
- Require two-factor authentication for administrators.
- Restrict accounting, payroll and employee personal data by role and branch.
- Enable scheduled encrypted backups and test restoration regularly.
- Keep the public website and ERP deployment isolated at application level.
- Pin application versions and rebuild images deliberately during upgrades.
