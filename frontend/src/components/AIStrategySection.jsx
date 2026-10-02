import { useState, useEffect, useContext } from 'react';
import { DbContext } from '../App';
import { 
  Target, ShieldAlert, Lightbulb, Eye, CheckSquare, Square, 
  ArrowRight, Loader2, AlertCircle, RefreshCw, Sparkles, Building,
  Bell, TrendingUp, TrendingDown, Clock
} from 'lucide-react';
import { getIntelligenceSummary, generateIntelligenceSummary } from '../api';
import { formatBriefTimestamp } from '../constants';

export default function AIStrategySection() {
  const context = useContext(DbContext) || {};
  const { 
    companyProfile, 
    checkStatus,
    startCheck, 
    setSelectedCompetitorFilter, 
    setActiveSection,
    showToast
  } = context;

  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Checkbox State for Strategic Recommendations (localStorage keyed by companyId & weeklyBriefGeneratedAt)
  const [checkedRecs, setCheckedRecs] = useState({});

  const companyId = companyProfile?.id || sessionStorage.getItem('company_id') || 'default_co';

  const fetchSummary = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getIntelligenceSummary();
      setSummaryData(data);

      // Load saved recommendation checkboxes from localStorage
      const genAt = data?.weeklyBriefGeneratedAt || 'latest';
      const storageKey = `intelligence_recs_${companyId}_${genAt}`;
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        try {
          setCheckedRecs(JSON.parse(saved));
        } catch (_) {}
      }
    } catch (err) {
      console.error('Error fetching intelligence summary:', err);
      setError('Failed to load AI strategy summary. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const toggleCheckRec = (index) => {
    const genAt = summaryData?.weeklyBriefGeneratedAt || 'latest';
    const storageKey = `intelligence_recs_${companyId}_${genAt}`;

    setCheckedRecs(prev => {
      const next = { ...prev, [index]: !prev[index] };
      localStorage.setItem(storageKey, JSON.stringify(next));
      return next;
    });
  };

  // Click on watchList chip -> filter Market Intelligence by competitor
  const handleWatchListClick = (compName) => {
    if (setSelectedCompetitorFilter) setSelectedCompetitorFilter(compName);
    if (setActiveSection) setActiveSection('market');
  };

  const handleGenerateSummary = async () => {
    if (isGenerating) return;
    setIsGenerating(true);
    showToast('Generating AI Strategy Brief... this may take a few seconds.', 'success');
    
    try {
      await generateIntelligenceSummary();
      
      // Poll/wait and refetch
      setTimeout(async () => {
        await fetchSummary();
        setIsGenerating(false);
        showToast('New AI Strategy Brief is ready!', 'success');
      }, 10000);
      
    } catch (err) {
      console.error(err);
      showToast(err.message || 'Failed to generate AI brief', 'error');
      setIsGenerating(false);
    }
  };

  const getSeverityColor = (severity) => {
    const norm = severity?.toUpperCase();
    if (norm === 'HIGH') return 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 border-red-300 dark:border-red-800';
    if (norm === 'MEDIUM') return 'bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400 border-orange-300 dark:border-orange-800';
    return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border-amber-300 dark:border-amber-800';
  };

  // Urgency badge helper (HIGH red, MEDIUM orange, LOW yellow)
  const getUrgencyBadgeStyle = (urgency = '') => {
    const norm = urgency.toUpperCase();
    if (norm === 'HIGH') return 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 border-red-300 dark:border-red-800';
    if (norm === 'MEDIUM') return 'bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400 border-orange-300 dark:border-orange-800';
    return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border-amber-300 dark:border-amber-800';
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-8 animate-pulse pb-12">
        <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
        <div className="h-40 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-64 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800" />
          <div className="h-64 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800" />
        </div>
      </div>
    );
  }

  if (error && !summaryData) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/40 rounded-3xl p-8 text-center space-y-4 max-w-xl mx-auto">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">{error}</h3>
        <button
          onClick={fetchSummary}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition-all shadow-md"
        >
          <RefreshCw size={16} /> Retry Loading
        </button>
      </div>
    );
  }

  const weeklyBrief = summaryData?.weeklyBrief;
  const generatedAtText = formatBriefTimestamp(summaryData?.weeklyBriefGeneratedAt);
  const topThreats = Array.isArray(summaryData?.topThreats) ? summaryData.topThreats : [];
  const opportunities = Array.isArray(summaryData?.opportunities) ? summaryData.opportunities : [];
  const watchList = Array.isArray(summaryData?.watchList) ? summaryData.watchList : [];
  const recommendations = Array.isArray(summaryData?.strategicRecommendations) ? summaryData.strategicRecommendations : [];

  // Phase 3 Extensions
  const criticalAlerts = Array.isArray(summaryData?.criticalAlerts) ? summaryData.criticalAlerts : [];
  const trendSummary = summaryData?.trendSummary;
  const anomalySummary = summaryData?.anomalySummary;

  const hasNoData = !weeklyBrief && topThreats.length === 0 && opportunities.length === 0 && criticalAlerts.length === 0;

  return (
    <div className="animate-fade-in-up max-w-5xl mx-auto space-y-8 pb-12">
      
      {/* ── HEADER SECTION ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
            <Target size={30} className="text-blue-600 dark:text-blue-400" /> AI Strategy Brief
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Generated from this week's competitive intelligence.
          </p>
          {generatedAtText && (
            <div className="text-xs text-slate-400 font-semibold mt-1">
              {generatedAtText}
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleGenerateSummary}
            disabled={isGenerating || loading}
            className="inline-flex items-center gap-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-100 font-semibold px-5 py-2.5 rounded-xl transition-all shadow-md text-sm disabled:opacity-50 shrink-0"
          >
            {isGenerating ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Generate Fresh AI Brief
              </>
            )}
          </button>
          
          <button
            onClick={startCheck}
            disabled={checkStatus?.status === 'RUNNING'}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl transition-all shadow-md text-sm disabled:opacity-50 shrink-0"
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

      {/* ── NO SUMMARY EMPTY STATE ── */}
      {hasNoData && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-12 text-center space-y-6 max-w-2xl mx-auto shadow-sm">
          <Sparkles size={40} className="text-blue-600 dark:text-blue-400 mx-auto animate-pulse" />
          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              No strategic brief generated yet
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
              Run a check to generate your latest intelligence summary.
            </p>
          </div>
          <button
            onClick={startCheck}
            disabled={checkStatus?.status === 'RUNNING'}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-6 py-3 rounded-xl text-sm transition-all shadow-md"
          >
            {checkStatus?.status === 'RUNNING' ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Checking...
              </>
            ) : (
              <>
                <RefreshCw size={16} /> Check Now
              </>
            )}
          </button>
        </div>
      )}

      {!hasNoData && (
        <>
          {/* ── WEEKLY BRIEF CARD ── */}
          {weeklyBrief && (
            <section className="bg-gradient-to-br from-blue-900 via-slate-900 to-black text-white rounded-3xl p-8 shadow-xl space-y-4 border border-blue-800/40 relative overflow-hidden">
              <div className="flex items-center gap-2.5 text-blue-400 text-xs font-black uppercase tracking-widest">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping" />
                This Week in Your Market
              </div>
              <p className="text-lg md:text-xl font-medium leading-relaxed text-slate-100">
                "{weeklyBrief}"
              </p>
            </section>
          )}

          {/* ── PHASE 3: CRITICAL ALERTS & TRENDS SUMMARIES ── */}
          {(criticalAlerts.length > 0 || trendSummary || anomalySummary) && (
            <section className="space-y-6">
              
              {/* Critical Alerts Block */}
              {criticalAlerts.length > 0 && (
                <div className="bg-red-50/80 dark:bg-red-950/20 border-2 border-red-300 dark:border-red-800/60 rounded-3xl p-6 md:p-8 shadow-sm space-y-4">
                  <div className="flex items-center gap-2.5 text-red-700 dark:text-red-400 font-extrabold text-xl">
                    <Bell size={24} className="animate-wiggle" />
                    Critical Strategy Alerts
                  </div>
                  <div className="space-y-4">
                    {criticalAlerts.map(alert => (
                      <div key={alert.id} className="bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/40 rounded-2xl p-4 shadow-sm">
                        <div className="flex justify-between items-start mb-1">
                          <h4 className="font-extrabold text-slate-900 dark:text-white text-lg">{alert.title}</h4>
                          <span className="text-xs font-black bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 px-2 py-0.5 rounded uppercase">{alert.type}</span>
                        </div>
                        <p className="text-sm font-medium text-slate-700 dark:text-slate-300 leading-relaxed mb-3">
                          {alert.description}
                        </p>
                        {alert.recommendedAction && (
                          <div className="text-xs font-bold text-red-700 dark:text-red-400 flex items-start gap-1.5 pt-2 border-t border-red-100 dark:border-red-900/30">
                            <ArrowRight size={14} className="shrink-0 mt-0.5" />
                            <span>Action: {alert.recommendedAction}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Trend & Anomaly Summary Block */}
              {(trendSummary || anomalySummary) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {trendSummary && (
                    <div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-900/30 rounded-3xl p-6 shadow-sm space-y-3">
                      <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400 font-extrabold text-lg">
                        <TrendingUp size={20} /> Trend Analysis
                      </div>
                      <p className="text-sm text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                        {trendSummary}
                      </p>
                    </div>
                  )}
                  {anomalySummary && (
                    <div className="bg-purple-50 dark:bg-purple-900/10 border border-purple-200 dark:border-purple-900/30 rounded-3xl p-6 shadow-sm space-y-3">
                      <div className="flex items-center gap-2 text-purple-700 dark:text-purple-400 font-extrabold text-lg">
                        <TrendingDown size={20} /> Detected Anomalies
                      </div>
                      <p className="text-sm text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                        {anomalySummary}
                      </p>
                    </div>
                  )}
                </div>
              )}

            </section>
          )}

          {/* ── TOP THREATS & OPPORTUNITIES GRID ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Top Threats Section */}
            <section className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-5">
              <div className="flex items-center gap-2.5 text-red-600 dark:text-red-400 font-extrabold text-xl">
                <ShieldAlert size={24} />
                Top Threats This Week
              </div>

              {topThreats.length === 0 ? (
                <div className="text-sm font-semibold text-slate-400 py-6 text-center">
                  No significant threats detected this week.
                </div>
              ) : (
                <div className="space-y-4">
                  {topThreats.map((threat, idx) => (
                    <div 
                      key={idx}
                      className="bg-red-50/60 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 rounded-2xl p-5 space-y-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full border ${getUrgencyBadgeStyle(threat.urgency)}`}>
                          {threat.urgency || 'MEDIUM'} URGENCY
                        </span>

                        {threat.competitorName && (
                          <span className="flex items-center gap-1 text-xs font-bold text-slate-700 dark:text-slate-300">
                            <Building size={12} className="text-slate-400" />
                            {threat.competitorName}
                          </span>
                        )}
                      </div>

                      <p className="text-sm font-bold text-slate-900 dark:text-white leading-snug">
                        {threat.description}
                      </p>

                      {threat.recommendedAction && (
                        <div className="text-xs font-semibold text-red-700 dark:text-red-400 flex items-start gap-1.5 pt-1 border-t border-red-200/50 dark:border-red-900/40">
                          <ArrowRight size={14} className="shrink-0 mt-0.5" />
                          <span>{threat.recommendedAction}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Opportunities Section */}
            <section className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-5">
              <div className="flex items-center gap-2.5 text-emerald-600 dark:text-emerald-400 font-extrabold text-xl">
                <Lightbulb size={24} />
                Opportunities Identified
              </div>

              {opportunities.length === 0 ? (
                <div className="text-sm font-semibold text-slate-400 py-6 text-center">
                  No specific opportunities identified this week.
                </div>
              ) : (
                <div className="space-y-4">
                  {opportunities.map((opp, idx) => (
                    <div 
                      key={idx}
                      className="bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 rounded-2xl p-5 space-y-3"
                    >
                      <p className="text-sm font-bold text-slate-900 dark:text-white leading-snug">
                        {opp.description}
                      </p>

                      {opp.basis && (
                        <div className="text-xs text-slate-500 font-medium">
                          Based on: <span className="text-slate-700 dark:text-slate-300 font-semibold">{opp.basis}</span>
                        </div>
                      )}

                      {opp.recommendedAction && (
                        <div className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 flex items-start gap-1.5 pt-1 border-t border-emerald-200/50 dark:border-emerald-900/40">
                          <ArrowRight size={14} className="shrink-0 mt-0.5" />
                          <span>{opp.recommendedAction}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

          </div>

          {/* ── WATCH LIST SECTION ── */}
          {watchList.length > 0 && (
            <section className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-4">
              <div className="flex items-center gap-2 text-slate-900 dark:text-white font-extrabold text-xl">
                <Eye size={24} className="text-blue-600 dark:text-blue-400" />
                Watch Closely This Week
              </div>
              <p className="text-xs text-slate-500 font-medium">
                Click any competitor to filter real-time intelligence events.
              </p>

              <div className="flex flex-wrap gap-3 pt-2">
                {watchList.map((compName, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleWatchListClick(compName)}
                    className="inline-flex items-center gap-2 bg-blue-50 hover:bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 dark:text-blue-300 border border-blue-200 dark:border-blue-800 px-4 py-2 rounded-xl text-xs font-extrabold transition-all shadow-sm group"
                  >
                    <Building size={14} />
                    <span>{compName}</span>
                    <ArrowRight size={12} className="opacity-50 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* ── STRATEGIC RECOMMENDATIONS SECTION ── */}
          {recommendations.length > 0 && (
            <section className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-900 dark:text-white font-extrabold text-xl">
                  <CheckSquare size={24} className="text-blue-600 dark:text-blue-400" />
                  Strategic Recommendations
                </div>
                <span className="text-xs font-semibold text-slate-400">
                  {Object.values(checkedRecs).filter(Boolean).length} of {recommendations.length} completed
                </span>
              </div>

              <div className="space-y-3">
                {recommendations.map((rec, idx) => {
                  const isChecked = !!checkedRecs[idx];

                  return (
                    <div
                      key={idx}
                      onClick={() => toggleCheckRec(idx)}
                      className={`flex items-start gap-4 p-4 md:p-5 rounded-2xl border transition-all cursor-pointer ${
                        isChecked
                          ? 'bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 text-slate-400 line-through'
                          : 'bg-white dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 hover:border-blue-300'
                      }`}
                    >
                      <button className="mt-0.5 text-blue-600 dark:text-blue-400 shrink-0">
                        {isChecked ? (
                          <CheckSquare size={20} className="text-emerald-600 dark:text-emerald-400" />
                        ) : (
                          <Square size={20} className="text-slate-400" />
                        )}
                      </button>

                      <div className="flex-1 text-sm md:text-base font-semibold leading-relaxed">
                        <span className="text-blue-600 dark:text-blue-400 font-bold mr-2">{idx + 1}.</span>
                        {rec}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

        </>
      )}

    </div>
  );
}
