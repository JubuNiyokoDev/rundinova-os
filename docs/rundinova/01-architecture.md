---
title: RundiNova Tech ERP Architecture
---

# RundiNova Tech ERP Architecture

This document defines the target operating platform for RundiNova Tech. The
public static website remains a separate project. The ERP is exposed through
one or more subdomains such as `erp.rundinova.com`.

## Platform layers

| Layer | Responsibility | Initial implementation |
| --- | --- | --- |
| Docker infrastructure | Containers, networking, persistence, TLS | This repository |
| Frappe Framework | Users, permissions, workflows, audit, REST API | Custom image |
| ERPNext | Accounting, selling, buying, projects, assets, stock | Installed app |
| HRMS | Employees, leave, attendance, payroll, appraisals | Installed app |
| CRM | Leads, opportunities, activities and sales pipeline | Installed app |
| RundiNova application | Company-specific data, dashboards and controls | Separate Frappe app repository |
| Static website | Marketing and public content | Existing website repository |

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

## Security baseline

- Use a private production environment file; never commit credentials.
- Use HTTPS for every public hostname.
- Use role-based access rather than shared accounts.
- Require two-factor authentication for administrators.
- Restrict accounting, payroll and employee personal data by role and branch.
- Enable scheduled encrypted backups and test restoration regularly.
- Keep the public website and ERP deployment isolated at application level.
- Pin application versions and rebuild images deliberately during upgrades.
