// Keep the browser tab branded on both website and every Desk route.
const rundinova_favicon =
  "/assets/rundinova_tech/images/rundinova-brand-favicon.svg";
const rundinova_brand_desk = () => {
  const links = [
    ...document.querySelectorAll(
      'link[rel~="icon"], link[rel="shortcut icon"]',
    ),
  ];
  if (!links.length) {
    const link = document.createElement("link");
    link.rel = "icon";
    document.head.appendChild(link);
    links.push(link);
  }
  links.forEach((link) => {
    link.href = rundinova_favicon;
  });

  const current = document.title.trim();
  if (!current) return;
  if (current.toLowerCase() === "login") {
    document.title = "RundiNova Tech · Connexion";
  } else if (
    current !== "RundiNova Tech" &&
    !current.startsWith("RundiNova Tech ·")
  ) {
    document.title = `RundiNova Tech · ${current}`;
  }
};

rundinova_brand_desk();
const rundinova_title_element = document.querySelector("title");
if (rundinova_title_element) {
  new MutationObserver(rundinova_brand_desk).observe(rundinova_title_element, {
    childList: true,
    characterData: true,
  });
}
const rundinova_frappe = window.frappe;
if (rundinova_frappe?.router) {
  rundinova_frappe.router.on("change", () =>
    requestAnimationFrame(rundinova_brand_desk),
  );
}
