import { useState, useContext, useEffect } from 'react';
import { DbContext } from '../App';
import { 
  Bell, Loader2, AlertCircle, CheckCircle2, TrendingUp,
  Clock, Eye, Target, RefreshCw
} from 'lucide-react';
import { getIntelligenceAlerts, acknowledgeAnomaly } from '../api';
import { 
  getUrgencyBadgeStyle, 
  getTypeBadgeStyle, 
  getImpactBadgeStyle,
  formatRelativeTime 
} from '../constants';

export default function AlertsSection() {
  const context = useContext(DbContext) || {};
  const { companyProfile, intelligenceAlerts, refreshAlertsAndTrends, showToast, checkStatus, startCheck } = context;

  const [alertsData, setAlertsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('ALL'); // ALL, TRENDS, ANOMALIES, ACKNOWLEDGED
  const [acknowledgingIds, setAcknowledgingIds] = useState(new Set());

  const fetchAlerts = async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setError('');
    try {
      const data = await getIntelligenceAlerts();
      setAlertsData(data);
      // Also trigger a background refresh of global context
      if (refreshAlertsAndTrends) refreshAlertsAndTrends();
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError('Failed to load competitive alerts. Please try again.');
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  useEffect(() => {
    // If context already has alerts, use them immediately while fetching fresh ones
    if (intelligenceAlerts && !alertsData) {
      setAlertsData(intelligenceAlerts);
      fetchAlerts(false); // background fetch
    } else {
      fetchAlerts(true);
    }
  }, []);

  const handleAcknowledge = async (alertId, isTrend) => {
    setAcknowledgingIds(prev => new Set(prev).add(alertId));
    try {
      if (!isTrend) {
        await acknowledgeAnomaly(alertId);
      }
      // Optimistically update local state
      setAlertsData(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          totalUnacknowledged: Math.max(0, prev.totalUnacknowledged - 1),
          alerts: prev.alerts.map(a => 
            a.id === alertId ? { ...a, isAcknowledged: true, acknowledgedAt: new Date().toISOString() } : a
          )
        };
      });
      showToast('Alert marked as acknowledged.');
      if (refreshAlertsAndTrends) refreshAlertsAndTrends();
    } catch (err) {
      showToast('Failed to acknowledge alert.', 'error');
    } finally {
      setAcknowledgingIds(prev => {
        const next = new Set(prev);
        next.delete(alertId);
        return next;
      });
    }
  };

  const getUrgencyIcon = (urgency = '') => {
    const norm = urgency.toUpperCase();
    if (norm === 'ACT_NOW') return <Clock size={14} />;
    if (norm === 'MONITOR') return <Eye size={14} />;
    return <Eye size={14} />;
  };

  const getUrgencyText = (urgency = '') => {
    const norm = urgency.toUpperCase();
    if (norm === 'ACT_NOW') return 'Immediate action recommended';
    if (norm === 'MONITOR') return 'Monitor closely';
    return 'Keep watching';
  };

  if (loading && !alertsData) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 animate-pulse pb-12">
        <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
        <div className="flex gap-4">
          <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-24" />
          <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-24" />
        </div>
        <div className="space-y-4 mt-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-48 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800" />
          ))}
        </div>
      </div>
    );
  }

  if (error && !alertsData) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/40 rounded-3xl p-8 text-center space-y-4 max-w-xl mx-auto">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">{error}</h3>
        <button
          onClick={() => fetchAlerts(true)}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow-md"
        >
          <RefreshCw size={16} /> Retry Loading
        </button>
      </div>
    );
  }

  const alerts = alertsData?.alerts || [];
  
  // Filtering logic
  const allUnack = alerts.filter(a => !a.isAcknowledged);
  const trendsUnack = allUnack.filter(a => a.type === 'TREND');
  const anomaliesUnack = allUnack.filter(a => a.type === 'ANOMALY');
  const acknowledged = alerts.filter(a => a.isAcknowledged);

  const getFilteredAlerts = () => {
    switch (activeTab) {
      case 'TRENDS': return trendsUnack;
      case 'ANOMALIES': return anomaliesUnack;
      case 'ACKNOWLEDGED': return acknowledged;
      case 'ALL':
      default: return allUnack;
    }
  };

  const displayedAlerts = getFilteredAlerts().sort((a, b) => {
    // Sort logic: Severity (CRITICAL > HIGH > MEDIUM > LOW) then date
    const sevMap = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
    const sevDiff = (sevMap[b.severity] || 0) - (sevMap[a.severity] || 0);
    if (sevDiff !== 0) return sevDiff;
    return new Date(b.detectedAt || 0).getTime() - new Date(a.detectedAt || 0).getTime();
  });

  // Calculate days since company creation to show informative empty state
  const createdAt = companyProfile?.createdAt || companyProfile?.created_at;
  let daysSinceCreation = 30; // default to > 14
  if (createdAt) {
    const diffTime = Math.abs(Date.now() - new Date(createdAt).getTime());
    daysSinceCreation = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }
  const daysRemaining = Math.max(0, 14 - daysSinceCreation);

  return (
    <div className="animate-fade-in-up max-w-5xl mx-auto space-y-8 pb-12">
      
      {/* ── HEADER ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
            <Bell size={30} className="text-blue-600 dark:text-blue-400" /> Competitive Alerts
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Critical trends and anomalies detected in your market.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={startCheck}
            disabled={checkStatus?.status === 'RUNNING'}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-xl transition-all shadow-md text-sm disabled:opacity-50 shrink-0"
          >
            {checkStatus?.status === 'RUNNING' ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Checking...
              </>
            ) : (
              <>
                <RefreshCw size={16} />
                Check Now
              </>
            )}
          </button>
          
          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-2 rounded-xl text-sm font-bold shadow-sm hidden sm:block">
            {alertsData?.totalUnacknowledged || 0} unacknowledged alert{(alertsData?.totalUnacknowledged || 0) !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
      
      {/* Progress Card if running */}
      {checkStatus?.status === 'RUNNING' && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex justify-between items-center text-blue-700 dark:text-blue-400 font-bold text-sm">
            <div className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              Checking competitor activity...
            </div>
            <span>{checkStatus.progress}%</span>
          </div>
          <div className="w-full bg-blue-200/50 dark:bg-blue-900/50 rounded-full h-2 overflow-hidden">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${checkStatus.progress}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-blue-600/80 dark:text-blue-400/80 font-medium">
            <span>Current Step: {checkStatus.currentStep}</span>
            <span>Docs Found: {checkStatus.documentsFound} | Processed: {checkStatus.documentsProcessed}</span>
          </div>
        </div>
      )}

      {/* ── MINIMUM DATA WARNING FOR ANOMALIES ── */}
      {daysRemaining > 0 && activeTab === 'ANOMALIES' && anomaliesUnack.length === 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/40 rounded-2xl p-4 flex items-center gap-3 text-blue-700 dark:text-blue-400 font-medium text-sm">
          <AlertCircle size={20} className="shrink-0" />
          <p>
            Anomaly detection will activate in {daysRemaining} day{daysRemaining !== 1 ? 's' : ''}. We need at least 14 days of monitoring data to detect patterns.
          </p>
        </div>
      )}

      {/* ── TABS ── */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 dark:border-slate-800 pb-4">
        {[
          { id: 'ALL', label: 'All Alerts', count: allUnack.length },
          { id: 'TRENDS', label: 'Trends', count: trendsUnack.length },
          { id: 'ANOMALIES', label: 'Anomalies', count: anomaliesUnack.length },
          { id: 'ACKNOWLEDGED', label: 'Acknowledged', count: acknowledged.length }
        ].map(tab => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all border ${
                isActive
                  ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 border-slate-900 dark:border-white shadow-sm'
                  : 'bg-white text-slate-600 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/60'
              }`}
            >
              <span>{tab.label}</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold ${
                isActive
                  ? 'bg-blue-600 text-white dark:bg-blue-500'
                  : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300'
              }`}>
                {tab.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* ── ALERTS LIST ── */}
      <div className="space-y-4">
        {displayedAlerts.length === 0 ? (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-12 text-center space-y-4">
            <CheckCircle2 size={48} className="text-emerald-500 mx-auto" />
            <h3 className="text-xl font-extrabold text-slate-900 dark:text-white">
              No alerts generated yet
            </h3>
            <p className="text-slate-500 text-sm max-w-md mx-auto mb-4">
              Run a check to scan for new alerts. Your competitive landscape looks stable otherwise.
            </p>
            <button
              onClick={startCheck}
              disabled={checkStatus?.status === 'RUNNING'}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition-all shadow-sm"
            >
              <RefreshCw size={14} /> Check Now
            </button>
          </div>
        ) : (
          displayedAlerts.map(alert => (
            <div 
              key={alert.id}
              className={`bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm flex flex-col md:flex-row md:items-start justify-between gap-6 transition-all ${
                alert.isAcknowledged ? 'opacity-70 grayscale-[20%]' : 'hover:shadow-md'
              }`}
            >
              <div className="space-y-4 flex-1">
                {/* Top Row */}
                <div className="flex flex-wrap items-center gap-3">
                  <span className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full border ${getImpactBadgeStyle(alert.severity)}`}>
                    {alert.severity}
                  </span>
                  <span className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full border ${getTypeBadgeStyle(alert.type)}`}>
                    {alert.type}
                  </span>
                  <span className="text-xs font-extrabold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md">
                    {alert.competitorName}
                  </span>
                  <span className="text-xs font-semibold text-slate-400">
                    {formatRelativeTime(alert.detectedAt)}
                  </span>
                </div>

                {/* Title & Desc */}
                <div className="space-y-1">
                  <h3 className="text-lg md:text-xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
                    {alert.title}
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                    {alert.description}
                  </p>
                </div>

                {/* Urgency & Action */}
                <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6 pt-2">
                  <div className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-xl border ${getUrgencyBadgeStyle(alert.urgency)}`}>
                    {getUrgencyIcon(alert.urgency)}
                    <span>{getUrgencyText(alert.urgency)}</span>
                  </div>

                  {alert.recommendedAction && (
                    <div className="flex items-start gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
                      <Target size={14} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase tracking-wider mb-0.5">Suggested Action</span>
                        {alert.recommendedAction}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Column */}
              <div className="shrink-0 flex flex-col items-start md:items-end gap-2 md:w-48 border-t md:border-t-0 md:border-l border-slate-100 dark:border-slate-800 pt-4 md:pt-0 md:pl-6">
                {!alert.isAcknowledged ? (
                  <button
                    onClick={() => handleAcknowledge(alert.id, alert.type === 'TREND')}
                    disabled={acknowledgingIds.has(alert.id)}
                    className="w-full inline-flex justify-center items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 font-bold px-4 py-2.5 rounded-xl text-xs transition-colors shadow-sm disabled:opacity-50"
                  >
                    {acknowledgingIds.has(alert.id) ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <CheckCircle2 size={14} className="text-emerald-500" />
                    )}
                    Mark Acknowledged
                  </button>
                ) : (
                  <div className="text-right w-full space-y-1">
                    <div className="inline-flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 text-xs font-bold bg-emerald-50 dark:bg-emerald-900/20 px-3 py-1 rounded-lg">
                      <CheckCircle2 size={14} /> Acknowledged
                    </div>
                    {alert.acknowledgedAt && (
                      <div className="text-[10px] text-slate-400 font-medium">
                        {formatRelativeTime(alert.acknowledgedAt)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
}
