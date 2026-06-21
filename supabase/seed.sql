insert into public.users (auth_user_id, email, name)
values ('00000000-0000-4000-8000-000000000001', 'dev@example.local', 'Dev User')
on conflict (auth_user_id) do update
set email = excluded.email,
    name = excluded.name;

insert into public.fitness_profiles (
  user_id,
  main_goal,
  experience_level,
  training_location,
  available_equipment,
  weekly_availability,
  session_length_minutes,
  preferred_workout_days,
  coaching_style,
  consent_disclaimer
)
select
  users.id,
  'improve_consistency',
  'beginner',
  'home',
  '["bodyweight"]'::jsonb,
  3,
  30,
  '["Monday","Wednesday","Friday"]'::jsonb,
  'direct',
  true
from public.users
where users.auth_user_id = '00000000-0000-4000-8000-000000000001'
on conflict (user_id) do nothing;
