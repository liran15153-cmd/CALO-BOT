with expected_tables(table_name) as (
  values
    ('users'),
    ('fitness_profiles'),
    ('chat_sessions'),
    ('chat_messages'),
    ('workout_plans'),
    ('workouts'),
    ('workout_exercises'),
    ('workout_logs'),
    ('meal_logs'),
    ('meal_items'),
    ('meal_image_analyses'),
    ('body_metrics'),
    ('safety_events'),
    ('usage_events'),
    ('pending_actions'),
    ('memory_facts')
)
select
  expected_tables.table_name,
  case when pg_class.oid is null then false else true end as table_exists,
  coalesce(pg_class.relrowsecurity, false) as rls_enabled,
  count(pg_policy.polname) as policy_count
from expected_tables
left join pg_class
  on pg_class.relname = expected_tables.table_name
left join pg_namespace
  on pg_namespace.oid = pg_class.relnamespace
  and pg_namespace.nspname = 'public'
left join pg_policy
  on pg_policy.polrelid = pg_class.oid
group by expected_tables.table_name, pg_class.oid, pg_class.relrowsecurity
order by expected_tables.table_name;

select column_name
from information_schema.columns
where table_schema = 'public'
  and table_name = 'body_metrics'
  and column_name in ('body_fat_percent', 'measurements_json', 'source')
order by column_name;

select column_name
from information_schema.columns
where table_schema = 'public'
  and table_name = 'memory_facts'
  and column_name in ('type', 'status', 'text_he', 'source_message_id', 'safety_event_id', 'expired_at', 'superseded_by')
order by column_name;

select id, name, public
from storage.buckets
where id = 'meal-images';
