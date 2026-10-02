import { useState, useContext, useEffect } from 'react';
import { DbContext } from '../App';
import { 
  TrendingUp, Loader2, AlertCircle, TrendingDown, Clock,
  Target, Zap, ShieldAlert, BarChart3, RefreshCw
} from 'lucide-react';
import { getIntelligenceTrends } from '../api';
import { getTrendHumanReadableLabel, getImpactBadgeStyle } from '../constants';

export default function TrendsSection() {
  const context = useContext(DbContext) || {};
  const { companyProfile, intelligenceTrends, refreshAlertsAndTrends, checkStatus, startCheck } = context;

  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchTrends = async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setError('');
    try {
      const data = await getIntelligenceTrends();
      setTrendsData(data);
      if (refreshAlertsAndTrends) refreshAlertsAndTrends();
    } catch (err) {
      console.error('Error fetching trends:', err);
      setError('Failed to load competitive trends. Please try again.');
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  useEffect(() => {
    if (intelligenceTrends && !trendsData) {
      setTrendsData(intelligenceTrends);
      fetchTrends(false);
    } else {
      fetchTrends(true);
    }
  }, []);

  if (loading && !trendsData) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 animate-pulse pb-12">
        <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-24 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800" />
          ))}
        </div>
        <div className="h-64 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 mt-6" />
      </div>
    );
  }

  if (error && !trendsData) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/40 rounded-3xl p-8 text-center space-y-4 max-w-xl mx-auto">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">{error}</h3>
        <button
          onClick={() => fetchTrends(true)}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow-md"
        >
          <RefreshCw size={16} /> Retry Loading
        </button>
      </div>
    );
  }

  const trendsList = trendsData?.trends || [];
  const activeTrends = trendsList.filter(t => t.isActive);

  // Group by competitor
  const trendsByCompetitor = activeTrends.reduce((acc, trend) => {
    const comp = trend.competitorName || 'Unknown';
    if (!acc[comp]) acc[comp] = [];
    acc[comp].push(trend);
    return acc;
  }, {});

  // Sort each group's trends by severity
  Object.keys(trendsByCompetitor).forEach(comp => {
    trendsByCompetitor[comp].sort((a, b) => {
      const sevMap = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
      return (sevMap[b.severity] || 0) - (sevMap[a.severity] || 0);
    });
  });

  // Calculate days since creation
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
            <TrendingUp size={30} className="text-blue-600 dark:text-blue-400" /> Competitive Trends
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Patterns detected in competitor behavior over time.
          </p>
        </div>
        
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

      {/* ── MINIMUM DATA WARNING ── */}
      {daysRemaining > 0 && activeTrends.length === 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/40 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400 font-extrabold text-lg">
            <Clock size={20} /> Trend detection is gathering data
          </div>
          <p className="text-blue-800 dark:text-blue-300/90 text-sm font-medium">
            Trend detection will activate in <strong>{daysRemaining} day{daysRemaining !== 1 ? 's' : ''}</strong>. We need at least 14 days of monitoring data to establish a baseline and detect reliable patterns.
          </p>
          <div className="w-full bg-blue-200/50 dark:bg-blue-900/40 rounded-full h-2 mt-2">
            <div 
              className="bg-blue-600 dark:bg-blue-500 h-full rounded-full transition-all"
              style={{ width: `${Math.max(5, (daysSinceCreation / 14) * 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* ── SUMMARY BAR ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Active Trends', val: trendsData?.totalActive || 0, icon: BarChart3, color: 'text-blue-600' },
          { label: 'Critical', val: trendsData?.criticalCount || 0, icon: ShieldAlert, color: 'text-red-500' },
          { label: 'High Priority', val: trendsData?.highCount || 0, icon: AlertCircle, color: 'text-orange-500' },
          { label: 'Competitors Trending', val: trendsData?.trendingCompetitorsCount || 0, icon: Zap, color: 'text-purple-500' },
        ].map(stat => (
          <div key={stat.label} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm flex items-center justify-between">
            <div>
              <div className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider mb-1">{stat.label}</div>
              <div className="text-2xl font-black text-slate-900 dark:text-white">{stat.val}</div>
            </div>
            <div className={`p-2 bg-slate-50 dark:bg-slate-800 rounded-xl ${stat.color}`}>
              <stat.icon size={20} />
            </div>
          </div>
        ))}
      </div>

      {/* ── EMPTY STATE ── */}
      {daysRemaining === 0 && activeTrends.length === 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-12 text-center space-y-4">
          <TrendingUp size={48} className="text-slate-300 dark:text-slate-700 mx-auto" />
          <h3 className="text-xl font-extrabold text-slate-900 dark:text-white">
            No trends detected yet
          </h3>
          <p className="text-slate-500 text-sm max-w-md mx-auto mb-4">
            Run a check to analyze recent data for emerging trends. Trend detection requires at least 14 days of historical data to establish a baseline.
          </p>
          <button
            onClick={startCheck}
            disabled={checkStatus?.status === 'RUNNING'}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition-all shadow-sm"
          >
            <RefreshCw size={14} /> Check Now
          </button>
        </div>
      )}

      {/* ── TRENDS BY COMPETITOR ── */}
      <div className="space-y-8">
        {Object.entries(trendsByCompetitor).map(([compName, trends]) => (
          <section key={compName} className="space-y-4">
            <h2 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
              <span className="w-2 h-6 bg-blue-600 rounded-full" /> {compName}
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {trends.map(trend => (
                <div key={trend.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all space-y-4 flex flex-col">
                  
                  {/* Header */}
                  <div className="flex justify-between items-start gap-3">
                    <span className="text-sm font-extrabold text-slate-900 dark:text-white">
                      {getTrendHumanReadableLabel(trend.trendType)}
                    </span>
                    <span className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full border ${getImpactBadgeStyle(trend.severity)}`}>
                      {trend.severity}
                    </span>
                  </div>

                  {/* Change Indicator */}
                  <div className="bg-slate-50 dark:bg-slate-950/50 rounded-2xl p-4 border border-slate-100 dark:border-slate-800 flex items-center gap-4">
                    <div className={`p-2 rounded-full ${trend.changePercent >= 0 ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400'}`}>
                      {trend.changePercent >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                    </div>
                    <div>
                      <div className={`font-black text-lg ${trend.changePercent >= 0 ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-700 dark:text-red-400'}`}>
                        {trend.changePercent > 0 ? '+' : ''}{trend.changePercent}% vs baseline
                      </div>
                      <div className="text-xs text-slate-500 font-semibold">
                        Current: {trend.currentValue} | Baseline: {trend.baselineValue}
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
                    {trend.description}
                  </p>

                  <div className="flex-1" />

                  {/* Context & Actions */}
                  <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                    {trend.strategicImplication && (
                      <div className="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30 rounded-xl p-3 space-y-1">
                        <div className="text-[10px] font-extrabold uppercase tracking-wider text-blue-800 dark:text-blue-400">
                          What this means for you
                        </div>
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                          {trend.strategicImplication}
                        </p>
                      </div>
                    )}

                    {trend.recommendedAction && (
                      <div className="flex items-start gap-2 bg-slate-50 dark:bg-slate-800/50 rounded-xl p-3">
                        <Target size={16} className="text-slate-400 shrink-0 mt-0.5" />
                        <div>
                          <div className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500 mb-0.5">
                            Recommended Action
                          </div>
                          <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                            {trend.recommendedAction}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Period Footer */}
                  <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wide text-right pt-2">
                    Detected period: {trend.periodStart} to {trend.periodEnd}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

    </div>
  );
}
