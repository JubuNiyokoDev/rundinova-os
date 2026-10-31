frappe.pages["rundinova-document-library"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Documents & fichiers"),
    single_column: true,
  });
  const state = { folder: null, search: "", document_type: "", project: "", view: "grid" };

  const escape = (value) => $("<div>").text(value || "").html();
  const extension = (file) => (file || "").split(".").pop().toLowerCase();
  const iconFor = (file) => {
    const ext = extension(file);
    if (["png", "jpg", "jpeg", "gif", "webp"].includes(ext)) return "image";
    if (ext === "pdf") return "file-pdf";
    if (["doc", "docx"].includes(ext)) return "file-word";
    if (["xls", "xlsx", "csv"].includes(ext)) return "file-excel";
    return "file";
  };
  const canPreview = (file) => ["pdf", "png", "jpg", "jpeg", "gif", "webp"].includes(extension(file));

  $(page.body).html(`
    <style>
      .rn-library { max-width: 1440px; margin: 0 auto; padding: 8px 0 30px; }
      .rn-library-toolbar { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin:0 0 16px; }
      .rn-library-search { flex:1 1 260px; min-width:220px; }
      .rn-library-search input { border-radius:8px; height:38px; }
      .rn-library-select { min-width:160px; height:38px; border:1px solid var(--border-color); border-radius:8px; padding:0 10px; background:var(--fg-color); }
      .rn-library-breadcrumb { display:flex; gap:7px; align-items:center; flex-wrap:wrap; min-height:28px; margin-bottom:12px; color:var(--text-muted); font-size:13px; }
      .rn-library-breadcrumb button { border:0; background:transparent; color:var(--primary); padding:0; }
      .rn-library-summary { color:var(--text-muted); font-size:13px; margin:0 0 12px; }
      .rn-library-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:12px; }
      .rn-library-card { background:var(--card-bg); border:1px solid var(--border-color); border-radius:12px; min-height:154px; padding:14px; position:relative; transition:box-shadow .16s,border-color .16s; }
      .rn-library-card:hover { border-color:var(--primary); box-shadow:0 6px 18px rgba(0,0,0,.08); }
      .rn-library-card button.rn-open { display:block; width:100%; text-align:left; border:0; background:transparent; padding:0; color:inherit; }
      .rn-library-card .rn-icon { color:var(--primary); font-size:28px; margin-bottom:14px; }
      .rn-library-card.document .rn-icon { color:#78849a; }
      .rn-library-name { font-size:14px; font-weight:600; line-height:1.35; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
      .rn-library-meta { color:var(--text-muted); font-size:12px; margin-top:7px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .rn-library-actions { position:absolute; top:8px; right:8px; display:flex; gap:4px; }
      .rn-library-actions button { border:0; background:transparent; color:var(--text-muted); padding:4px; border-radius:5px; }
      .rn-library-actions button:hover { background:var(--control-bg); color:var(--primary); }
      .rn-library-list { border:1px solid var(--border-color); border-radius:10px; overflow:hidden; }
      .rn-library-row { display:grid; grid-template-columns:36px minmax(200px,2fr) minmax(120px,1fr) minmax(110px,1fr) 76px; gap:12px; align-items:center; padding:11px 14px; border-bottom:1px solid var(--border-color); }
      .rn-library-row:last-child { border-bottom:0; }
      .rn-library-row:hover { background:var(--subtle-fg); }
      .rn-library-row .rn-row-name { border:0; background:transparent; text-align:left; padding:0; color:inherit; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .rn-library-empty { border:1px dashed var(--border-color); border-radius:12px; text-align:center; padding:52px 20px; color:var(--text-muted); }
      @media (max-width: 720px) { .rn-library-row { grid-template-columns:30px minmax(0,1fr) 34px; } .rn-library-row .rn-hide-mobile { display:none; } }
    </style>
    <div class="rn-library">
      <div class="rn-library-toolbar">
        <button class="btn btn-default btn-sm rn-root"><i class="fa fa-home"></i> Racine</button>
        <button class="btn btn-default btn-sm rn-refresh" title="Actualiser la bibliothèque"><i class="fa fa-refresh"></i></button>
        <div class="rn-library-search input-with-feedback"><input class="form-control rn-search" placeholder="Rechercher un dossier ou un document"></div>
        <select class="rn-library-select rn-type"><option value="">Tous les types</option></select>
        <select class="rn-library-select rn-project"><option value="">Tous les projets</option></select>
        <button class="btn btn-default btn-sm rn-view" title="Changer de vue"><i class="fa fa-th-large"></i></button>
        <button class="btn btn-default btn-sm rn-folder"><i class="fa fa-folder-o"></i> Nouveau dossier</button>
        <button class="btn btn-primary btn-sm rn-upload"><i class="fa fa-upload"></i> Ajouter un fichier</button>
      </div>
      <div class="rn-library-breadcrumb"></div>
      <div class="rn-library-summary"></div>
      <div class="rn-library-content"></div>
    </div>
  `);

  const $body = $(page.body);
  const renderBreadcrumbs = (breadcrumbs) => {
    const $crumbs = $body.find(".rn-library-breadcrumb").empty();
    $("<button>").text("Bibliothèque").on("click", () => openFolder(null)).appendTo($crumbs);
    breadcrumbs.forEach((crumb) => {
      $("<span>").text("/").appendTo($crumbs);
      $("<button>").text(crumb.label).on("click", () => openFolder(crumb.name)).appendTo($crumbs);
    });
  };

  const preview = (document) => {
    if (!document.file) return;
    if (!canPreview(document.file)) return window.open(document.file, "_blank", "noopener");
    const dialog = new frappe.ui.Dialog({ title: document.document_title, size: "extra-large", fields: [{ fieldtype: "HTML", fieldname: "preview" }] });
    dialog.show();
    const $target = dialog.get_field("preview").$wrapper.empty();
    if (extension(document.file) === "pdf") {
      $("<iframe>", { src: document.file, css: { width: "100%", height: "70vh", border: 0 } }).appendTo($target);
    } else {
      $("<img>", { src: document.file, css: { maxWidth: "100%", maxHeight: "70vh", display: "block", margin: "0 auto" } }).appendTo($target);
    }
  };

  const render = (data) => {
    const folders = data.folders || [];
    const documents = data.documents || [];
    renderBreadcrumbs(data.breadcrumbs || []);
    $body.find(".rn-library-summary").text(`${folders.length} dossier(s) · ${documents.length} document(s)`);
    const $content = $body.find(".rn-library-content").empty();
    if (!folders.length && !documents.length) {
      $content.html('<div class="rn-library-empty"><i class="fa fa-folder-open-o fa-2x"></i><p class="mt-3 mb-1">Cet emplacement est vide.</p><small>Créez un dossier ou ajoutez un fichier pour commencer.</small></div>');
      return;
    }
    const entries = [
      ...folders.map((folder) => ({ kind: "folder", ...folder })),
      ...documents.map((document) => ({ kind: "document", ...document })),
    ];
    if (state.view === "grid") {
      const $grid = $("<div class='rn-library-grid'></div>").appendTo($content);
      entries.forEach((entry) => {
        const folder = entry.kind === "folder";
        const $card = $(`<div class="rn-library-card ${folder ? "folder" : "document"}"></div>`).appendTo($grid);
        $("<button class='rn-open'></button>").append(`<div class="rn-icon"><i class="fa fa-${folder ? "folder" : iconFor(entry.file)}"></i></div><div class="rn-library-name">${escape(folder ? entry.folder_name : entry.document_title)}</div><div class="rn-library-meta">${escape(folder ? (entry.project || "Dossier partagé") : (entry.document_type || "Document"))}</div>`).on("click", () => folder ? openFolder(entry.name) : preview(entry)).appendTo($card);
        if (!folder) {
          const $actions = $("<div class='rn-library-actions'></div>").appendTo($card);
          $("<button title='Aperçu'><i class='fa fa-eye'></i></button>").on("click", () => preview(entry)).appendTo($actions);
          $("<button title='Télécharger'><i class='fa fa-download'></i></button>").on("click", () => window.open(entry.file, "_blank", "noopener")).appendTo($actions);
        }
      });
      return;
    }
    const $list = $("<div class='rn-library-list'></div>").appendTo($content);
    entries.forEach((entry) => {
      const folder = entry.kind === "folder";
      const $row = $("<div class='rn-library-row'></div>").appendTo($list);
      $row.append(`<i class="fa fa-${folder ? "folder" : iconFor(entry.file)} text-muted"></i>`);
      $("<button class='rn-row-name'></button>").text(folder ? entry.folder_name : entry.document_title).on("click", () => folder ? openFolder(entry.name) : preview(entry)).appendTo($row);
      $row.append(`<span class="rn-hide-mobile text-muted">${escape(folder ? (entry.project || "Dossier partagé") : (entry.document_type || "Document"))}</span>`);
      $row.append(`<span class="rn-hide-mobile text-muted">${escape(folder ? "Dossier" : (entry.document_date || ""))}</span>`);
      const $actions = $("<span class='rn-library-actions position-static'></span>").appendTo($row);
      if (!folder) $("<button title='Aperçu'><i class='fa fa-eye'></i></button>").on("click", () => preview(entry)).appendTo($actions);
    });
  };

  const load = async () => {
    $body.find(".rn-library-content").html('<div class="text-muted p-4"><i class="fa fa-spinner fa-spin"></i> Chargement de la bibliothèque…</div>');
    const response = await frappe.call({ method: "rundinova_tech.rundinova_tech.document_library.get_library", args: { folder: state.folder, search: state.search, document_type: state.document_type, project: state.project } });
    const data = response.message;
    const $projects = $body.find(".rn-project");
    if (!$projects.data("loaded")) {
      data.projects.forEach((project) => $("<option>", { value: project.name, text: project.project_name || project.name }).appendTo($projects));
      $projects.data("loaded", true);
    }
    render(data);
  };
  const openFolder = (folder) => { state.folder = folder; state.search = ""; $body.find(".rn-search").val(""); load(); };

  const createFolder = () => {
    const dialog = new frappe.ui.Dialog({
      title: __("Nouveau dossier"),
      fields: [
        { fieldname: "folder_name", label: "Nom du dossier", fieldtype: "Data", reqd: 1 },
        { fieldname: "project", label: "Projet (facultatif)", fieldtype: "Link", options: "Project" },
      ],
      primary_action_label: __("Créer"),
      primary_action: async (values) => {
        dialog.disable_primary_action();
        try {
          const response = await frappe.call({
            method: "rundinova_tech.rundinova_tech.document_library.create_folder",
            args: { ...values, parent_folder: state.folder },
          });
          dialog.hide();
          const result = response.message || {};
          frappe.show_alert({
            message: result.created === false ? (result.message || __("Dossier déjà présent")) : __("Dossier créé"),
            indicator: result.created === false ? "orange" : "green",
          });
          await load();
        } catch (error) {
          dialog.enable_primary_action();
          throw error;
        }
      },
    });
    dialog.show();
  };

  const upload = () => frappe.prompt([
    { fieldname: "document_title", label: "Titre du document", fieldtype: "Data" },
    { fieldname: "document_type", label: "Type de document", fieldtype: "Select", reqd: 1, options: "Contrat\nFacture\nReçu\nRapport\nModèle\nProcès-verbal\nPolitique\nDocument juridique\nSpécification technique\nLivrable\nImage\nVidéo\nAutre" },
    { fieldname: "project", label: "Projet (facultatif)", fieldtype: "Link", options: "Project", default: state.project || "" },
    { fieldname: "notes", label: "Notes / contexte", fieldtype: "Small Text" },
  ], (values) => new frappe.ui.FileUploader({
    allow_multiple: false,
    is_private: 1,
    on_success: async (file) => {
      await frappe.call({ method: "rundinova_tech.rundinova_tech.document_library.create_document", args: { ...values, document_title: values.document_title || file.file_name, file_url: file.file_url, folder: state.folder } });
      frappe.show_alert({ message: __("Document ajouté à la bibliothèque"), indicator: "green" });
      load();
    },
  }), __("Ajouter un fichier"), __("Choisir le fichier"));

  let timer;
  $body.find(".rn-search").on("input", function () { clearTimeout(timer); timer = setTimeout(() => { state.search = this.value.trim(); load(); }, 280); });
  $body.find(".rn-root").on("click", () => openFolder(null));
  $body.find(".rn-refresh").on("click", load);
  $body.find(".rn-type").on("change", function () { state.document_type = this.value; load(); });
  $body.find(".rn-project").on("change", function () { state.project = this.value; load(); });
  $body.find(".rn-view").on("click", () => { state.view = state.view === "grid" ? "list" : "grid"; $body.find(".rn-view i").attr("class", `fa fa-${state.view === "grid" ? "th-large" : "list"}`); load(); });
  $body.find(".rn-folder").on("click", createFolder);
  $body.find(".rn-upload").on("click", upload);
  load();
};
