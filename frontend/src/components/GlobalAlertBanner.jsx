import { useState, useContext, useEffect } from 'react';
import { DbContext } from '../App';
import { AlertTriangle, X, ArrowRight } from 'lucide-react';

export default function GlobalAlertBanner() {
  const context = useContext(DbContext) || {};
  const { intelligenceAlerts, setActiveSection } = context;

  // Local state to hide banner for the current session
  const [isDismissed, setIsDismissed] = useState(false);

  // Reset dismissed state if totalUnacknowledged increases (optional, but good UX)
  const totalUnacknowledged = intelligenceAlerts?.totalUnacknowledged || 0;
  const criticalUnacknowledged = intelligenceAlerts?.criticalUnacknowledged || 0;
  const highUnacknowledged = intelligenceAlerts?.highUnacknowledged || 0;

  useEffect(() => {
    // If user has dismissed it, keep it dismissed unless a new critical alert comes in
    // For simplicity, we just use session state.
    const dismissedKey = 'alert_banner_dismissed';
    if (sessionStorage.getItem(dismissedKey) === 'true') {
      setIsDismissed(true);
    }
  }, []);

  const handleDismiss = () => {
    setIsDismissed(true);
    sessionStorage.setItem('alert_banner_dismissed', 'true');
  };

  const handleViewAlerts = () => {
    if (setActiveSection) {
      setActiveSection('alerts');
    }
  };

  if (!intelligenceAlerts || totalUnacknowledged === 0 || isDismissed) {
    return null;
  }

  const isCritical = criticalUnacknowledged > 0;
  const count = isCritical ? criticalUnacknowledged : highUnacknowledged;
  const typeText = isCritical ? 'critical' : 'high severity';

  const bgColor = isCritical ? 'bg-red-600 dark:bg-red-900/80' : 'bg-orange-500 dark:bg-orange-800/80';
  const textColor = 'text-white';
  const hoverColor = isCritical ? 'hover:bg-red-700 dark:hover:bg-red-900' : 'hover:bg-orange-600 dark:hover:bg-orange-800';
  const iconColor = isCritical ? 'text-red-200' : 'text-orange-200';

  return (
    <div className={`${bgColor} ${textColor} px-4 py-3 flex items-center justify-between shadow-md relative z-40 transition-all`}>
      <div className="flex items-center gap-3">
        <div className={`p-1.5 rounded-full bg-white/20 ${iconColor}`}>
          <AlertTriangle size={18} />
        </div>
        <p className="font-bold text-sm">
          {count} {typeText} competitive alert{count !== 1 ? 's' : ''} require{count === 1 ? 's' : ''} your attention
        </p>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={handleViewAlerts}
          className={`flex items-center gap-1.5 text-xs font-extrabold bg-white text-slate-900 px-4 py-1.5 rounded-lg shadow-sm hover:bg-slate-100 transition-colors`}
        >
          View Alerts <ArrowRight size={14} />
        </button>
        
        <button 
          onClick={handleDismiss}
          className="text-white/70 hover:text-white p-1 rounded-md transition-colors"
          aria-label="Dismiss alert banner"
        >
          <X size={18} />
        </button>
      </div>
    </div>
  );
}
