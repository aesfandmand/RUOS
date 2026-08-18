-- Research Engine v0.3 persistence hardening.
-- Adds normalized queryable fields while keeping richer payload in metadata.

alter table ci_research_evidence
  add column if not exists fingerprint text,
  add column if not exists source_class text,
  add column if not exists topic text,
  add column if not exists title text,
  add column if not exists published_at timestamptz,
  add column if not exists confidence numeric(5,4),
  add column if not exists commercial_relevance numeric(5,2),
  add column if not exists corroboration_status text;

create unique index if not exists ci_research_evidence_project_fingerprint_uidx
  on ci_research_evidence(project_id, fingerprint)
  where fingerprint is not null;

create index if not exists ci_research_evidence_project_source_idx
  on ci_research_evidence(project_id, source_type, observed_at desc);

create index if not exists ci_research_evidence_project_topic_idx
  on ci_research_evidence(project_id, topic)
  where topic is not null;
