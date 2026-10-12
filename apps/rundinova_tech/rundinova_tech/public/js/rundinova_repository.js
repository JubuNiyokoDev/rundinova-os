frappe.ui.form.on("RundiNova Repository", {
  refresh(frm) {
    if (frm.is_new() || !frm.doc.github_url) return;
    const can_review = ["RundiNova Director", "RundiNova Project Lead"].some(
      (role) => frappe.user.has_role(role),
    );
    if (!can_review) return;
    const owner = frm.doc.github_url.split("/").filter(Boolean).at(-2);

    if (frappe.user.has_role("RundiNova Director") && owner) {
      frm.add_custom_button(
        __("Analyser tous les dépôts de {0}", [owner]),
        () => {
          frappe.confirm(
            __(
              "Les noms, descriptions et fichiers source textuels de tous les dépôts accessibles à l’installation GitHub {0} seront envoyés à Google Gemini. L’analyse sera mise en file d’attente; aucun dépôt, issue, tâche ou code ne sera modifié. Continuer ?",
              [owner],
            ),
            () => {
              frappe.call({
                method: "rundinova_tech.api.analyze_github_account",
                args: { owner },
                freeze: true,
                freeze_message: __("Chargement des dépôts GitHub…"),
                callback(response) {
                  const count = response.message?.repository_count || 0;
                  const running = response.message?.already_running || 0;
                  frappe.msgprint(
                    __(
                      "{0} dépôt(s) mis en file. {1} déjà en cours. L’état et le rapport apparaîtront sur chaque fiche.",
                      [count, running],
                    ),
                  );
                },
              });
            },
          );
        },
        __("RundiNova AI"),
      );
    }

    frm.add_custom_button(
      __("Analyser avec l’IA"),
      () => {
        frappe.confirm(
          __(
            "Le code textuel retenu du dépôt sera envoyé à Google Gemini pour produire une analyse et une recherche de marché. Aucune tâche ou modification GitHub ne sera créée. Continuer ?",
          ),
          () => {
            frappe.call({
              method: "rundinova_tech.api.analyze_repository",
              args: { repository_name: frm.doc.name },
              freeze: true,
              freeze_message: __("Analyse du dépôt et du marché en cours…"),
              callback(response) {
                if (!response.message) return;
                frm.reload_doc();
                frappe.msgprint({
                  title: __("Analyse terminée — validation humaine requise"),
                  message: frappe.utils.escape_html(
                    response.message.executive_summary || "Rapport enregistré.",
                  ),
                  indicator: "green",
                });
              },
            });
          },
        );
      },
      __("RundiNova AI"),
    );
  },
});
