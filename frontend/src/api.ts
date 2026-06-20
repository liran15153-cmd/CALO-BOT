const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

export type HealthStatus = {
  status: string;
  service: string;
  database: string;
  ai_provider: string;
};

export type OnboardingPayload = {
  name: string;
  age_range?: string | null;
  gender?: string | null;
  height_cm?: number | null;
  weight_kg?: number | null;
  main_goal: string;
  experience_level: string;
  training_location: string;
  available_equipment: string[];
  weekly_availability: number;
  session_length_minutes: number;
  preferred_workout_days: string[];
  injuries_limitations?: string | null;
  nutrition_preference?: string | null;
  foods_disliked?: string | null;
  allergies?: string | null;
  typical_schedule?: string | null;
  coaching_style: string;
  consent_disclaimer: boolean;
};

export type OnboardingState = {
  completed: boolean;
  profile: (OnboardingPayload & { id: number; user_id: number }) | null;
};

export type ChatResponse = {
  session_id: number;
  user_message_id: number;
  coach_message_id: number;
  response: string;
  safety_flagged: boolean;
  provider_status: string;
};

export type ChatSession = {
  id: number;
  title: string;
  is_active: boolean;
};

export type WorkoutPlan = {
  id: number;
  is_current: boolean;
  name: string;
  goal: string;
  plan_type?: string | null;
  duration_weeks?: number | null;
  training_split?: string | null;
  days_per_week: number;
  session_length_minutes?: number | null;
  equipment_needed: string[];
  days: Array<{
    workout_id?: number | null;
    name: string;
    estimated_duration_minutes?: number | null;
    warmup: string[];
    difficulty: string;
    notes?: string | null;
    exercises: Array<{
      exercise_id?: number | null;
      name: string;
      sets: string;
      reps_or_duration: string;
      rest: string;
      notes?: string | null;
    }>;
  }>;
  progression_rule: string;
  recovery_note?: string | null;
};

export type TrainingAdaptation = {
  completed_recent?: number;
  skipped_recent?: number;
  pain_flags_recent?: number;
  load_signal: string;
  signals?: string[];
  next_adjustment: string;
  exercise_adjustments?: Array<{
    exercise_id?: number | null;
    exercise_name?: string | null;
    adjustment: string;
    reason: string;
    next_action: string;
  }>;
};

export type ExecutionPlanExercise = {
  exercise_id?: number | null;
  source_exercise_id?: number | null;
  name: string;
  sets: string;
  reps_or_duration: string;
  rest: string;
  notes?: string | null;
  alternatives?: string[];
  adjustment?: string | null;
  reason?: string | null;
  execution_note?: string | null;
};

export type ExecutionPlan = {
  source: string;
  base_workout_id?: number | null;
  workout_name?: string | null;
  load_signal: string;
  summary: string;
  adjusted_exercises: ExecutionPlanExercise[];
};

export type NextWorkout = {
  id: number;
  plan_id: number | null;
  name: string;
  scheduled_day?: string | null;
  difficulty?: string | null;
  warmup: string[];
  notes?: string | null;
  exercises: Array<{
    exercise_id: number;
    name: string;
    sets: string;
    reps_or_duration: string;
    rest: string;
    notes?: string | null;
    alternatives?: string[];
  }>;
  adaptation: TrainingAdaptation;
  execution_plan?: ExecutionPlan | null;
  plan?: { id: number; name: string };
};

export type WorkoutSetLogInput = {
  set_index: number;
  reps?: number | null;
  weight?: string | null;
  duration_seconds?: number | null;
  completed: boolean;
};

export type WorkoutExerciseLogInput = {
  exercise_id?: number | null;
  exercise_name: string;
  status: 'completed' | 'partial' | 'skipped' | 'modified';
  sets: WorkoutSetLogInput[];
  rpe?: number | null;
  rir?: number | null;
  notes?: string | null;
};

