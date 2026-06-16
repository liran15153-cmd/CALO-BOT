import { Download, RotateCcw, ShieldCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { exportSettingsData, fetchSettings, fetchUsage, resetLocalData, type SettingsState, type UsageState } from './api';

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
    const data = await exportSettingsData();
    setExportData(data);
    setActionMessage('Export ready');
    setActionStatus('idle');
  }

  async function handleReset() {
    if (!resetArmed) {
      setResetArmed(true);
      setActionMessage('Click reset again to confirm deletion.');
      return;
    }
    setActionMessage('');
    setActionStatus('busy');
    try {
      const result = await resetLocalData();
      setExportData(null);
      setResetArmed(false);
      setActionMessage(`${result.deleted_records} records deleted`);
      const [settingsData, usageData] = await Promise.all([fetchSettings(), fetchUsage()]);
      setSettings(settingsData);
      setUsage(usageData);
      setActionStatus('idle');
    } catch {
      setActionStatus('error');
      setActionMessage('Reset failed');
    }
  }

  if (status === 'loading') {
    return (
      <section className="panel settings-panel">
        <p>Loading settings...</p>
      </section>
    );
  }

  if (status === 'error' || !settings) {
    return (
      <section className="panel settings-panel">
        <h3>Settings unavailable</h3>
        <p className="error-text">The backend did not return settings.</p>
      </section>
    );
  }

  return (
    <section className="panel settings-panel">
      <div className="panel-heading">
        <h3>Provider and data controls</h3>
        <p>Local configuration status and data controls for this machine.</p>
      </div>

      <div className="settings-grid">
        <div className="settings-row">
          <span>AI provider</span>
          <strong>{settings.ai_provider}</strong>
        </div>
        <div className="settings-row">
          <span>Model</span>
          <strong>{settings.model}</strong>
        </div>
        <div className="settings-row">
          <span>Database</span>
          <strong>{settings.database}</strong>
        </div>
        <div className="settings-row">
          <span>API key</span>
          <strong>{settings.api_key_present ? 'configured outside browser' : 'not present'}</strong>
        </div>
      </div>

      <div className="safety-note">
        <ShieldCheck size={18} aria-hidden="true" />
        <p>{settings.disclaimer}</p>
      </div>

      {usage ? (
        <div className="usage-grid" aria-label="Usage today">
          <div>
            <span>Chat requests</span>
            <strong>{usage.chat_requests_count}</strong>
          </div>
          <div>
            <span>Image analysis</span>
            <strong>{usage.image_analysis_count}</strong>
          </div>
          <div>
            <span>Summaries</span>
            <strong>{usage.summary_requests_count}</strong>
          </div>
          <div>
            <span>Estimated tokens</span>
            <strong>{usage.estimated_tokens_in + usage.estimated_tokens_out}</strong>
          </div>
        </div>
      ) : null}

      <div className="settings-actions">
        <button className="ghost-button" type="button" onClick={handleExport} disabled={actionStatus === 'busy'}>
          <Download size={16} aria-hidden="true" />
          Export
        </button>
        <button className="ghost-button danger-button" type="button" onClick={handleReset} disabled={actionStatus === 'busy'}>
          <RotateCcw size={16} aria-hidden="true" />
          {resetArmed ? 'Confirm reset' : 'Reset local data'}
        </button>
      </div>

      {actionMessage ? <p className="success-text">{actionMessage}</p> : null}

      {exportPreview ? (
        <label className="export-preview">
          Export preview
          <textarea readOnly value={exportPreview} />
        </label>
      ) : null}
    </section>
  );
}
