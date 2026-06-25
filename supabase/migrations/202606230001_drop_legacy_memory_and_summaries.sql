-- Compatibility cleanup for older deployments: remove legacy keyword-based memory
-- tables (coaching_memories, memory_summaries) and the separate weekly/daily
-- summaries table (weekly_summaries). This migration does not create the next memory
-- system; it only prevents old deployments from keeping duplicate memory sources.
--
-- Dropping each table with CASCADE also removes its indexes and RLS policies.

drop policy if exists coaching_memories_own_rows on public.coaching_memories;
drop policy if exists memory_summaries_own_rows on public.memory_summaries;
drop policy if exists weekly_summaries_own_rows on public.weekly_summaries;

drop table if exists public.coaching_memories cascade;
drop table if exists public.memory_summaries cascade;
drop table if exists public.weekly_summaries cascade;
