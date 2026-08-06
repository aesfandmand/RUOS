from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable


class CreativeKnowledgeGraphError(ValueError):
    """Raised when creative knowledge is invalid or not traceable."""


_ALLOWED_KINDS = {
    "brand",
    "industry",
    "persona",
    "query",
    "intent",
    "journey-stage",
    "pattern",
    "component",
    "motion",
    "story",
    "typography",
    "cta",
    "capability",
}

_ALLOWED_RELATIONS = {
    "suggests",
    "targets",
    "prefers",
    "requires",
    "supports",
    "reinforces",
    "advances",
    "fits",
    "constrains",
}


@dataclass(frozen=True)
class KnowledgeEntity:
    id: str
    kind: str
    label: str
    attributes: tuple[tuple[str, object], ...] = ()

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "attributes": {key: value for key, value in self.attributes},
        }


@dataclass(frozen=True)
class KnowledgeRelation:
    source: str
    relation: str
    target: str
    evidence: str
    weight: int = 100

    def payload(self) -> dict[str, object]:
        return {
            "source": self.source,
            "relation": self.relation,
            "target": self.target,
            "evidence": self.evidence,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class CreativeKnowledgeGraph:
    page_slug: str
    entities: tuple[KnowledgeEntity, ...]
    relations: tuple[KnowledgeRelation, ...]

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "entities": [entity.payload() for entity in self.entities],
            "relations": [relation.payload() for relation in self.relations],
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def entity(self, entity_id: str) -> KnowledgeEntity:
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        raise KeyError(entity_id)

    def targets(self, source: str, relation: str | None = None) -> tuple[KnowledgeEntity, ...]:
        ids = {
            edge.target
            for edge in self.relations
            if edge.source == source and (relation is None or edge.relation == relation)
        }
        return tuple(entity for entity in self.entities if entity.id in ids)


def _normalize_entity(entity: KnowledgeEntity) -> KnowledgeEntity:
    entity_id = entity.id.strip()
    label = entity.label.strip()
    kind = entity.kind.strip()
    if not entity_id or not label:
        raise CreativeKnowledgeGraphError("Knowledge entities require non-empty id and label")
    if kind not in _ALLOWED_KINDS:
        raise CreativeKnowledgeGraphError(f"Unsupported knowledge entity kind: {kind}")
    attributes = tuple(sorted(entity.attributes, key=lambda item: item[0]))
    return KnowledgeEntity(id=entity_id, kind=kind, label=label, attributes=attributes)


def build_graph(
    page_slug: str,
    entities: Iterable[KnowledgeEntity],
    relations: Iterable[KnowledgeRelation],
) -> CreativeKnowledgeGraph:
    normalized_entities = tuple(sorted((_normalize_entity(entity) for entity in entities), key=lambda item: item.id))
    if not normalized_entities:
        raise CreativeKnowledgeGraphError("Creative knowledge graph cannot be empty")

    ids = [entity.id for entity in normalized_entities]
    if len(ids) != len(set(ids)):
        raise CreativeKnowledgeGraphError("Creative knowledge graph contains duplicate entity ids")
    entity_ids = set(ids)

    normalized_relations: list[KnowledgeRelation] = []
    seen_relations: set[tuple[str, str, str]] = set()
    for edge in relations:
        if edge.relation not in _ALLOWED_RELATIONS:
            raise CreativeKnowledgeGraphError(f"Unsupported knowledge relation: {edge.relation}")
        if edge.source not in entity_ids or edge.target not in entity_ids:
            raise CreativeKnowledgeGraphError(
                f"Knowledge relation references unknown entity: {edge.source} -> {edge.target}"
            )
        if edge.source == edge.target:
            raise CreativeKnowledgeGraphError("Self-referential knowledge relations are not allowed")
        if not edge.evidence.strip():
            raise CreativeKnowledgeGraphError("Knowledge relations require traceable evidence")
        if not 0 <= edge.weight <= 100:
            raise CreativeKnowledgeGraphError("Knowledge relation weight must be between 0 and 100")
        key = (edge.source, edge.relation, edge.target)
        if key in seen_relations:
            raise CreativeKnowledgeGraphError("Duplicate knowledge relation")
        seen_relations.add(key)
        normalized_relations.append(edge)

    normalized_relations.sort(key=lambda edge: (edge.source, edge.relation, edge.target))
    return CreativeKnowledgeGraph(
        page_slug=page_slug.strip(),
        entities=normalized_entities,
        relations=tuple(normalized_relations),
    )
