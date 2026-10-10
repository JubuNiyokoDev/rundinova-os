const derivedFields = [
	"movement_date",
	"movement_type",
	"destination_account",
	"amount",
	"category",
	"source_type",
	"source_description",
	"destination_type",
	"destination_description",
	"description",
	"expense",
];

function setDerivedFieldsReadOnly(frm) {
	derivedFields.forEach((fieldname) => {
		frm.set_df_property(fieldname, "read_only", Boolean(frm.doc.food_expense));
	});
}

frappe.ui.form.on("RundiNova Cash Movement", {
	refresh(frm) {
		setDerivedFieldsReadOnly(frm);
	},

	food_expense(frm) {
		setDerivedFieldsReadOnly(frm);
		if (!frm.doc.food_expense) {
			frm.refresh_fields();
			return;
		}

		const selectedExpense = frm.doc.food_expense;
		frappe.db.get_doc("RundiNova Food Expense", selectedExpense).then((expense) => {
			if (frm.doc.food_expense !== selectedExpense) return;

			const quantity = expense.quantity ? `${expense.quantity} ${expense.unit || ""} ` : "";
			const values = {
				movement_date: expense.expense_date,
				movement_type: "Expense",
				destination_account: null,
				amount: expense.amount,
				category: expense.category || "Food",
				source_type: null,
				source_description: null,
				destination_type: expense.supplier ? "Supplier" : "Expense",
				destination_description: expense.supplier || expense.item,
				description: `Food purchase: ${quantity}${expense.item || "Food purchase"}`,
				expense: null,
			};
			if (!frm.doc.evidence && expense.receipt) values.evidence = expense.receipt;

			Promise.all(
				Object.entries(values).map(([fieldname, value]) => frm.set_value(fieldname, value))
			).then(() => frm.refresh_fields());
		});
	},
});
