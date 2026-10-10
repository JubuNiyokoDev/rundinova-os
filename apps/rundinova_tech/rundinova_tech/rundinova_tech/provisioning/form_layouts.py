"""Keep custom RundiNova records readable and grouped in the Desk form UI."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


# Each section is inserted after a stable fieldname. Custom Fields preserve
# these additions when Frappe re-syncs the standard DocType JSON on migrate.
_LAYOUTS = {
	"RundiNova Decision": [
		("Décision et contexte", "decision_title", "decision_context"),
		("Responsable et suivi", "decision_text", "decision_follow_up"),
	],
	"RundiNova Growth Opportunity": [
		("Prospect et qualification", "title", "opportunity_qualification"),
		("Valeur et prochaine action", "stage", "opportunity_next_action"),
	],
	"RundiNova KPI Definition": [
		("Définition de l’indicateur", "kpi_name", "kpi_definition"),
		("Cible et responsabilité", "formula", "kpi_target_owner"),
	],
	"RundiNova Goal": [
		("Objectif et responsabilité", "goal_title", "goal_details"),
		("Période et cible", "project", "goal_target"),
		("Progression et notes", "unit", "goal_progress"),
	],
	"RundiNova KPI Snapshot": [
		("Indicateur et période", "kpi_definition", "kpi_snapshot_period"),
		("Résultat et justificatifs", "period_end", "kpi_snapshot_result"),
	],
	"RundiNova Partnership": [
		("Partenaire", "partner_name", "partnership_identity"),
		("Relation et suivi", "contact", "partnership_follow_up"),
	],
	"RundiNova Risk": [
		("Risque et évaluation", "risk_title", "risk_assessment"),
		("Réduction et suivi", "impact", "risk_mitigation"),
	],
	"RundiNova Office": [
		("Bureau et localisation", "office_name", "office_location"),
		("Responsable et activité", "address", "office_management"),
	],
	"RundiNova Asset": [
		("Bien et acquisition", "asset_name", "asset_acquisition"),
		("Affectation et emplacement", "serial_number", "asset_assignment"),
		("Valeur et justificatifs", "location", "asset_evidence"),
	],
	"RundiNova Community Impact": [
		("Activité et communauté", "activity_name", "impact_activity"),
		("Résultats et justificatifs", "community", "impact_results"),
	],
	"RundiNova Cash Movement": [
		("Mouvement et montant", "movement_title", "cash_transaction"),
		("Origine et destination", "category", "cash_counterparties"),
		("Justificatifs et validation", "description", "cash_review"),
	],
	"RundiNova Budget Review": [
		("Période et budget", "review_period", "budget_review_scope"),
		("Montants et analyse", "budget", "budget_review_analysis"),
	],
	"RundiNova Expense": [
		("Dépense", "expense_title", "expense_details"),
		("Paiement et affectation", "description", "expense_payment"),
		("Validation", "receipt", "expense_review"),
	],
	"RundiNova Cash Account": [
		("Compte de trésorerie", "account_name", "cash_account_identity"),
		("Solde et suivi", "account_holder", "cash_account_balance"),
	],
	"RundiNova Document": [
		("Fichier et contexte", "document_title", "document_context"),
		("Accès et suivi", "expense", "document_governance"),
	],
}


_LABELS = {
	"RundiNova Decision": {
		"decision_title": "Décision", "decision_date": "Date", "decision_type": "Type",
		"meeting_reference": "Réunion ou référence", "decision_text": "Décision prise",
		"decision_owner": "Responsable", "follow_up_date": "Date de suivi",
		"action_task": "Tâche de suivi", "evidence": "Procès-verbal ou justificatif",
		"notes": "Notes",
	},
	"RundiNova Growth Opportunity": {
		"title": "Opportunité", "source": "Origine", "customer": "Client ou partenaire",
		"opportunity_owner": "Responsable", "stage": "Étape", "expected_value": "Valeur estimée (FBu)",
		"next_action": "Prochaine action", "next_action_date": "Date de la prochaine action",
	},
	"RundiNova KPI Definition": {
		"kpi_name": "Indicateur", "description": "Description", "formula": "Méthode de calcul",
		"unit": "Unité", "target_value": "Valeur cible", "kpi_owner": "Responsable",
		"frequency": "Fréquence de suivi", "active": "Actif",
	},
	"RundiNova Goal": {
		"goal_title": "Objectif", "goal_type": "Type d’objectif", "description": "Description",
		"goal_owner": "Responsable", "period_start": "Début de période", "period_end": "Fin de période",
		"target_value": "Cible", "current_value": "Valeur actuelle", "unit": "Unité",
		"achievement_percent": "Progression (%)", "status": "Statut", "notes": "Notes",
	},
	"RundiNova KPI Snapshot": {
		"kpi_definition": "Indicateur", "period_start": "Début de période", "period_end": "Fin de période",
		"target_value": "Valeur cible", "actual_value": "Valeur réalisée",
		"target_achievement_percent": "Objectif atteint (%)", "evidence": "Justificatif", "notes": "Notes",
	},
	"RundiNova Partnership": {
		"partner_name": "Partenaire", "partner_type": "Type de partenaire", "contact": "Contact principal",
		"relationship_owner": "Responsable de la relation", "start_date": "Début de la relation",
		"review_date": "Date de révision", "agreement": "Accord ou convention", "status": "Statut",
	},
	"RundiNova Risk": {
		"risk_title": "Risque", "area": "Domaine", "risk_owner": "Responsable",
		"probability": "Probabilité", "impact": "Impact", "mitigation": "Mesure d’atténuation",
		"review_date": "Prochaine révision", "status": "Statut",
	},
	"RundiNova Office": {
		"office_name": "Nom du bureau", "branch": "Agence ERPNext", "cost_center": "Centre de coûts",
		"address": "Adresse", "timezone": "Fuseau horaire", "manager": "Responsable du bureau",
		"active": "Actif",
	},
	"RundiNova Asset": {
		"asset_name": "Nom du bien", "asset_type": "Type de bien", "status": "Statut",
		"serial_number": "Numéro de série", "assigned_to": "Attribué à", "project": "Projet",
		"purchase_date": "Date d’acquisition", "purchase_amount": "Valeur d’acquisition (FBu)",
		"current_value": "Valeur actuelle (FBu)", "supplier": "Fournisseur", "receipt": "Justificatif d’achat",
		"location": "Emplacement", "notes": "Notes",
	},
	"RundiNova Community Impact": {
		"activity_name": "Activité", "activity_date": "Date de l’activité", "office": "Bureau",
		"community": "Communauté ou groupe", "participants": "Participants", "beneficiaries": "Bénéficiaires",
		"outcome": "Résultat obtenu", "evidence": "Justificatif", "status": "Statut",
	},
	"RundiNova Cash Movement": {
		"movement_title": "Mouvement de trésorerie", "movement_date": "Date", "movement_type": "Type de mouvement",
		"account": "Compte source", "destination_account": "Compte destinataire", "amount": "Montant (FBu)",
		"category": "Catégorie", "source_type": "Type d’origine", "source_description": "Origine",
		"destination_type": "Type de destination", "destination_description": "Destination",
		"description": "Description", "expense": "Dépense liée", "food_expense": "Achat alimentaire lié",
		"project": "Projet", "evidence": "Justificatif", "status": "Statut", "approved_by": "Validé par",
	},
	"RundiNova Budget Review": {
		"review_period": "Période examinée", "branch": "Bureau ou agence", "budget": "Budget alimentaire",
		"planned_amount": "Montant prévu (FBu)", "committed_amount": "Montant engagé (FBu)",
		"actual_amount": "Montant dépensé (FBu)", "variance_amount": "Écart (FBu)", "review_notes": "Analyse et décisions",
	},
	"RundiNova Expense": {
		"expense_title": "Dépense", "expense_date": "Date de la dépense", "category": "Catégorie",
		"description": "Description", "amount": "Montant (FBu)", "paid_by": "Payé par",
		"payment_method": "Mode de paiement", "supplier": "Fournisseur", "project": "Projet",
		"cost_center": "Centre de coûts", "receipt": "Reçu ou justificatif", "status": "Statut",
		"approved_by": "Validé par", "approval_notes": "Note de validation",
	},
	"RundiNova Cash Account": {
		"account_name": "Nom du compte", "account_type": "Type de compte", "currency": "Devise",
		"account_holder": "Titulaire du compte", "opening_balance": "Solde initial",
		"current_balance": "Solde actuel", "opening_date": "Date d’ouverture", "status": "Statut", "notes": "Notes",
	},
	"RundiNova Document": {
		"document_title": "Document", "document_type": "Type de document", "file": "Fichier",
		"project": "Projet", "decision": "Décision liée", "expense": "Dépense liée",
		"document_owner": "Responsable", "confidentiality": "Confidentialité",
		"document_date": "Date du document", "review_date": "Date de révision",
		"status": "Statut", "notes": "Notes",
	},
}


def sync_form_layouts():
	"""Add persistent section dividers and user-facing French field labels."""
	custom_fields = {}
	for doctype, sections in _LAYOUTS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		custom_fields[doctype] = [
			{
				"fieldname": f"custom_rn_section_{fieldname}",
				"label": label,
				"fieldtype": "Section Break",
				"insert_after": anchor,
				"collapsible": 0,
			}
			for label, anchor, fieldname in sections
		]
	create_custom_fields(custom_fields, update=True)

	updated_labels = 0
	for doctype, labels in _LABELS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		for fieldname, label in labels.items():
			field = frappe.db.get_value("DocField", {"parent": doctype, "fieldname": fieldname}, "name")
			if not field:
				continue
			frappe.db.set_value("DocField", field, "label", label, update_modified=False)
			updated_labels += 1
		frappe.clear_cache(doctype=doctype)
	return {"doctypes": len(custom_fields), "labels": updated_labels}
