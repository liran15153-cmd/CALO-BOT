alter table if exists public.body_metrics
add column if not exists body_fat_percent double precision,
add column if not exists measurements_json jsonb not null default '{}'::jsonb,
add column if not exists source varchar(80) not null default 'manual';
