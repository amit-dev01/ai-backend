import { useState, useEffect, useContext } from 'react';
import { DbContext } from '../App';
import { 
  Rss, Filter, RefreshCw, ExternalLink, ChevronDown, ChevronUp, 
  Loader2, AlertCircle, Newspaper, Sparkles 
} from 'lucide-react';
import { getIntelligenceFeed } from '../api';
import { 
  EVENT_TYPES, 
  getEventTypeBadgeStyle, 
  getImpactBadgeStyle, 
  getSentimentDotColor, 
  formatRelativeTime 
} from '../constants';

export default function MarketIntelligenceSection() {
  const context = useContext(DbContext) || {};
  const { 
    acceptedCompetitors, 
    intelligenceStats, 
    checkStatus,
    startCheck,
    selectedCompetitorFilter,
    setSelectedCompetitorFilter
  } = context;

  // Filter States
  const [selectedCompetitor, setSelectedCompetitor] = useState(selectedCompetitorFilter || 'All Competitors');
  const [selectedEventType, setSelectedEventType] = useState('All Events');
  const [selectedImpact, setSelectedImpact] = useState('All');

  // Feed Data & Pagination States
  const [documents, setDocuments] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');

  // Expanded Cards State (set of document IDs)
  const [expandedCards, setExpandedCards] = useState(new Set());

  // Sync selectedCompetitor with global context filter if updated externally
  useEffect(() => {
    if (selectedCompetitorFilter) {
      setSelectedCompetitor(selectedCompetitorFilter);
    }
  }, [selectedCompetitorFilter]);

  const limit = 20;

  // Fetch feed with current filters
  const fetchFeed = async (isLoadMore = false, newOffset = 0) => {
    if (isLoadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }
    setError('');

    try {
      // Resolve competitor ID if an accepted competitor name is selected
      let compIdParam = 'all';
      if (selectedCompetitor !== 'All Competitors') {
        const foundComp = acceptedCompetitors.find(
          c => c.name?.toLowerCase() === selectedCompetitor.toLowerCase() || c.id === selectedCompetitor
        );
        compIdParam = foundComp ? foundComp.id : selectedCompetitor;
      }

      const res = await getIntelligenceFeed({
        competitorId: compIdParam,
        eventType: selectedEventType,
        impact: selectedImpact,
        limit,
        offset: newOffset
      });

      const docsList = Array.isArray(res) ? res : res.documents || [];
      const totalDocs = typeof res.total === 'number' ? res.total : docsList.length;

      if (isLoadMore) {
        setDocuments(prev => [...prev, ...docsList]);
      } else {
        setDocuments(docsList);
      }
      setTotalCount(totalDocs);
    } catch (err) {
      console.error('Error fetching intelligence feed:', err);
      setError('Failed to load intelligence feed. Please try again.');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // Trigger fetch whenever filters change
  useEffect(() => {
    setOffset(0);
    fetchFeed(false, 0);
  }, [selectedCompetitor, selectedEventType, selectedImpact]);

  // Load More handler
  const handleLoadMore = () => {
    const nextOffset = offset + limit;
    setOffset(nextOffset);
    fetchFeed(true, nextOffset);
  };

  // Toggle Card Expansion
  const toggleExpandCard = (id) => {
    setExpandedCards(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Counts for Impact Level Tabs
  const totalEventsCount = intelligenceStats?.documentsThisWeek ?? intelligenceStats?.total ?? 0;
  const criticalCount = intelligenceStats?.criticalEvents ?? 0;
  const highCount = intelligenceStats?.highEvents ?? 0;
  const mediumCount = intelligenceStats?.mediumEvents ?? 0;
  const lowCount = intelligenceStats?.lowEvents ?? 0;

  const getImpactTabBadge = (lvl) => {
    switch (lvl) {
      case 'Critical': return criticalCount;
      case 'High': return highCount;
      case 'Medium': return mediumCount;
      case 'Low': return lowCount;
      default: return totalEventsCount;
    }
  };

  // Check if completely empty state for new users
  const isNewUserEmpty = (intelligenceStats?.documentsThisWeek === 0 || intelligenceStats?.total === 0) && documents.length === 0 && !loading;

  return (
    <div className="animate-fade-in-up max-w-5xl mx-auto space-y-8 pb-12">
      
      {/* ── HEADER SECTION ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
            <Rss size={30} className="text-blue-600 dark:text-blue-400" /> Market Intelligence
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Real-time competitive activity across your market.
          </p>
        </div>

        <button
          onClick={startCheck}
          disabled={checkStatus?.status === 'RUNNING'}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl transition-all shadow-md text-sm disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
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

      {/* ── FILTERS BAR ── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          
          {/* Competitor Dropdown */}
          <div className="space-y-1.5">
            <label className="text-xs font-extrabold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Filter size={14} /> Competitor
            </label>
            <select
              value={selectedCompetitor}
              onChange={(e) => {
                setSelectedCompetitor(e.target.value);
                if (setSelectedCompetitorFilter) setSelectedCompetitorFilter(e.target.value);
              }}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-900 dark:text-white font-semibold outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="All Competitors">All Competitors</option>
              {acceptedCompetitors.map(c => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Event Type Dropdown */}
          <div className="space-y-1.5">
            <label className="text-xs font-extrabold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <Sparkles size={14} /> Event Type
            </label>
            <select
              value={selectedEventType}
              onChange={(e) => setSelectedEventType(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-900 dark:text-white font-semibold outline-none focus:ring-2 focus:ring-blue-600"
            >
              {EVENT_TYPES.map(type => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Impact Level Tabs */}
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="text-xs font-extrabold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
            Impact Level
          </div>
          <div className="flex flex-wrap gap-2">
            {['All', 'Critical', 'High', 'Medium', 'Low'].map(lvl => {
              const isActive = selectedImpact.toLowerCase() === lvl.toLowerCase();
              const badgeCount = getImpactTabBadge(lvl);

              return (
                <button
                  key={lvl}
                  onClick={() => setSelectedImpact(lvl)}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                    isActive
                      ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 border-slate-900 dark:border-white shadow-sm'
                      : 'bg-slate-50 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60'
                  }`}
                >
                  <span>{lvl}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                  }`}>
                    {badgeCount}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── LOADING STATE: SKELETON CARDS ── */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm animate-pulse space-y-4">
              <div className="flex justify-between items-center">
                <div className="flex gap-2">
                  <div className="h-6 w-24 bg-slate-200 dark:bg-slate-800 rounded-full" />
                  <div className="h-6 w-28 bg-slate-200 dark:bg-slate-800 rounded-full" />
                </div>
                <div className="h-4 w-20 bg-slate-200 dark:bg-slate-800 rounded" />
              </div>
              <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
              <div className="h-12 bg-slate-200 dark:bg-slate-800 rounded w-full" />
              <div className="flex justify-between items-center pt-2">
                <div className="h-4 w-32 bg-slate-200 dark:bg-slate-800 rounded" />
                <div className="h-4 w-24 bg-slate-200 dark:bg-slate-800 rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── ERROR STATE ── */}
      {!loading && error && (
        <div className="bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/40 rounded-3xl p-8 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">{error}</h3>
          <button
            onClick={() => fetchFeed(false, 0)}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition-all shadow-md"
          >
            <RefreshCw size={16} /> Retry Loading
          </button>
        </div>
      )}

      {/* ── EMPTY STATE FOR NEW USERS ── */}
      {!loading && !error && isNewUserEmpty && (
        <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-6 max-w-2xl mx-auto shadow-sm">
          <div className="w-16 h-16 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 mx-auto flex items-center justify-center">
            <Newspaper size={32} />
          </div>
          
          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
              No intelligence collected yet
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
              Click Check Now to fetch the latest competitor activity and build your intelligence feed.
            </p>
          </div>

          <button
            onClick={startCheck}
            disabled={checkStatus?.status === 'RUNNING'}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold px-6 py-3 rounded-xl text-sm transition-all shadow-md disabled:opacity-80"
          >
            {checkStatus?.status === 'RUNNING' ? (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-white animate-ping" />
                Checking competitor activity...
              </>
            ) : (
              'Check Now'
            )}
          </button>
        </div>
      )}

      {/* ── STANDARD EMPTY STATE ── */}
      {!loading && !error && !isNewUserEmpty && documents.length === 0 && (
        <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-4 max-w-xl mx-auto">
          <Newspaper size={40} className="text-slate-300 dark:text-slate-700 mx-auto" />
          <h3 className="text-xl font-extrabold text-slate-900 dark:text-white">
            No intelligence collected yet
          </h3>
          <p className="text-slate-500 text-xs leading-relaxed">
            Run a check to collect competitor intelligence.
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

      {/* ── INTELLIGENCE FEED CARDS ── */}
      {!loading && !error && documents.length > 0 && (
        <div className="space-y-5">
          {documents.map((doc) => {
            const isExpanded = expandedCards.has(doc.id);
            const impactStyle = getImpactBadgeStyle(doc.impact);
            const typeStyle = getEventTypeBadgeStyle(doc.eventType);
            const sentimentDot = getSentimentDotColor(doc.sentiment);
            const relTime = formatRelativeTime(doc.publishedAt || doc.date);

            const relevanceScore = doc.relevanceScore ?? 85;
            const impactScore = doc.impactScore ?? 88;

            return (
              <div
                key={doc.id}
                onClick={() => toggleExpandCard(doc.id)}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 md:p-7 shadow-sm hover:shadow-md transition-all cursor-pointer space-y-4 relative overflow-hidden"
              >
                {/* Top Row */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`text-[10px] font-extrabold uppercase px-3 py-1 rounded-full border ${impactStyle}`}>
                      {doc.impact || 'MEDIUM'}
                    </span>
                    <span className={`text-[10px] font-extrabold uppercase px-3 py-1 rounded-full border ${typeStyle}`}>
                      {doc.eventType || 'Other'}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs font-semibold text-slate-500 dark:text-slate-400">
                    <span className="text-slate-900 dark:text-white font-extrabold bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-lg">
                      {doc.competitorName}
                    </span>
                    <span>{relTime}</span>
                  </div>
                </div>

                {/* Middle Section */}
                <div className="space-y-2">
                  <h3 className="text-lg md:text-xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                    {doc.title}
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                    {doc.summary}
                  </p>
                </div>

                {/* Bottom Row */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs font-bold text-slate-500">
                  <div className="flex items-center gap-4">
                    {/* Sentiment */}
                    <div className="flex items-center gap-1.5">
                      <span className={`w-2.5 h-2.5 rounded-full ${sentimentDot}`} />
                      <span className="uppercase text-slate-700 dark:text-slate-300">{doc.sentiment || 'NEUTRAL'}</span>
                    </div>

                    {/* Scores */}
                    <span className="text-slate-500">Relevance: <strong className="text-slate-900 dark:text-white">{relevanceScore}/100</strong></span>
                    <span className="text-slate-500">Impact: <strong className="text-blue-600 dark:text-blue-400">{impactScore}/100</strong></span>
                  </div>

                  <div className="flex items-center gap-3">
                    {doc.sourceUrl && (
                      <a
                        href={doc.sourceUrl.startsWith('http') ? doc.sourceUrl : `https://${doc.sourceUrl}`}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline font-bold"
                      >
                        Read source <ExternalLink size={12} />
                      </a>
                    )}
                    <div className="text-slate-400">
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>
                  </div>
                </div>

                {/* Expanded Detail Panel */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 rounded-2xl p-5 space-y-3 animate-fade-in">
                    {doc.relevanceReason && (
                      <div>
                        <div className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider mb-1">
                          Relevance Reason
                        </div>
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 leading-relaxed">
                          {doc.relevanceReason}
                        </p>
                      </div>
                    )}

                    {doc.eventTypeExplanation && (
                      <div>
                        <div className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider mb-1">
                          Event Explanation
                        </div>
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 leading-relaxed">
                          {doc.eventTypeExplanation}
                        </p>
                      </div>
                    )}

                    {doc.additionalContext && (
                      <div>
                        <div className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider mb-1">
                          Additional Market Context
                        </div>
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 leading-relaxed">
                          {doc.additionalContext}
                        </p>
                      </div>
                    )}
                  </div>
                )}

              </div>
            );
          })}
        </div>
      )}

      {/* ── PAGINATION ── */}
      {!loading && !error && documents.length > 0 && (
        <div className="pt-4 flex flex-col items-center gap-3">
          <div className="text-xs font-semibold text-slate-500">
            Showing {documents.length} of {totalCount} intelligence events
          </div>

          {documents.length < totalCount && (
            <button
              onClick={handleLoadMore}
              disabled={loadingMore}
              className="inline-flex items-center gap-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 hover:bg-slate-800 font-extrabold px-6 py-3 rounded-xl text-sm transition-all shadow-md disabled:opacity-50"
            >
              {loadingMore ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Loading more...
                </>
              ) : (
                'Load More'
              )}
            </button>
          )}
        </div>
      )}

    </div>
  );
}
