import { ImageUp, ScanSearch } from 'lucide-react';
import { useState } from 'react';

import { analyzeMealImage, saveManualMeal, uploadMealImage, type Meal, type MealAnalysis } from './api';
import { formatProviderStatus } from './formatters';

export function MealsPanel() {
  const [note, setNote] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [manualText, setManualText] = useState('');
  const [meal, setMeal] = useState<Meal | null>(null);
  const [manualMeal, setManualMeal] = useState<Meal | null>(null);
  const [analysis, setAnalysis] = useState<MealAnalysis | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'analyzing' | 'error'>('idle');

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
          <p>{meal.note || 'ללא הערה'} נשמרה. ההפניה לתמונה נשמרת מקומית.</p>
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
            <span>
              {manualMeal.calories_min}-{manualMeal.calories_max} קלוריות
            </span>
            <span>
              {manualMeal.protein_min}-{manualMeal.protein_max} גרם חלבון
            </span>
          </div>
        )}
      </section>

      {status === 'error' && <p className="error-text">בקשת הארוחה נכשלה.</p>}
    </section>
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
    }[confidence ?? ''] ?? confidence ?? 'לא ידוע'
  );
}
