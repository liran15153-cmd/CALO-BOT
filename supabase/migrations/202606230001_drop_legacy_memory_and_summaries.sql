-- Step 1 of the memory-system rebuild: drop the legacy keyword-based memory engine
-- (coaching_memories, memory_summaries) and the separate weekly/daily summaries
-- analytics feature (weekly_summaries). These are intentionally removed to start from a
-- clean infrastructure before building the new typed fact store (memory_facts).
--
-- Dropping each table with CASCADE also removes its indexes and RLS policies.

drop policy if exists coaching_memories_own_rows on public.coaching_memories;
drop policy if exists memory_summaries_own_rows on public.memory_summaries;
drop policy if exists weekly_summaries_own_rows on public.weekly_summaries;

drop table if exists public.coaching_memories cascade;
drop table if exists public.memory_summaries cascade;
drop table if exists public.weekly_summaries cascade;
