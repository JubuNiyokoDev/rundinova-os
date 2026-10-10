"""Frappe persistence adapter for automatic food progress linking."""

import frappe


class FrappeFoodProgressLinkPort:
	"""Preserve the expense controller's query and controlled-create behavior."""

	def find_progress(self, budget, item):
		progress = frappe.get_all(
			"RundiNova Food Progress",
			filters={"budget": budget, "item": item},
			fields=["name"],
		)
		return progress[0].name if progress else None

	def create_progress(self, budget, item):
		doc = frappe.get_doc(
			{
				"doctype": "RundiNova Food Progress",
				"budget": budget,
				"item": item,
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name
