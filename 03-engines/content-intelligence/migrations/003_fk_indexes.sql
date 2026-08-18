-- RUOS Content Intelligence Engine v0.2 performance indexes

create index if not exists ci_sources_project_id_idx on ci_sources(project_id);
create index if not exists ci_content_items_project_id_idx on ci_content_items(project_id);
create index if not exists ci_content_items_source_id_idx on ci_content_items(source_id);
create index if not exists ci_research_evidence_project_id_idx on ci_research_evidence(project_id);
create index if not exists ci_patterns_project_id_idx on ci_patterns(project_id);
create index if not exists ci_opportunities_project_id_idx on ci_opportunities(project_id);
create index if not exists ci_calendar_items_project_id_idx on ci_calendar_items(project_id);
create index if not exists ci_calendar_items_opportunity_id_idx on ci_calendar_items(opportunity_id);
create index if not exists ci_business_outcomes_project_id_idx on ci_business_outcomes(project_id);
create index if not exists ci_business_outcomes_content_item_id_idx on ci_business_outcomes(content_item_id);