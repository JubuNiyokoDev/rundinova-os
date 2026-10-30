frappe.listview_settings["RundiNova Document"] = {
  onload(listview) {
    // Keep legacy direct URLs useful while moving daily work into the library.
    if (!listview.page.__rundinova_document_library_redirect) {
      listview.page.__rundinova_document_library_redirect = true;
      frappe.set_route("rundinova-document-library");
    }
  },
};
