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

export type WorkoutPlan = {
  id: number;
  is_current: boolean;
  name: string;
  goal: string;
  days_per_week: number;
  equipment_needed: string[];
  days: Array<{
    name: string;
    warmup: string[];
    difficulty: string;
    notes?: string | null;
    exercises: Array<{
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

export type WorkoutLog = {
  id: number;
  logged_on: string;
  status: string;
  exercise_results: Array<{
    exercise: string;
    sets?: number;
    reps?: number[];
    weight?: string;
  }>;
  pain_flag: boolean;
  parse_confidence: string;
};

export type Meal = {
  id: number;
  note: string | null;
  image_path: string | null;
  calories_min?: number | null;
  calories_max?: number | null;
  protein_min?: number | null;
  protein_max?: number | null;
  confidence: string | null;
};

export type MealAnalysis = {
  id: number;
  meal_id: number;
  provider_status: string;
  detected_items: unknown[];
  follow_up_questions?: string[];
  message: string;
};

export type DashboardState = {
  current_goal: string | null;
  current_workout_plan: { name: string } | null;
  completed_workouts_this_week: number;
  meals_logged_this_week: number;
  estimated_nutrition_range: [number, number] | null;
  recent_coach_notes: string[];
  current_streak: number;
  missed_workouts: number;
  next_recommended_action: string;
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
};

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/api/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchOnboarding(): Promise<OnboardingState> {
  const response = await fetch(`${API_BASE}/api/onboarding`);
  if (!response.ok) {
    throw new Error(`Onboarding fetch failed: ${response.status}`);
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
    throw new Error(`Onboarding save failed: ${response.status}`);
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
    throw new Error(`Chat request failed: ${response.status}`);
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
    throw new Error(`Workout plan generation failed: ${response.status}`);
  }
  return response.json();
}

export async function saveWorkoutLog(text: string): Promise<WorkoutLog> {
  const response = await fetch(`${API_BASE}/api/workout-logs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  if (!response.ok) {
    throw new Error(`Workout log save failed: ${response.status}`);
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
    throw new Error(`Meal upload failed: ${response.status}`);
  }
  return response.json();
}

export async function analyzeMealImage(mealId: number): Promise<MealAnalysis> {
  const response = await fetch(`${API_BASE}/api/meals/${mealId}/analyze`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error(`Meal analysis failed: ${response.status}`);
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
    throw new Error(`Manual meal save failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchDashboard(): Promise<DashboardState> {
  const response = await fetch(`${API_BASE}/api/dashboard`);
  if (!response.ok) {
    throw new Error(`Dashboard fetch failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchSettings(): Promise<SettingsState> {
  const response = await fetch(`${API_BASE}/api/settings`);
  if (!response.ok) {
    throw new Error(`Settings fetch failed: ${response.status}`);
  }
  return response.json();
}

export async function exportSettingsData(): Promise<unknown> {
  const response = await fetch(`${API_BASE}/api/settings/export`);
  if (!response.ok) {
    throw new Error(`Data export failed: ${response.status}`);
  }
  return response.json();
}

export async function resetLocalData(): Promise<ResetResult> {
  const response = await fetch(`${API_BASE}/api/settings/reset`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error(`Data reset failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchUsage(): Promise<UsageState> {
  const response = await fetch(`${API_BASE}/api/usage`);
  if (!response.ok) {
    throw new Error(`Usage fetch failed: ${response.status}`);
  }
  return response.json();
}
