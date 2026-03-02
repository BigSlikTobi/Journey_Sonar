"""Score cascading logic: child node scores roll up to parent nodes.

Parent scores are volume-weighted averages of their children's scores,
so high-traffic children have more influence on the parent score.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChildScore:
    node_id: str
    score: float
    signal_volume: int  # Total signals at this node (used as weight)


def cascade_scores(children: list[ChildScore]) -> float:
    """Compute a parent node's score from its children using volume-weighted average.

    Children with more signals (higher traffic) have proportionally more
    influence on the parent score.

    Returns the computed parent score (0-100).
    """
    if not children:
        return 50.0  # Neutral if no children

    total_volume = sum(c.signal_volume for c in children)

    if total_volume == 0:
        # Equal weight if no signals anywhere
        return sum(c.score for c in children) / len(children)

    weighted_sum = sum(c.score * c.signal_volume for c in children)
    return round(weighted_sum / total_volume, 2)
