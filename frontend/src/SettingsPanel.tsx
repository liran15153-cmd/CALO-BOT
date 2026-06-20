import { Download, RotateCcw, ShieldCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { exportSettingsData, fetchSettings, fetchUsage, resetLocalData, type SettingsState, type UsageState } from './api';
import { formatDatabaseStatus, formatProviderStatus } from './formatters';

export function SettingsPanel() {
  const [settings, setSettings] = useState<SettingsState | null>(null);
  const [usage, setUsage] = useState<UsageState | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [resetArmed, setResetArmed] = useState(false);
  const [actionStatus, setActionStatus] = useState<'idle' | 'busy' | 'error'>('idle');
  const [actionMessage, setActionMessage] = useState<string>('');
  const [exportData, setExportData] = useState<unknown>(null);

  useEffect(() => {
    let active = true;
    Promise.all([fetchSettings(), fetchUsage()])
      .then(([settingsData, usageData]) => {
        if (!active) return;
        setSettings(settingsData);
        setUsage(usageData);
        setStatus('ready');
      })
      .catch(() => {
        if (!active) return;
        setStatus('error');
      });
    return () => {
      active = false;
    };
  }, []);

  const exportPreview = useMemo(() => {
    if (!exportData) return '';
    return JSON.stringify(exportData, null, 2);
  }, [exportData]);

  async function handleExport() {
    setActionMessage('');
    setActionStatus('busy');
    try {
      const data = await exportSettingsData();
      setExportData(data);
      setActionMessage('הייצוא מוכן');
      setActionStatus('idle');
    } catch {
      setExportData(null);
      setActionMessage('הייצוא נכשל');
      setActionStatus('error');
    }
  }

  async function handleReset() {
    if (!resetArmed) {
      setResetArmed(true);
      setActionMessage('לחץ שוב על איפוס לאישור מחיקה.');
      return;
    }
    setActionMessage('');
    setActionStatus('busy');
    try {
      const result = await resetLocalData();
      setExportData(null);
      setResetArmed(false);
      setActionMessage(`${result.deleted_records} רשומות נמחקו`);
      const [settingsData, usageData] = await Promise.all([fetchSettings(), fetchUsage()]);
      setSettings(settingsData);
      setUsage(usageData);
      setActionStatus('idle');
    } catch {
      setActionStatus('error');
      setActionMessage('האיפוס נכשל');
    }
  }

  if (status === 'loading') {
    return (
      <section className="panel settings-panel">
        <p>טוען הגדרות...</p>
      </section>
    );
  }

  if (status === 'error' || !settings) {
    return (
      <section className="panel settings-panel">
        <h3>ההגדרות לא זמינות</h3>
        <p className="error-text">הבקאנד לא החזיר הגדרות.</p>
      </section>
    );
  }

  return (
    <section className="panel settings-panel">
      <div className="panel-heading">
        <h3>ספק בינה מלאכותית וניהול נתונים</h3>
        <p>סטטוס הגדרות מקומי וכלי שליטה בנתונים במחשב הזה.</p>
      </div>

      <div className="settings-grid">
        <div className="settings-row">
          <span>ספק בינה מלאכותית</span>
          <strong>{formatProviderStatus(settings.ai_provider)}</strong>
        </div>
        <div className="settings-row">
          <span>מודל</span>
          <strong>{settings.model}</strong>
        </div>
        <div className="settings-row">
          <span>מסד נתונים</span>
          <strong>{formatDatabaseStatus(settings.database)}</strong>
        </div>
        <div className="settings-row">
          <span>מפתח API</span>
          <strong>{settings.api_key_present ? 'מוגדר מחוץ לדפדפן' : 'לא קיים'}</strong>
        </div>
      </div>

      <div className="safety-note">
        <ShieldCheck size={18} aria-hidden="true" />
        <p>{settings.disclaimer}</p>
      </div>

      {usage ? (
        <div className="usage-grid" aria-label="שימוש היום">
          <div>
            <span>בקשות צ'אט</span>
            <strong>{usage.chat_requests_count}</strong>
          </div>
          <div>
            <span>ניתוחי תמונה</span>
            <strong>{usage.image_analysis_count}</strong>
          </div>
          <div>
            <span>סיכומים</span>
            <strong>{usage.summary_requests_count}</strong>
          </div>
          <div>
            <span>טוקנים משוערים</span>
            <strong>{usage.estimated_tokens_total.toLocaleString()}</strong>
          </div>
          <div>
            <span>תקציב שנותר</span>
            <strong>{usage.tokens_remaining.toLocaleString()}</strong>
          </div>
          <div>
            <span>תקציב יומי</span>
            <strong>{usage.daily_ai_token_limit.toLocaleString()}</strong>
          </div>
        </div>
      ) : null}

      <div className="settings-actions">
        <button className="ghost-button" type="button" onClick={handleExport} disabled={actionStatus === 'busy'}>
          <Download size={16} aria-hidden="true" />
          ייצוא
        </button>
        <button className="ghost-button danger-button" type="button" onClick={handleReset} disabled={actionStatus === 'busy'}>
          <RotateCcw size={16} aria-hidden="true" />
          {resetArmed ? 'אישור איפוס' : 'איפוס נתונים מקומיים'}
        </button>
      </div>

      {actionMessage ? <p className={actionStatus === 'error' ? 'error-text' : 'success-text'}>{actionMessage}</p> : null}

      {exportPreview ? (
        <label className="export-preview">
          תצוגת ייצוא
          <textarea readOnly value={exportPreview} />
        </label>
      ) : null}
    </section>
  );
}
