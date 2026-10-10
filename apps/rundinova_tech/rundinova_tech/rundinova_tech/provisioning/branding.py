"""Keep the self-hosted Desk and website identity on RundiNova branding."""

import frappe


def sync_branding():
	logo = "/assets/rundinova_tech/images/rundinova-logo-wide.svg"
	favicon = "/assets/rundinova_tech/images/rundinova-brand-favicon.svg"
	frappe.db.set_single_value("System Settings", "app_name", "RundiNova Tech")
	frappe.db.set_single_value("Website Settings", "app_name", "RundiNova Tech")
	frappe.db.set_single_value("Website Settings", "favicon", favicon)
	frappe.db.set_single_value("Navbar Settings", "app_logo", logo)
	cleaned_field_descriptions = 0
	_titles = {
		"RundiNova Food Budget": "budget_title",
		"RundiNova Food Progress": "progress_title",
		"RundiNova Food Expense": "expense_title",
		"RundiNova Growth Opportunity": "title",
		"RundiNova KPI Definition": "kpi_name",
		"RundiNova KPI Snapshot": "kpi_definition",
		"RundiNova Partnership": "partner_name",
		"RundiNova Risk": "risk_title",
		"RundiNova Office": "office_name",
		"RundiNova Community Impact": "activity_name",
		"RundiNova Budget Review": "review_period",
	}
	for doctype in frappe.get_all("DocType", filters={"module": "RundiNova Tech"}, pluck="name"):
		meta = frappe.get_meta(doctype)
		title_field = _titles.get(doctype) or meta.title_field
		if title_field and meta.has_field(title_field):
			frappe.db.set_value(
				"DocType", doctype,
				{"title_field": title_field, "show_title_field_in_link": 1},
				update_modified=False,
			)
		# Old provisioning runs copied machine fieldnames into descriptions, so
		# users saw values such as "expense_date" under ordinary field labels.
		for field in frappe.get_all(
			"DocField",
			filters={"parent": doctype},
			fields=["name", "fieldname", "description"],
		):
			if field.description and field.description.strip() == field.fieldname:
				frappe.db.set_value("DocField", field.name, "description", "", update_modified=False)
				cleaned_field_descriptions += 1
		frappe.clear_cache(doctype=doctype)
	for name in frappe.get_all("RundiNova Food Progress", pluck="name"):
		doc = frappe.get_doc("RundiNova Food Progress", name)
		from rundinova_tech.rundinova_tech.doctype.rundinova_food_progress.rundinova_food_progress import set_progress_title

		set_progress_title(doc)
		frappe.db.set_value("RundiNova Food Progress", name, "progress_title", doc.progress_title, update_modified=False)
	from rundinova_tech.rundinova_tech.doctype.rundinova_food_expense.rundinova_food_expense import set_expense_title
	for name in frappe.get_all("RundiNova Food Expense", pluck="name"):
		doc = frappe.get_doc("RundiNova Food Expense", name)
		set_expense_title(doc)
		frappe.db.set_value("RundiNova Food Expense", name, "expense_title", doc.expense_title, update_modified=False)
	frappe.clear_cache()
	return {
		"app_name": "RundiNova Tech",
		"favicon": favicon,
		"logo": logo,
		"readable_doctypes": len(_titles) + 2,
		"cleaned_field_descriptions": cleaned_field_descriptions,
	}
