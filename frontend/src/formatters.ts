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
