-- RUOS Content Intelligence Engine v0.2 database hardening
-- Mirrors the live Supabase hardening applied to project `umbrella social`.

create unique index if not exists ci_sources_project_type_key_uidx
  on ci_sources(project_id, source_type, source_key)
  where source_key is not null;

create unique index if not exists ci_metric_snapshots_target_uidx
  on ci_metric_snapshots(content_item_id, age_hours)
  where age_hours is not null;

alter table ci_projects enable row level security;
alter table ci_sources enable row level security;
alter table ci_content_items enable row level security;
alter table ci_metric_snapshots enable row level security;
alter table ci_research_evidence enable row level security;
alter table ci_patterns enable row level security;
alter table ci_opportunities enable row level security;
alter table ci_calendar_items enable row level security;
alter table ci_business_outcomes enable row level security;

-- Intentionally no public RLS policies in this phase.
-- The engine writes through a trusted server-side PostgreSQL connection only.