"""Career-readiness score. Transparent weights; guidance, not a prediction."""
WEIGHTS = {"skills": 0.50, "roadmap": 0.20, "portfolio": 0.15, "courses": 0.15}
PORTFOLIO_TARGET = 4  # projects + certifications needed for a full portfolio score


def readiness(coverage: float, roadmap_pct: float, portfolio_items: int, courses_done: int, courses_tracked: int,
              weights: dict | None = None) -> tuple[int, dict]:
    w = weights or WEIGHTS
    values = {"skills": coverage, "roadmap": roadmap_pct,
              "portfolio": 100 * min(1, portfolio_items / PORTFOLIO_TARGET),
              "courses": 100 * courses_done / courses_tracked if courses_tracked else 0}
    breakdown = {k: {"value": round(v), "weight": round(100 * w[k]), "points": round(v * w[k], 1)} for k, v in values.items()}
    return round(sum(v * w[k] for k, v in values.items())), breakdown
