// Frappe opens a Form in edit mode when the user has write access. RundiNova
// uses a safer detail-first interaction: read a record first, then explicitly
// enter edit mode. New records remain editable so creation stays fast.
const rundinovaDetailDoctypes = [
  "Project",
  "Task",
  "Employee",
  "RundiNova Decision",
  "RundiNova Expense",
  "RundiNova Budget Review",
  "RundiNova Cash Account",
  "RundiNova Cash Movement",
  "RundiNova Food Budget",
  "RundiNova Food Expense",
  "RundiNova Food Progress",
  "RundiNova Daily Update",
  "RundiNova Repository",
  "RundiNova Document",
  "RundiNova Document Folder",
  "RundiNova Goal",
  "RundiNova KPI Definition",
  "RundiNova KPI Snapshot",
  "RundiNova Partnership",
  "RundiNova Growth Opportunity",
  "RundiNova Community Impact",
  "RundiNova Risk",
  "RundiNova Asset",
  "RundiNova Office",
];

const rundinovaNonInputFields = new Set([
  "Section Break",
  "Column Break",
  "Tab Break",
  "HTML",
  "Heading",
  "Button",
  "Fold",
]);

function rundinovaSetFieldsReadOnly(frm, readOnly) {
  frm.__rundinova_original_read_only ||= {};
  (frm.meta.fields || []).forEach((df) => {
    if (!df.fieldname || rundinovaNonInputFields.has(df.fieldtype)) return;
    if (!(df.fieldname in frm.__rundinova_original_read_only)) {
      frm.__rundinova_original_read_only[df.fieldname] = Boolean(df.read_only);
    }
    frm.set_df_property(
      df.fieldname,
      "read_only",
      readOnly ? 1 : Number(frm.__rundinova_original_read_only[df.fieldname]),
    );
  });
}

function rundinovaCanEdit(frm) {
  return (frm.perm || []).some((permission) => Boolean(permission.write));
}

function rundinovaEnableEditMode(frm) {
  frm.__rundinova_edit_mode = true;
  rundinovaSetFieldsReadOnly(frm, false);
  frm.enable_save();
  frm.set_intro(__("Mode modification — enregistrez vos changements une fois terminés."), "blue");
}

function rundinovaEnableDetailMode(frm) {
  if (frm.is_new()) {
    frm.__rundinova_edit_mode = true;
    rundinovaSetFieldsReadOnly(frm, false);
    frm.enable_save();
    return;
  }
  if (frm.__rundinova_edit_mode) return;

  rundinovaSetFieldsReadOnly(frm, true);
  frm.disable_save();
  frm.set_intro(
    __("Mode lecture — consultez les informations puis utilisez « Modifier » pour les changer."),
    "blue",
  );
  if (rundinovaCanEdit(frm) && !frm.page.__rundinova_edit_button) {
    frm.page.__rundinova_edit_button = true;
    frm.add_custom_button(__("Modifier"), () => rundinovaEnableEditMode(frm), __("Actions"));
  }
}

rundinovaDetailDoctypes.forEach((doctype) => {
  frappe.ui.form.on(doctype, {
    refresh(frm) {
      rundinovaEnableDetailMode(frm);
    },
  });
});
