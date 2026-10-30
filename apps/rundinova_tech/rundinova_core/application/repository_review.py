"""Framework-independent validation for AI repository review reports."""

INSUFFICIENT_EVIDENCE_SUMMARY = (
    "Le modèle n’a pas fourni de preuves vérifiables liées aux fichiers scannés. "
    "Ne pas utiliser ce résumé pour juger la maturité ou la capacité de vente; "
    "relancer l’analyse après correction du format des preuves."
)

INSUFFICIENT_MARKET_RESEARCH = (
    "Aucune recherche Web externe vérifiable n’a été fournie par cette analyse. "
    "Ne pas traiter les affirmations de marché comme des faits; les clients cibles "
    "restent des hypothèses à valider."
)


def prepare_repository_review(report, source_context, web_sources):
    """Normalize claims against scanned files and mark unsupported conclusions."""
    result = dict(report)
    result["evidence"] = _verified_evidence(report, source_context)
    evidence_paths = {item["source_path"] for item in result["evidence"]}
    evidence_is_sufficient = len(result["evidence"]) >= 3 and len(evidence_paths) >= 2
    result["analysis_quality"] = (
        "evidence_linked" if evidence_is_sufficient else "insufficient_evidence"
    )
    if not evidence_is_sufficient:
        result["executive_summary"] = INSUFFICIENT_EVIDENCE_SUMMARY
        result["readiness_score"] = None
        result["sales_verdict"] = "À évaluer — preuves insuffisantes"
        result["completed_capabilities"] = []

    result["web_sources"] = list(web_sources or [])
    result["market_research_status"] = (
        "grounded_sources_available" if result["web_sources"] else "not_performed"
    )
    if not result["web_sources"]:
        result["market_opportunity"] = INSUFFICIENT_MARKET_RESEARCH
    return result


def _verified_evidence(report, source_context):
    """Keep only evidence excerpts that exactly match files included in the scan."""
    files = {
        entry.get("path"): " ".join(entry.get("content", "").split()).casefold()
        for entry in source_context.get("files", [])
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }
    evidence = report.get("evidence")
    if not isinstance(evidence, list):
        return []

    verified = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        path = item.get("source_path")
        excerpt = item.get("excerpt")
        claim = item.get("claim")
        if not all(
            isinstance(value, str) and value.strip() for value in (path, excerpt, claim)
        ):
            continue
        normalized_excerpt = " ".join(excerpt.split()).casefold()
        if len(normalized_excerpt) < 24 or normalized_excerpt not in files.get(
            path, ""
        ):
            continue
        verified.append(
            {"claim": claim.strip(), "source_path": path, "excerpt": excerpt.strip()}
        )
    return verified
