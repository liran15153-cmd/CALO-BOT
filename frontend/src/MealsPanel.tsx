import { ImageUp, ScanSearch } from 'lucide-react';
import { useState } from 'react';

import { analyzeMealImage, saveManualMeal, uploadMealImage, type Meal, type MealAnalysis } from './api';

export function MealsPanel() {
  const [note, setNote] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [manualText, setManualText] = useState('Log protein shake 25g protein');
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
    setStatus('uploading');
    try {
      const saved = await saveManualMeal(manualText);
      setManualMeal(saved);
      setStatus('idle');
    } catch {
      setStatus('error');
    }
  }

  return (
    <section className="panel meals-panel">
      <div className="panel-heading">
        <h3>Meal image</h3>
        <p>Upload a meal photo. Nutrition estimates are approximate and require an AI provider.</p>
      </div>

      <form className="form-grid" onSubmit={handleUpload}>
        <label>
          <span>Meal note</span>
          <input value={note} onChange={(event) => setNote(event.target.value)} placeholder="Lunch" />
        </label>
        <label>
          <span>Meal image</span>
          <input
            accept="image/jpeg,image/png,image/webp"
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <div className="form-actions wide">
          <button className="primary-button icon-button" type="submit" disabled={status === 'uploading'}>
            <ImageUp size={17} aria-hidden="true" />
            Upload meal
          </button>
          {meal && <span className="success-text">{meal.confidence}</span>}
        </div>
      </form>

      {meal && (
        <div className="inline-section">
          <h4>Uploaded meal</h4>
          <p>{meal.note || 'No note'} saved. Image reference is stored locally.</p>
          <button className="ghost-button" type="button" onClick={handleAnalyze} disabled={status === 'analyzing'}>
            <ScanSearch size={16} aria-hidden="true" />
            Analyze image
          </button>
        </div>
      )}

      {analysis && (
        <div className="log-result">
          <strong>{analysis.provider_status}</strong>
          <span>{analysis.message}</span>
        </div>
      )}

      <section className="inline-section">
        <h4>Manual meal</h4>
        <form className="composer" onSubmit={handleManualMeal}>
          <label htmlFor="manual-meal">Manual meal</label>
          <div className="composer-row">
            <textarea id="manual-meal" value={manualText} onChange={(event) => setManualText(event.target.value)} />
            <button className="primary-button icon-button" type="submit">
              Save meal log
            </button>
          </div>
        </form>
        {manualMeal && (
          <div className="log-result">
            <strong>{manualMeal.confidence}</strong>
            <span>
              {manualMeal.calories_min}-{manualMeal.calories_max} calories
            </span>
            <span>
              {manualMeal.protein_min}-{manualMeal.protein_max}g protein
            </span>
          </div>
        )}
      </section>

      {status === 'error' && <p className="error-text">Meal request failed.</p>}
    </section>
  );
}
