-- RUOS Content Intelligence Engine v0.1
-- PostgreSQL / Supabase-compatible starter schema.

create table if not exists ci_projects (
  id text primary key,
  name text not null,
  language text not null default 'fa',
  geography jsonb not null default '{}'::jsonb,
  config jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ci_sources (
  id bigserial primary key,
  project_id text not null references ci_projects(id) on delete cascade,
  source_type text not null,
  source_key text,
  data_class text not null check (data_class in ('owned','competitive','public','first_party')),
  access_mode text,
  weight numeric(5,4) not null default 1.0,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists ci_content_items (
  id bigserial primary key,
  project_id text not null references ci_projects(id) on delete cascade,
  source_id bigint references ci_sources(id) on delete set null,
  external_id text,
  canonical_url text,
  author_handle text,
  platform text not null,
  content_type text,
  published_at timestamptz,
  title text,
  caption text,
  hook text,
  topic text,
  pillar text,
  intent text,
  funnel_stage text,
  content_role text,
  language text,
  public_metrics jsonb not null default '{}'::jsonb,
  analysis jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(project_id, platform, external_id)
);

create table if not exists ci_metric_snapshots (
  id bigserial primary key,
  content_item_id bigint not null references ci_content_items(id) on delete cascade,
  captured_at timestamptz not null default now(),
  age_hours integer,
  metrics jsonb not null,
  derived jsonb not null default '{}'::jsonb
);

create index if not exists ci_metric_snapshots_item_time_idx
  on ci_metric_snapshots(content_item_id, captured_at desc);

create table if not exists ci_research_evidence (
  id bigserial primary key,
  project_id text not null references ci_projects(id) on delete cascade,
  source_type text not null,
  evidence_type text not null,
  query text,
  excerpt text,
  url text,
  observed_at timestamptz not null default now(),
  tags text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists ci_patterns (
  id bigserial primary key,
  project_id text not null references ci_projects(id) on delete cascade,
  pattern_type text not null,
  name text not null,
  formula text,
  evidence_count integer not null default 0,
  confidence numeric(5,2),
  examples jsonb not null default '[]'::jsonb,
  status text not null default 'candidate',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ci_opportunities (
  id bigserial primary key,
  project_id text not null references ci_projects(id) on delete cascade,
  topic text not null,
  proposed_hook text,
  proposed_format text,
  pillar text,
  content_role text,
  evidence_ids bigint[] not null default '{}',
  signals jsonb not null,
  opportunity_score numeric(5,2) not null,
  bucket text not null check (bucket in ('produce_now','backlog','watch_or_reject')),
  status text not null default 'candidate',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ci_calendar_items (
  id bigserial primary key,
  project_id text not null references ci_projects(id) on delete cascade,
  opportunity_id bigint references ci_opportunities(id) on delete set null,
  planned_date date,
  platform text,
  format text,
  hook text,
  objective text,
  kpi text,
  status text not null default 'planned',
  production_brief jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ci_business_outcomes (
  id bigserial primary key,
  project_id text not null references ci_projects(id) on delete cascade,
  content_item_id bigint references ci_content_items(id) on delete set null,
  occurred_at timestamptz not null default now(),
  outcome_type text not null check (outcome_type in ('profile_visit','follow','dm','consultation','lead','sale')),
  value numeric,
  metadata jsonb not null default '{}'::jsonb
);

-- Security rule for implementation phase:
-- API tokens and OAuth secrets MUST NOT be stored in these tables or committed to Git.
