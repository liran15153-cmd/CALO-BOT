import type { WorkoutPlan } from './api';

export function formatPlanType(planType?: string | null): string | null {
  if (isSingleWorkoutPlan(planType)) return 'אימון יחיד';
  if (planType === 'weekly_plan') return 'תוכנית שבועית';
  if (planType === 'two_week_plan') return 'תוכנית לשבועיים';
  if (planType === 'monthly_plan') return 'תוכנית חודשית';
  if (planType === 'multi_week') return 'תוכנית רב-שבועית';
  return null;
}

export function formatPlanWeeks(planType?: string | null, weeks?: number | null): string | null {
  if (isSingleWorkoutPlan(planType) || !weeks) return null;
  if (weeks === 1) return 'שבוע אחד';
  if (weeks === 2) return 'שבועיים';
  return `${weeks} שבועות`;
}

export function formatPlanSessionLength(planType?: string | null, minutes?: number | null): string | null {
  if (!minutes) return null;
  if (isSingleWorkoutPlan(planType)) return `${minutes} דקות`;
  return `${minutes} דקות לאימון`;
}

export function formatWorkoutPlanDuration(plan: Pick<WorkoutPlan, 'plan_type' | 'duration_weeks' | 'session_length_minutes' | 'days'>): string | null {
  const duration = plan.session_length_minutes ?? plan.days[0]?.estimated_duration_minutes;
  if (isSingleWorkoutPlan(plan.plan_type)) {
    return formatPlanSessionLength(plan.plan_type, duration);
  }
  return [formatPlanWeeks(plan.plan_type, plan.duration_weeks), formatPlanSessionLength(plan.plan_type, duration)]
    .filter(Boolean)
    .join(', ') || null;
}

function isSingleWorkoutPlan(planType?: string | null): boolean {
  return planType === 'single_workout' || planType === 'single_session';
}
