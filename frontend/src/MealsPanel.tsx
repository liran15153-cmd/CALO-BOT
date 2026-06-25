import { ImageUp, ScanSearch } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { analyzeMealImage, fetchRecentMeals, saveManualMeal, uploadMealImage, type Meal, type MealAnalysis } from './api';
import { formatProviderStatus } from './formatters';

export function MealsPanel() {
  const [note, setNote] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [manualText, setManualText] = useState('');
  const [meal, setMeal] = useState<Meal | null>(null);
  const [manualMeal, setManualMeal] = useState<Meal | null>(null);
  const [recentMeals, setRecentMeals] = useState<Meal[]>([]);
  const [recentMealsStatus, setRecentMealsStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [analysis, setAnalysis] = useState<MealAnalysis | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'analyzing' | 'error'>('idle');

  const loadRecentMeals = useCallback(async () => {
    try {
      const meals = await fetchRecentMeals();
      setRecentMeals(Array.isArray(meals) ? meals : []);
      setRecentMealsStatus('ready');
    } catch {
      setRecentMealsStatus('error');
    }
  }, []);

  useEffect(() => {
    let active = true;
    fetchRecentMeals()
      .then((meals) => {
        if (!active) return;
        setRecentMeals(Array.isArray(meals) ? meals : []);
        setRecentMealsStatus('ready');
      })
      .catch(() => {
        if (!active) return;
        setRecentMealsStatus('error');
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setStatus('error');
      return;
    }
    setStatus('uploading');
    try {
      const saved = await uploadMealImage(note, file);
      setMeal(saved);
      setAnalysis(null);
      await loadRecentMeals();
      setStatus('idle');
    } catch {
      setStatus('error');
    }
  }

  async function handleAnalyze() {
    if (!meal) return;
    setStatus('analyzing');
    try {
      const result = await analyzeMealImage(meal.id);
      setAnalysis(result);
      await loadRecentMeals();
      setStatus('idle');
    } catch {
      setStatus('error');
    }
  }

  async function handleManualMeal(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = manualText.trim();
    if (!trimmed) return;
    setStatus('uploading');
    try {
      const saved = await saveManualMeal(trimmed);
      setManualMeal(saved);
      setManualText('');
      await loadRecentMeals();
      setStatus('idle');
    } catch {
      setStatus('error');
    }
  }

  return (
    <section className="panel meals-panel">
      <div className="panel-heading">
        <h3>תמונת ארוחה</h3>
        <p>העלה תמונת ארוחה. הערכות תזונה הן משוערות ודורשות ספק בינה מלאכותית פעיל.</p>
      </div>

      <form className="form-grid" onSubmit={handleUpload}>
        <label>
          <span>הערת ארוחה</span>
          <input value={note} onChange={(event) => setNote(event.target.value)} placeholder="ארוחת צהריים" />
        </label>
        <label>
          <span>תמונת ארוחה</span>
          <input
            accept="image/jpeg,image/png,image/webp"
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <div className="form-actions wide">
          <button className="primary-button icon-button" type="submit" disabled={status === 'uploading'}>
            <ImageUp size={17} aria-hidden="true" />
            העלאת ארוחה
          </button>
          {meal && <span className="success-text">{formatConfidence(meal.confidence)}</span>}
        </div>
      </form>

      {meal && (
        <div className="inline-section">
          <h4>ארוחה שהועלתה</h4>
          <p>הארוחה מוכנה לניתוח. {meal.note ? `הערה: ${meal.note}. ` : ''}ההפניה לתמונה זמינה מקומית.</p>
          <button className="ghost-button" type="button" onClick={handleAnalyze} disabled={status === 'analyzing'}>
            <ScanSearch size={16} aria-hidden="true" />
            ניתוח תמונה
          </button>
        </div>
      )}

      {analysis && (
        <div className="log-result">
          <strong>{formatProviderStatus(analysis.provider_status)}</strong>
          {analysis.message ? <span>{analysis.message}</span> : null}
          {formatRange(analysis.analysis?.calorie_range ?? analysis.analysis?.calories_range, 'קלוריות')}
          {formatRange(analysis.analysis?.macro_ranges?.protein, 'גרם חלבון')}
          {analysis.detected_items.map((item) =>
            item.name ? (
              <span key={`${item.name}-${item.quantity ?? ''}`}>
                {item.name}
                {item.quantity ? `, ${item.quantity}` : ''}
              </span>
            ) : null
          )}
          {analysis.follow_up_questions?.map((question) => <span key={question}>{question}</span>)}
        </div>
      )}

      <section className="inline-section">
        <h4>ארוחה ידנית</h4>
        <form className="composer" onSubmit={handleManualMeal}>
          <label htmlFor="manual-meal">ארוחה ידנית</label>
          <div className="composer-row">
            <textarea
              id="manual-meal"
              value={manualText}
              onChange={(event) => setManualText(event.target.value)}
              placeholder="תעד שייק חלבון עם 25 גרם חלבון."
            />
            <button className="primary-button icon-button" type="submit" disabled={!manualText.trim()}>
              שמירת ארוחה
            </button>
          </div>
        </form>
        {manualMeal && (
          <div className="log-result">
            <strong>{formatConfidence(manualMeal.confidence)}</strong>
            {formatRange([manualMeal.calories_min ?? null, manualMeal.calories_max ?? null], 'קלוריות')}
            {formatRange([manualMeal.protein_min ?? null, manualMeal.protein_max ?? null], 'גרם חלבון')}
          </div>
        )}
      </section>

      <section className="inline-section meal-history-section">
        <h4>ארוחות אחרונות</h4>
        {recentMealsStatus === 'loading' ? (
          <p className="plan-note">טוען ארוחות אחרונות...</p>
        ) : recentMealsStatus === 'error' ? (
          <p className="error-text">לא הצלחתי לטעון את הארוחות האחרונות.</p>
        ) : recentMeals.length > 0 ? (
          <div className="meal-history-list">
            {recentMeals.map((recentMeal) => (
              <article className="meal-history-item" key={recentMeal.id}>
                <div className="meal-history-heading">
                  <strong>{recentMeal.note || formatMealType(recentMeal.meal_type)}</strong>
                  <span>{formatMealDate(recentMeal.eaten_on)}</span>
                  <span>{formatConfidence(recentMeal.confidence)}</span>
                </div>
                <div className="meal-history-ranges">
                  {formatRange([recentMeal.calories_min ?? null, recentMeal.calories_max ?? null], 'קלוריות')}
                  {formatRange([recentMeal.protein_min ?? null, recentMeal.protein_max ?? null], 'גרם חלבון')}
                </div>
                {recentMeal.items?.length ? (
                  <div className="meal-history-items">
                    {recentMeal.items.map((item) => (
                      <span key={item.id ?? `${recentMeal.id}-${item.name}`}>
                        {item.name}
                        {item.quantity ? `, ${item.quantity}` : ''}
                      </span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <p className="plan-note">אין עדיין ארוחות שמורות להצגה.</p>
        )}
      </section>

      {status === 'error' && <p className="error-text">בקשת הארוחה נכשלה.</p>}
    </section>
  );
}

function formatMealDate(value: string | null | undefined): string {
  if (!value) return 'תאריך לא ידוע';
  return value;
}

function formatMealType(value: string | null | undefined): string {
  return (
    {
      breakfast: 'ארוחת בוקר',
      lunch: 'ארוחת צהריים',
      dinner: 'ארוחת ערב',
      snack: 'נשנוש'
    }[value ?? ''] ?? 'ארוחה'
  );
}

function formatRange(range: [number | null, number | null] | undefined, unit: string) {
  if (!range || range[0] == null || range[1] == null) {
    return null;
  }
  return (
    <span>
      {range[0]}-{range[1]}
      {' '}
      {unit}
    </span>
  );
}

function formatConfidence(confidence: string | null | undefined): string {
  return (
    {
      not_analyzed: 'טרם נותח',
      unavailable: 'לא זמין',
      low: 'ביטחון נמוך',
      medium: 'ביטחון בינוני',
      high: 'ביטחון גבוה'
    }[confidence ?? ''] ?? 'לא ידוע'
  );
}