export type WorkoutLogInput = {
  text?: string | null;
  workout_id?: number | null;
  logged_on?: string | null;
  status?: 'completed' | 'partial' | 'skipped' | 'modified';
  exercises?: WorkoutExerciseLogInput[];
  rpe?: number | null;
  rir?: number | null;
  pain_flag?: boolean;
  notes?: string | null;
};

export type WorkoutLog = {
  id: number;
  workout_id?: number | null;
  logged_on: string;
  status: string;
  exercise_results: Array<{
    exercise?: string;
    exercise_id?: number | null;
    exercise_name?: string;
    status?: string;
    sets?: number | WorkoutSetLogInput[];
    rpe?: number | null;
    rir?: number | null;
    notes?: string | null;
    reps?: number[];
    weight?: string;
  }>;
  rpe?: number | null;
  notes?: string | null;
  pain_flag: boolean;
  parse_confidence: string;
  adaptation?: TrainingAdaptation;
};

export type Meal = {
  id: number;
  eaten_on?: string | null;
  meal_type?: string | null;
  note: string | null;
  image_path: string | null;
  calories_min?: number | null;
  calories_max?: number | null;
  protein_min?: number | null;
  protein_max?: number | null;
  confidence: string | null;
  items?: Array<{
    id?: number;
    name: string;
    quantity?: string | null;
    calories_min?: number | null;
    calories_max?: number | null;
    protein_min?: number | null;
    protein_max?: number | null;
    confidence?: string | null;
  }>;
};

export type MealAnalysis = {
  id: number;
  meal_id: number;
  provider_status: string;
  detected_items: Array<{
    name?: string;
    quantity?: string | null;
  }>;
  follow_up_questions?: string[];
  message: string;
  analysis?: {
    calorie_range?: [number | null, number | null];
    calories_range?: [number | null, number | null];
    macro_ranges?: {
      protein?: [number | null, number | null];
      carbs?: [number | null, number | null];
      fat?: [number | null, number | null];
    };
    confidence?: string;
  };
};

export type DashboardState = {
  current_goal: string | null;
  current_workout_plan: { name: string } | null;
  next_workout: {
    id?: number | null;
    name?: string | null;
    plan_id?: number | null;
    plan_name?: string | null;
    load_signal?: string | null;
    next_adjustment?: string | null;
  } | null;
  completed_workouts_this_week: number;
  meals_logged_this_week: number;
  meals_logged_today: number;
  estimated_nutrition_range: [number | null, number | null] | null;
  estimated_protein_range_today: [number | null, number | null] | null;
  nutrition_action: string;
  recent_coach_notes: string[];
  current_streak: number;
  missed_workouts: number;
  next_recommended_action: string;
};

export type SummaryResponse = {
  summary?: string | null;
  metrics?: Record<string, number | string | null | undefined>;
  next_action?: string | null;
  week_start?: string | null;
  week_end?: string | null;
  persisted?: boolean;
};

export type SettingsState = {
  ai_provider: string;
  model: string;
  database: string;
  api_key_present: boolean;
  disclaimer: string;
};

export type ResetResult = {
  deleted_records: number;
  message: string;
};

export type UsageState = {
  usage_date: string;
  chat_requests_count: number;
  image_analysis_count: number;
  summary_requests_count: number;
  estimated_tokens_in: number;
  estimated_tokens_out: number;
  estimated_tokens_total: number;
  daily_ai_token_limit: number;
  tokens_remaining: number;
};

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/api/health`);
  if (!response.ok) {
    throw new Error(`בדיקת תקינות נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function fetchOnboarding(): Promise<OnboardingState> {
  const response = await fetch(`${API_BASE}/api/onboarding`);
  if (!response.ok) {
    throw new Error(`טעינת פרופיל ראשוני נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function saveOnboarding(payload: OnboardingPayload): Promise<OnboardingState> {
  const response = await fetch(`${API_BASE}/api/onboarding`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`שמירת פרופיל ראשוני נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function sendChatMessage(message: string, sessionId?: number): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId ?? null })
  });
  if (!response.ok) {
    throw new Error(`בקשת הצ'אט נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function createChatSession(title = 'צ\'אט מאמן'): Promise<ChatSession> {
  const response = await fetch(`${API_BASE}/api/chat/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  });
  if (!response.ok) {
    throw new Error(`יצירת שיחת מאמן נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function resetChatSession(sessionId: number): Promise<ChatSession> {
  const response = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}/reset`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error(`איפוס שיחת המאמן נכשל: ${response.status}`);
  }
  return response.json();
}

