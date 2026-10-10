# RundiNova Core

`rundinova-core` contains framework-independent rules for food budgets,
expenses, cash, governance and currencies. It has no Frappe, ERPNext, database
or network dependencies. The Frappe application adapts its documents to these
functions; the core package can be installed and tested on its own. The food
item progress aggregation (quantities, amounts, percentages, warning/over states
and remaining days) is also framework-independent and accepts date/value
snapshots from an adapter. Food-expense policy validation also runs here; its
port supplies budget periods and committed totals while the Frappe adapter
retains database and role access. The food purchase use case also lives here:
it defines the command, result, validation flow, and a persistence/permission
port. Frappe implements that port as an adapter, so the purchase orchestration
can be tested without a site or database.
The automatic expense-to-progress association is also a core use case: it keeps
an existing link, reuses a matching budget/item progress record, or asks the
adapter to create one. The adapter remains responsible for Frappe permissions
and persistence.
Supplier-invoice synchronization is another application use case. It maps
invoice lines to food-expense commands, updates an existing line idempotently,
and cancels linked expenses through a separate Frappe persistence adapter.

From the repository root:

```bash
python3 -m pip install --no-deps --target /tmp/rundinova-core-install \
  ./apps/rundinova_tech/rundinova_core
PYTHONPATH=/tmp/rundinova-core-install python3 -m unittest discover \
  -s apps/rundinova_tech/rundinova_core/tests -p 'test_*.py'
```

The old `rundinova_tech.rundinova_tech.domain` import path remains as a
compatibility layer while adapters migrate to `rundinova_core`.
