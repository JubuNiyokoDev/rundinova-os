"""Initial company and ERPNext warehouse setup."""

import frappe

COMPANY_NAME = "RundiNova Tech"
COMPANY_ABBR = "RNT"

# Company defaults for the initial RundiNova installation.


def ensure_transit_warehouse_type():
    if frappe.db.exists("Warehouse Type", "Transit"):
        return "already-exists"
    doc = frappe.get_doc(
        {
            "doctype": "Warehouse Type",
            "name": "Transit",
            "description": "Goods in transit",
        }
    )
    doc.flags.name_set = True
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return "created"


def ensure_company():
    if frappe.db.exists("Company", COMPANY_NAME):
        company = frappe.get_doc("Company", COMPANY_NAME)
        company.flags.ignore_mandatory = True
        company.save(ignore_permissions=True)
        frappe.db.commit()
        return "already-exists"

    company = frappe.new_doc("Company")
    company.company_name = COMPANY_NAME
    company.abbr = COMPANY_ABBR
    company.country = "Burundi"
    company.default_currency = "BIF"
    company.enable_perpetual_inventory = 1
    company.flags.ignore_mandatory = True
    company.insert(ignore_permissions=True)
    frappe.db.commit()
    return "created"