export async function generateWorkoutPlan(prompt: string): Promise<WorkoutPlan> {
  const response = await fetch(`${API_BASE}/api/workout-plans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });
  if (!response.ok) {
    throw new Error(`יצירת תוכנית האימון נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function fetchCurrentWorkoutPlan(): Promise<WorkoutPlan | null> {
  const response = await fetch(`${API_BASE}/api/workout-plans/current`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`טעינת תוכנית האימון הנוכחית נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function fetchNextWorkout(): Promise<NextWorkout | null> {
  const response = await fetch(`${API_BASE}/api/workouts/next`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`טעינת האימון הבא נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function saveWorkoutLog(input: string | WorkoutLogInput): Promise<WorkoutLog> {
  const body = typeof input === 'string' ? { text: input } : input;
  const response = await fetch(`${API_BASE}/api/workout-logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(`שמירת תיעוד האימון נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function fetchRecentWorkoutLogs(): Promise<WorkoutLog[]> {
  const response = await fetch(`${API_BASE}/api/workout-logs/recent`);
  if (!response.ok) {
    throw new Error(`טעינת תיעודי האימון האחרונים נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function uploadMealImage(note: string, file: File): Promise<Meal> {
  const formData = new FormData();
  formData.set('note', note);
  formData.set('file', file);
  const response = await fetch(`${API_BASE}/api/meals/upload`, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) {
    throw new Error(`העלאת הארוחה נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function fetchRecentMeals(): Promise<Meal[]> {
  const response = await fetch(`${API_BASE}/api/meals/recent`);
  if (!response.ok) {
    throw new Error(`טעינת הארוחות האחרונות נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function analyzeMealImage(mealId: number): Promise<MealAnalysis> {
  const response = await fetch(`${API_BASE}/api/meals/${mealId}/analyze`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error(`ניתוח הארוחה נכשל: ${response.status}`);
  }
  return response.json();
}

export async function saveManualMeal(text: string): Promise<Meal> {
  const response = await fetch(`${API_BASE}/api/meals/manual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  if (!response.ok) {
    throw new Error(`שמירת הארוחה הידנית נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function fetchDashboard(): Promise<DashboardState> {
  const response = await fetch(`${API_BASE}/api/dashboard`);
  if (!response.ok) {
    throw new Error(`טעינת לוח הבקרה נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function fetchCurrentWeeklySummary(): Promise<SummaryResponse> {
  const response = await fetch(`${API_BASE}/api/summaries/weekly/current`);
  if (!response.ok) {
    throw new Error(`טעינת הסקירה השבועית נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function fetchSettings(): Promise<SettingsState> {
  const response = await fetch(`${API_BASE}/api/settings`);
  if (!response.ok) {
    throw new Error(`טעינת ההגדרות נכשלה: ${response.status}`);
  }
  return response.json();
}

export async function exportSettingsData(): Promise<unknown> {
  const response = await fetch(`${API_BASE}/api/settings/export`);
  if (!response.ok) {
    throw new Error(`ייצוא הנתונים נכשל: ${response.status}`);
  }
  return response.json();
}

export async function resetLocalData(): Promise<ResetResult> {
  const response = await fetch(`${API_BASE}/api/settings/reset`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error(`איפוס הנתונים נכשל: ${response.status}`);
  }
  return response.json();
}

export async function fetchUsage(): Promise<UsageState> {
  const response = await fetch(`${API_BASE}/api/usage`);
  if (!response.ok) {
    throw new Error(`טעינת נתוני השימוש נכשלה: ${response.status}`);
  }
  return response.json();
}
