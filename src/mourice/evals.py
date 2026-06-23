"""Retrieval evals — measure semantic-search relevance (RU/PL/code).

A small labelled set of queries with the note we expect to surface. Running it
gives a hit-rate we can compare across embedding models — a simple MLOps feedback
loop (see "Выбор embedding-модели"). Deterministic: no LLM generation involved.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mourice.memory.store import ChromaStore

__all__ = ["EvalCase", "EvalReport", "DEFAULT_CASES", "evaluate"]


@dataclass(frozen=True)
class EvalCase:
    """One query and the note title/path we expect among the results."""

    query: str
    expect: str  # substring matched against a result's note title or path
    lang: str = "ru"


@dataclass(frozen=True)
class CaseResult:
    case: EvalCase
    hit: bool
    top: str


@dataclass(frozen=True)
class EvalReport:
    """Aggregate eval outcome."""

    results: list[CaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def hits(self) -> int:
        return sum(1 for r in self.results if r.hit)

    @property
    def hit_rate(self) -> float:
        return self.hits / self.total if self.total else 0.0


# Queries reference notes that exist in the project knowledge base.
DEFAULT_CASES: tuple[EvalCase, ...] = (
    EvalCase("как Морис выбирает модель под задачу", "Стратегия выбора моделей"),
    EvalCase("правила записи фактов в память", "самообучение"),
    EvalCase("мой самый первый прототип Мориса", "Прототип Morris"),
    EvalCase("какой характер и тон у Мориса", "Личность"),
    EvalCase("как делается бэкап заметок", "Бэкап"),
    EvalCase("plan rozwoju i etapy projektu", "Дорожная карта", lang="pl"),
    EvalCase("docker multi-stage build", "Docker", lang="code"),
)


def evaluate(
    store: ChromaStore,
    cases: tuple[EvalCase, ...] = DEFAULT_CASES,
    *,
    k: int = 3,
) -> EvalReport:
    """Run the eval cases against the store and return a report."""
    results: list[CaseResult] = []
    for case in cases:
        hits = store.search(case.query, n_results=k)
        expect = case.expect.lower()
        matched = next(
            (h for h in hits if expect in h.note_title.lower() or expect in h.note_path.lower()),
            None,
        )
        top = hits[0].breadcrumb if hits else "(no results)"
        results.append(CaseResult(case=case, hit=matched is not None, top=top))
    return EvalReport(results=results)
