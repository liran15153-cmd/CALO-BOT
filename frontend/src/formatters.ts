export function formatProviderStatus(status: string | null | undefined): string {
  return (
    {
      configured: 'פעיל',
      not_configured: 'לא מוגדר',
      provider_error: 'שגיאת ספק',
      budget_exceeded: 'תקציב נוצל',
      local_tool: 'כלי מקומי',
      safety_override: 'מענה בטיחות'
    }[status ?? ''] ?? 'בודק'
  );
}

export function formatDatabaseStatus(status: string | null | undefined): string {
  return (
    {
      configured: 'מוגדר',
      not_configured: 'לא מוגדר',
      unknown: 'לא ידוע'
    }[status ?? ''] ?? 'לא ידוע'
  );
}

export function formatSupabaseStatus(status: string | null | undefined): string {
  return (
    {
      configured: 'מוגדר',
      configured_optional: 'מוגדר, אימות אופציונלי',
      required: 'אימות נדרש',
      local: 'מצב מקומי',
      not_configured: 'לא מוגדר'
    }[status ?? ''] ?? 'לא ידוע'
  );
}

const ADJUSTMENT_EXPLANATIONS: Record<string, (exercise: string) => string> = {
  pain_reported: (exercise) =>
    `${exercise}: שומרים על אותו עומס כי סימנת כאב באימון האחרון. אם הכאב חוזר - עוצרים.`,
  high_rpe: (exercise) =>
    `${exercise}: הורדנו סט אחד כי האימון הקודם נסגר ב-RPE גבוה. נראה איך זה מרגיש היום.`,
  high_rpe_recently: (exercise) =>
    `${exercise}: הורדנו סט אחד כי האימון הקודם נסגר ב-RPE גבוה. נראה איך זה מרגיש היום.`,
  missed_or_partial: (exercise) =>
    `${exercise}: גרסת מינימום כי האימון הקודם לא הושלם - חוזרים בשלמות, לא בכוח.`,
  missed_or_partial_recently: (exercise) =>
    `${exercise}: גרסת מינימום כי האימון הקודם לא הושלם - חוזרים בשלמות, לא בכוח.`,
  completed_with_manageable_effort: (exercise) =>
    `${exercise}: אפשר לשקול תוספת עדינה - האימון הקודם נסגר במאמץ נשלט.`,
  qualitative_controlled_effort: (exercise) =>
    `${exercise}: אפשר לשקול תוספת עדינה - הלוג האחרון תיאר מאמץ בשליטה.`,
  qualitative_underload: (exercise) =>
    `${exercise}: אפשר לתקן בעדינות - הלוג האחרון תיאר שהתרגיל היה קל מדי.`,
  qualitative_high_effort: (exercise) =>
    `${exercise}: שומרים או מורידים מעט - הלוג האחרון תיאר שהתרגיל היה כבד מדי.`,
  progression_gate_missing_rpe: (exercise) =>
    `${exercise}: נשארים בגרסה הנוכחית - מאמץ מילולי נשמר, אבל צריך RPE 1-10 לפני שמתקדמים שלב.`,
  recent_workout_supported_progression: (exercise) =>
    `${exercise}: אפשר לשקול תוספת עדינה - האימון הקודם נסגר במאמץ נשלט.`,
  insufficient_pattern: (exercise) =>
    `${exercise}: שומרים על המתכון של התוכנית, אין עדיין מספיק לוגים אחרונים להחלטה אחרת.`,
  base_plan: (exercise) => `${exercise}: ממשיכים לפי התוכנית כפי שהיא נכתבה.`
};

export function formatAdjustmentExplanation(
  reason: string | null | undefined,
  exerciseName: string
): string | null {
  if (!reason) return null;
  const template = ADJUSTMENT_EXPLANATIONS[reason];
  return template ? template(exerciseName) : null;
}
