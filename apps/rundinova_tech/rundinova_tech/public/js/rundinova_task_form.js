frappe.ui.form.on("Task", {
  validate(frm) {
    // This is an audit field, not a task assignment: it records a human-readable
    // name in the list while Frappe keeps the technical email in modified_by.
    const user_info = frappe.boot.user_info?.[frappe.session.user] || {};
    frm.set_value("rundinova_last_updated_by", frappe.session.user);
    frm.set_value(
      "rundinova_last_updated_by_name",
      user_info.fullname || user_info.full_name || frappe.session.user,
    );
  },
});
