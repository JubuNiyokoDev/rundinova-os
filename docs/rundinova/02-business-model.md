---
title: RundiNova Tech Business Model
---

# RundiNova Tech Business Model

This is the implementation contract for the future `rundinova_tech` Frappe
application. It is intentionally separate from the static website repository.

## Organization master data

Configure the following in ERPNext:

- Company: `RundiNova Tech`
- Country: `Burundi`
- Primary location: `Gitega`
- Currency: `BIF` / FBU presentation
- Fiscal year: confirm the legal accounting year before production
- Default branch: `Gitega - Headquarters`
- Departments: Direction, Engineering, Communication, Community, Growth,
  Ecosystem and Administration
- Cost centers matching the departments and every future office

## Initial people

Create employee records with a unique employee number, work email, phone,
department, branch, manager, employment status, academic qualification and
professional qualification.

| Employee | Initial responsibility | Technical profile |
| --- | --- | --- |
| NIYONDIKO Joffre | Project Lead | Frontend and Mobile |
| IRAMBONA Elvis | Communication and Visibility Lead | Backend |
| Mandela KASUMBA Fanuel | Community and Social Relations Lead | Backend |
| MANIRANYIBUTSE Franck | Growth and Development Lead | Backend |
| NDABUBAHA Janvier | Ecosystem Lead | Frontend |
| To be registered | Housekeeping | Operational support |

The housekeeping employee participates in the food budget but must not be
granted access to confidential engineering, finance or HR records by default.

## RundiNova-specific DocTypes

The custom app should add these DocTypes:

| DocType | Purpose |
| --- | --- |
| RundiNova Office | Office, address, branch, timezone, manager and status |
| RundiNova Initiative | Innovation or ecosystem initiative with owners and outcomes |
| RundiNova Partnership | Partner, category, contacts, agreement and review dates |
| RundiNova Community Activity | Event or community activity with participants and impact |
| RundiNova Growth Opportunity | Growth source, owner, stage, value and next action |
| RundiNova Food Budget | Monthly approved food budget by office and cost center |
| RundiNova Food Budget Item | Item, category, quantity, unit, monthly amount and supplier |
| RundiNova Budget Review | Planned amount, actual amount, variance and approval |
| RundiNova Risk | Risk, impact, probability, owner, mitigation and status |
| RundiNova KPI Definition | KPI formula, owner, frequency and target |
| RundiNova KPI Snapshot | Periodic measured result and evidence |

## Food budget baseline

Create the first approved budget for the Gitega office:

- Period: monthly, recurring
- People covered: 6
- Contributors: 5 developers plus 1 housekeeping employee
- Approved monthly ceiling: `1,150,000 BIF`
- Annual planning value: `13,800,000 BIF`
- Planning daily value: approximately `38,333 BIF`
- Planning value per person per day: approximately `6,389 BIF`

The initial item values supplied by management are:

| Item | Category | Monthly amount (BIF) |
| --- | --- | ---: |
| Rice | Cereals | 145,000 |
| Bread | Cereals | 90,000 |
| Ubugari | Cereals | 33,000 |
| Spaghetti | Cereals | 22,000 |
| Sugar | Condiments | 22,000 |
| Salt | Condiments | 4,000 |
| Tomatoes and condiments | Condiments | 149,000 |
| Intore | Condiments | 45,000 |
| Potatoes | Vegetables | 112,000 |
| Igitoke | Vegetables | 89,000 |
| Irengarenga | Vegetables | 34,000 |
| Amakoto | Vegetables | 45,000 |
| Amashu | Vegetables | 34,000 |
| Beans | Proteins | 117,000 |
| Meat | Proteins | 89,000 |
| Amakara | Cereals | 120,000 |

The total must be validated during data import. A budget cannot be submitted
for approval when its item total exceeds the approved ceiling. Actual purchase
transactions must be linked to the budget, office and cost center so the
dashboard shows both committed and paid amounts.

## Roles and approval boundaries

Create separate roles for System Manager, Director, Finance Manager, HR
Manager, Project Manager, Engineering Lead, Communication Lead, Community
Lead, Growth Lead, Ecosystem Lead, Employee and Housekeeping Support.

Every spending workflow must record requester, approver, office, cost center,
supplier, amount, currency, supporting file and approval timestamp. Payroll,
employee personal data and accounting journals require stricter roles than
project or community records.
