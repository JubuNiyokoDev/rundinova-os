"""Resolve a food progress record for an expense through a persistence port."""

from typing import Protocol


class FoodProgressLinkPort(Protocol):
    """Persistence operations needed to attach a food progress record."""

    def find_progress(self, budget: str, item: str) -> str | None: ...

    def create_progress(self, budget: str, item: str) -> str: ...


def ensure_food_progress_link(
    budget: str | None,
    item: str | None,
    current_progress: str | None,
    port: FoodProgressLinkPort,
) -> str | None:
    """Keep an existing link, or find/create the record for this budget item."""
    if current_progress or not budget or not item:
        return current_progress

    progress = port.find_progress(budget, item)
    if progress:
        return progress
    return port.create_progress(budget, item)
