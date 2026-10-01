import frappe
from frappe import _
from frappe.model.document import Document


class RundiNovaKPISnapshot(Document):
    def validate(self):
        validate_snapshot(self)


def validate_snapshot(doc, _method=None):
    if not doc.period_start or not doc.period_end:
        frappe.throw(_("A KPI snapshot requires a start and end date."))

    if doc.period_end < doc.period_start:
        frappe.throw(_("The KPI period end cannot be before its start."))

    if doc.target_value is not None and doc.actual_value is not None:
        target = frappe.utils.flt(doc.target_value)
        actual = frappe.utils.flt(doc.actual_value)
        doc.target_achievement_percent = actual / target * 100 if target else 0
