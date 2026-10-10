import frappe

# Update company currency
company = frappe.get_doc("Company", "RundiNova Tech")
company.default_currency = "BIF"
company.symbol = "FBu"
company.save()
print(f"Currency updated: {company.default_currency} - {company.symbol}")
