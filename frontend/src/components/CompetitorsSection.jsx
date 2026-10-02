import { useState, useEffect, useRef, useContext } from 'react';
import { DbContext } from '../App';
import { 
  Users, Check, X, Plus, ExternalLink, ShieldAlert, Target, Zap, 
  Sparkles, Loader2, AlertCircle, CheckCircle2, ChevronDown, ChevronUp, Newspaper,
  MoreVertical, Edit3, Archive, RefreshCw, Trash2, Tag, MessageSquare, RotateCcw
} from 'lucide-react';
import { 
  getCompetitors, acceptCompetitor, rejectCompetitor, addManualCompetitor, getIntelligenceFeed,
  updateCompetitor, deleteCompetitor, researchCompetitor, archiveCompetitor, restoreCompetitor
} from '../api';
import { getEventTypeBadgeStyle, getImpactBadgeStyle, formatRelativeTime } from '../constants';
import CompetitorCharts from './CompetitorCharts';

export default function CompetitorsSection() {
  const context = useContext(DbContext) || {};
  const { intelligenceStats } = context;

  const [competitors, setCompetitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('DIRECT'); // DIRECT, INDIRECT, EMERGING
  const [statusFilter, setStatusFilter] = useState('active'); // active, archived, all
  const [summaryStats, setSummaryStats] = useState(null);

  // Modals / Dialogs State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [manualName, setManualName] = useState('');
  const [manualWebsite, setManualWebsite] = useState('');
  const [isSubmittingManual, setIsSubmittingManual] = useState(false);
  const [manualError, setManualError] = useState('');

  const [activeMenuId, setActiveMenuId] = useState(null);
  
  const [editComp, setEditComp] = useState(null);
  const [editData, setEditData] = useState({ name: '', website: '', notes: '' });
  
  const [archiveComp, setArchiveComp] = useState(null);
  const [deleteComp, setDeleteComp] = useState(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Toast state
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success');

  // Expanded Competitor Activity State
  const [activityState, setActivityState] = useState({});

  // Polling ref for pending scores & re-researching
  const pollIntervalRef = useRef(null);
  const researchPollRef = useRef(null);

  const fetchCompetitorsList = async (showLoading = false) => {
    if (showLoading) setLoading(true);
    setError('');
    try {
      const data = await getCompetitors(statusFilter);
      const list = Array.isArray(data) ? data : data.competitors || [];
      setCompetitors(list);
      if (data && data.summary) setSummaryStats(data.summary);
    } catch (err) {
      console.error('Error fetching competitors:', err);
      setError(err.message || 'Failed to load competitors list.');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompetitorsList(true);
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (researchPollRef.current) clearInterval(researchPollRef.current);
    };
  }, [statusFilter]);

  // Polling for unscored or researching
  useEffect(() => {
    const hasPending = competitors.some(
      c => c.competitiveScore === null || c.competitiveScore === undefined || c.isResearching || c.researchStatus === 'IN_PROGRESS'
    );

    if (hasPending) {
      if (!pollIntervalRef.current) {
        pollIntervalRef.current = setInterval(() => {
          fetchCompetitorsList(false);
        }, 10000);
      }
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [competitors]);

  // Global click to close active menu
  useEffect(() => {
    const closeMenu = () => setActiveMenuId(null);
    document.addEventListener('click', closeMenu);
    return () => document.removeEventListener('click', closeMenu);
  }, []);

  const showToast = (msg, type = 'success') => {
    setToastMessage(msg);
    setToastType(type);
    setTimeout(() => setToastMessage(''), 4000);
  };

  const handleAccept = async (id) => {
    try {
      await acceptCompetitor(id);
      setCompetitors(prev => prev.map(c => c.id === id ? { ...c, isAccepted: true } : c));
      showToast('Competitor accepted and confirmed!', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to accept competitor.', 'error');
    }
  };

  const handleReject = async (id) => {
    try {
      await rejectCompetitor(id);
      setCompetitors(prev => prev.map(c => c.id === id ? { ...c, isAccepted: false } : c));
      showToast('Competitor rejected.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to reject competitor.', 'error');
    }
  };

  const handleAddManualCompetitor = async (e) => {
    e.preventDefault();
    if (!manualName.trim() || !manualWebsite.trim()) {
      setManualError('Please enter both company name and website URL.');
      return;
    }
    setIsSubmittingManual(true);
    setManualError('');
    try {
      const result = await addManualCompetitor({ name: manualName.trim(), website: manualWebsite.trim() });
      const newComp = result.competitor || result || {
        id: Date.now().toString(), name: manualName.trim(), website: manualWebsite.trim(),
        type: 'DIRECT', isAccepted: true, source: 'MANUAL', competitiveScore: null, isResearching: true
      };
      setCompetitors(prev => [newComp, ...prev]);
      setIsAddModalOpen(false);
      setManualName(''); setManualWebsite('');
      showToast('Competitor added. We are researching them now.');
    } catch (err) {
      setManualError(err.message || 'Could not add competitor. Please try again.');
    } finally {
      setIsSubmittingManual(false);
    }
  };

  // ── Actions ──
  
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await updateCompetitor(editComp.id, editData);
      setCompetitors(prev => prev.map(c => c.id === editComp.id ? { ...c, name: editData.name, website: editData.website, notes: editData.notes } : c));
      setEditComp(null);
      showToast('Competitor updated successfully', 'success');
    } catch(err) {
      showToast(err.message || 'Failed to update', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleChangeType = async (id, newType) => {
    try {
      const payload = { customType: newType === 'AI' ? null : newType };
      await updateCompetitor(id, payload);
      setCompetitors(prev => prev.map(c => c.id === id ? { ...c, type: newType === 'AI' ? 'DIRECT' : newType, customType: payload.customType } : c));
      showToast('Competitor type updated', 'success');
    } catch(err) {
      showToast(err.message || 'Failed to update type', 'error');
    }
  };

  const handleResearch = async (comp) => {
    if(!window.confirm(`Re-research ${comp.name || comp.companyName}? We will scan their website and update their profile and scores.`)) return;
    try {
      setCompetitors(prev => prev.map(c => c.id === comp.id ? { ...c, isResearching: true, researchStatus: 'IN_PROGRESS' } : c));
      await researchCompetitor(comp.id);
      showToast('Research started');
      // Polling will pick up the IN_PROGRESS state
    } catch(err) {
      showToast(err.message || 'Failed to start research');
      setCompetitors(prev => prev.map(c => c.id === comp.id ? { ...c, isResearching: false, researchStatus: 'FAILED' } : c));
    }
  };

  const handleArchive = async () => {
    setActionLoading(true);
    try {
      await archiveCompetitor(archiveComp.id);
      setCompetitors(prev => prev.filter(c => c.id !== archiveComp.id));
      setArchiveComp(null);
      showToast('Competitor archived. View archived to restore.', 'success');
    } catch(err) {
      showToast(err.message || 'Failed to archive', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestore = async (id) => {
    try {
      await restoreCompetitor(id);
      setCompetitors(prev => prev.filter(c => c.id !== id));
      showToast('Competitor restored', 'success');
    } catch(err) {
      showToast(err.message || 'Failed to restore', 'error');
    }
  };

  const handleDelete = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await deleteCompetitor(deleteComp.id);
      setCompetitors(prev => prev.filter(c => c.id !== deleteComp.id));
      setDeleteComp(null);
      showToast('Competitor permanently deleted', 'success');
    } catch(err) {
      showToast(err.message || 'Deletion not allowed', 'error');
      setDeleteComp(null);
      setDeleteConfirmText('');
    } finally {
      setActionLoading(false);
    }
  };

  const toggleCompetitorActivity = async (compId) => {
    const currentState = activityState[compId] || { expanded: false, docs: [], loading: false };
    const nextExpanded = !currentState.expanded;

    setActivityState(prev => ({ ...prev, [compId]: { ...currentState, expanded: nextExpanded } }));

    if (nextExpanded && (!currentState.docs || currentState.docs.length === 0)) {
      setActivityState(prev => ({ ...prev, [compId]: { ...prev[compId], loading: true } }));
      try {
        const res = await getIntelligenceFeed({ competitorId: compId, limit: 5 });
        const docsList = Array.isArray(res) ? res : res.documents || [];
        setActivityState(prev => ({ ...prev, [compId]: { ...prev[compId], docs: docsList, loading: false } }));
      } catch (err) {
        setActivityState(prev => ({ ...prev, [compId]: { ...prev[compId], docs: [], loading: false } }));
      }
    }
  };

  const getEventCountThisWeek = (comp) => {
    if (!intelligenceStats?.byCompetitor) return 0;
    const compNameNorm = (comp.name || comp.companyName || comp.company_name || '').toLowerCase();
    const found = intelligenceStats.byCompetitor.find(
      b => b.competitorId === comp.id || (b.competitorName && b.competitorName.toLowerCase() === compNameNorm)
    );
    return found?.documentCount || 0;
  };

  const pendingCompetitors = competitors.filter(c => c.isAccepted === null);
  const confirmedCompetitors = competitors.filter(c => c.isAccepted === true);

  const getCompType = (c) => {
    const raw = c.customType || c.type || c.competitiveStatus || c.competitive_status || 'DIRECT';
    const u = raw.toUpperCase();
    if (u.includes('INDIRECT')) return 'INDIRECT';
    if (u.includes('EMERGING')) return 'EMERGING';
    return 'DIRECT';
  };

  const tabFilteredCompetitors = confirmedCompetitors
    .filter(c => getCompType(c) === activeTab)
    .sort((a, b) => (b.competitiveScore || b.ai_score || 0) - (a.competitiveScore || a.ai_score || 0));

  const getTypeBadgeStyle = (typeStr) => {
    switch (typeStr) {
      case 'DIRECT': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800';
      case 'INDIRECT': return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800';
      case 'EMERGING': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800';
      default: return 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';
    }
  };

  const getScoreValue = (comp, field, fallback = 70) => {
    if (comp[field] !== undefined && comp[field] !== null) return comp[field];
    if (comp.scores && comp.scores[field] !== undefined) return comp.scores[field];
    return fallback;
  };

  return (
    <div className="animate-fade-in-up max-w-5xl mx-auto space-y-8 pb-12 relative">
      
      {toastMessage && (
        <div className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-3 animate-fade-in text-sm font-semibold border ${toastType === 'error' ? 'bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400 border-red-200 dark:border-red-900' : 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 border-slate-800 dark:border-slate-200'}`}>
          {toastType === 'error' ? <AlertCircle className="w-5 h-5 text-red-500" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400 dark:text-emerald-600" />}
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
            <Users size={30} className="text-blue-600 dark:text-blue-400" /> Competitor Landscape
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
            Real-time discovered competitors, AI scoring, and market position analysis.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl transition-all shadow-md hover:shadow-lg text-sm"
        >
          <Plus size={18} /> Add Competitor
        </button>
      </div>

      {loading && (
        <div className="space-y-6 animate-pulse">
          <div className="h-24 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-64 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800" />)}
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 rounded-2xl p-6 text-center text-red-600 dark:text-red-400 font-medium">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Summary Stats */}
          {summaryStats && (
            <div className="flex flex-wrap items-center gap-8 py-2 mb-4">
              <div className="flex flex-col"><span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">Total</span><span className="font-black text-slate-900 dark:text-white text-xl">{summaryStats.total}</span></div>
              <div className="flex flex-col"><span className="text-emerald-600 text-[10px] uppercase font-bold tracking-wider">Active</span><span className="font-black text-emerald-700 dark:text-emerald-400 text-xl">{summaryStats.active}</span></div>
              <div className="flex flex-col"><span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Archived</span><span className="font-black text-slate-500 dark:text-slate-400 text-xl">{summaryStats.archived}</span></div>
              {summaryStats.pendingReview > 0 && (
                <div className="flex flex-col"><span className="text-amber-600 text-[10px] uppercase font-bold tracking-wider">Pending Review</span><span className="font-black text-amber-700 dark:text-amber-400 text-xl">{summaryStats.pendingReview}</span></div>
              )}
            </div>
          )}

          {/* Filters Area */}
          <div className="flex items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
            <div className="flex-1 flex space-x-8">
              {[
                { id: 'DIRECT', label: 'Direct Competitors', icon: ShieldAlert, color: 'text-red-500' },
                { id: 'INDIRECT', label: 'Indirect Competitors', icon: Target, color: 'text-amber-500' },
                { id: 'EMERGING', label: 'Emerging Competitors', icon: Zap, color: 'text-blue-500' },
              ].map(tab => {
                const isActive = activeTab === tab.id;
                const count = confirmedCompetitors.filter(c => getCompType(c) === tab.id).length;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 py-2 font-bold text-sm transition-all ${
                      isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                    }`}
                  >
                    <tab.icon size={18} className={tab.color} />
                    <span>{tab.label}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-extrabold ${isActive ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-500">View:</span>
              <select 
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block px-3 py-2 font-medium"
              >
                <option value="active">Active</option>
                <option value="archived">Archived</option>
                <option value="all">All</option>
              </select>
            </div>
          </div>

          {pendingCompetitors.length > 0 && statusFilter !== 'archived' && (
            <section className="bg-amber-50/80 dark:bg-amber-950/20 border-2 border-amber-300 dark:border-amber-800/60 rounded-3xl p-6 shadow-sm space-y-6">
              <div>
                <div className="flex items-center gap-2.5 text-amber-700 dark:text-amber-400 font-extrabold text-lg">
                  <Sparkles size={22} className="animate-spin-slow" />
                  Review These Competitors
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {pendingCompetitors.map(comp => {
                  const compName = comp.name || comp.companyName || comp.company_name || 'Competitor';
                  const compWeb = comp.website || comp.websiteUrl || comp.website_url;
                  const typeBadge = getCompType(comp);
                  const score = comp.competitiveScore ?? comp.ai_score ?? null;
                  return (
                    <div key={comp.id} className="bg-white dark:bg-slate-900 border border-amber-200 dark:border-amber-900/40 rounded-2xl p-5 shadow-sm space-y-4 flex flex-col justify-between">
                      <div>
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-extrabold text-slate-900 dark:text-white text-lg">{compName}</h3>
                            {compWeb && (
                              <a href={compWeb.startsWith('http') ? compWeb : `https://${compWeb}`} target="_blank" rel="noreferrer" className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-medium mt-0.5">
                                {compWeb} <ExternalLink size={12} />
                              </a>
                            )}
                          </div>
                          <span className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded-full border ${getTypeBadgeStyle(typeBadge)}`}>{typeBadge}</span>
                        </div>
                        <p className="text-slate-600 dark:text-slate-300 text-xs line-clamp-2 mt-2 leading-relaxed">{comp.description}</p>
                      </div>
                      <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-3">
                        <span className="text-xs font-semibold text-slate-400">{score !== null ? `Score: ${score}/100` : 'Evaluating...'}</span>
                        <div className="flex items-center gap-2">
                          <button onClick={() => handleAccept(comp.id)} className="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow-sm"><Check size={14} /> Confirm</button>
                          <button onClick={() => handleReject(comp.id)} className="inline-flex items-center gap-1 bg-slate-100 hover:bg-red-50 hover:text-red-600 text-slate-600 text-xs font-bold px-3 py-1.5 rounded-lg"><X size={14} /> Reject</button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {tabFilteredCompetitors.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-12 text-center space-y-3">
              <Users className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto" />
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-200">No {activeTab.toLowerCase()} competitors found.</h3>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {tabFilteredCompetitors.map(comp => {
                const compName = comp.name || comp.companyName || comp.company_name || 'Competitor';
                const compWeb = comp.website || comp.websiteUrl || comp.website_url;
                const typeBadge = getCompType(comp);
                const isResearching = comp.competitiveScore === null || comp.isResearching || comp.researchStatus === 'IN_PROGRESS';
                const score = comp.competitiveScore ?? comp.ai_score ?? 0;
                const confidence = comp.confidenceScore ?? comp.confidence ?? 92;
                const whyReason = comp.reason || comp.whyCompetitor || comp.description || 'Presents direct feature and market overlap.';
                const sourceStr = (comp.source || '').toUpperCase() === 'MANUAL' ? 'Added Manually' : 'AI Discovered';
                const eventCountThisWeek = getEventCountThisWeek(comp);
                const actState = activityState[comp.id] || { expanded: false, docs: [], loading: false };
                const isArchived = statusFilter === 'archived' || comp.status === 'ARCHIVED';

                return (
                  <div key={comp.id} className={`bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-6 relative ${isArchived ? 'opacity-80 grayscale-[20%]' : ''}`}>
                    
                    {/* Menu Button */}
                    {!isResearching && (
                      <div className="absolute top-4 right-4">
                        <div className="relative">
                          <button onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === comp.id ? null : comp.id); }} className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                            <MoreVertical size={20} />
                          </button>
                          {activeMenuId === comp.id && (
                            <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-10 py-1 overflow-hidden" onClick={e => e.stopPropagation()}>
                              {!isArchived ? (
                                <>
                                  <button onClick={() => { setEditComp(comp); setEditData({ name: compName, website: compWeb, notes: comp.notes || '' }); setActiveMenuId(null); }} className="w-full text-left px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2"><Edit3 size={16} /> Edit</button>
                                  <button onClick={() => { handleResearch(comp); setActiveMenuId(null); }} className="w-full text-left px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 flex items-center gap-2"><RefreshCw size={16} /> Re-research</button>
                                  
                                  <div className="border-t border-slate-100 dark:border-slate-800 my-1"></div>
                                  <div className="px-3 py-1.5 text-xs font-bold text-slate-400 uppercase tracking-wider">Change Type</div>
                                  <button onClick={() => handleChangeType(comp.id, 'DIRECT')} className="w-full text-left px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2">Set as Direct</button>
                                  <button onClick={() => handleChangeType(comp.id, 'INDIRECT')} className="w-full text-left px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2">Set as Indirect</button>
                                  <button onClick={() => handleChangeType(comp.id, 'EMERGING')} className="w-full text-left px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2">Set as Emerging</button>
                                  <button onClick={() => handleChangeType(comp.id, 'AI')} className="w-full text-left px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2 text-blue-600"><Sparkles size={16} /> Use AI Type</button>
                                  
                                  <div className="border-t border-slate-100 dark:border-slate-800 my-1"></div>
                                  <button onClick={() => { setArchiveComp(comp); setActiveMenuId(null); }} className="w-full text-left px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 flex items-center gap-2"><Archive size={16} /> Archive</button>
                                </>
                              ) : (
                                <>
                                  <button onClick={() => { handleRestore(comp.id); setActiveMenuId(null); }} className="w-full text-left px-4 py-2 text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 flex items-center gap-2"><RotateCcw size={16} /> Restore</button>
                                  <button onClick={() => { setDeleteComp(comp); setActiveMenuId(null); }} className="w-full text-left px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"><Trash2 size={16} /> Delete Permanently</button>
                                </>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Top Header Row */}
                    <div className="pr-10">
                      <div className="flex items-center gap-2">
                        <h3 className="text-xl font-extrabold text-slate-900 dark:text-white tracking-tight">{compName}</h3>
                        {comp.notes && <MessageSquare size={16} className="text-slate-400" />}
                      </div>
                      {compWeb && <a href={compWeb.startsWith('http') ? compWeb : `https://${compWeb}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline font-semibold mt-1">{compWeb} <ExternalLink size={12} /></a>}
                      
                      <div className="flex items-center gap-2 mt-3">
                        <span className={`text-[10px] font-extrabold uppercase px-3 py-1 rounded-full border ${getTypeBadgeStyle(typeBadge)}`}>
                          {typeBadge} {comp.customType && <span className="opacity-70 ml-1">(Custom)</span>}
                        </span>
                        {isArchived && <span className="text-[10px] font-extrabold uppercase px-3 py-1 rounded-full border bg-slate-100 text-slate-500 border-slate-200">Archived</span>}
                      </div>
                      
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 line-clamp-2 leading-relaxed">{whyReason}</p>
                    </div>

                    {/* Scoring */}
                    {isResearching ? (
                      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/40 rounded-2xl p-4 flex items-center gap-3">
                        <Loader2 className="w-5 h-5 text-blue-600 animate-spin shrink-0" />
                        <div><div className="text-xs font-bold text-blue-700 dark:text-blue-300">Researching...</div><div className="text-[11px] text-blue-600/80 dark:text-blue-400">Updating profile and scores</div></div>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-950/60 rounded-2xl p-4 border border-slate-100 dark:border-slate-800">
                          <div><div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Competitive Threat Score</div></div>
                          <div className="flex items-baseline gap-1"><span className="text-3xl font-black text-blue-600 dark:text-blue-400 tracking-tight">{score}</span><span className="text-xs font-bold text-slate-400">/100</span></div>
                        </div>
                      </div>
                    )}

                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-3">
                      <button onClick={() => toggleCompetitorActivity(comp.id)} className="w-full flex items-center justify-between text-xs font-extrabold text-blue-600 dark:text-blue-400 hover:underline py-1">
                        <span>Details, Activity & Trends</span>
                        {actState.expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>

                      {actState.expanded && (
                        <div className="bg-slate-50 dark:bg-slate-950/60 rounded-2xl p-4 border border-slate-200 dark:border-slate-800 space-y-6 animate-fade-in w-full">
                          
                          {comp.notes && (
                            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4 rounded-xl">
                              <h4 className="text-xs font-extrabold text-yellow-800 dark:text-yellow-500 uppercase tracking-wider mb-2 flex items-center gap-2"><MessageSquare size={14}/> Your Notes</h4>
                              <p className="text-sm text-yellow-900 dark:text-yellow-100 whitespace-pre-wrap">{comp.notes}</p>
                            </div>
                          )}

                          <div className="w-full overflow-hidden"><CompetitorCharts competitorId={comp.id} /></div>

                          <div className="border-t border-slate-200 dark:border-slate-800 pt-4">
                            <h4 className="text-xs font-extrabold text-slate-500 uppercase tracking-wider mb-3">Recent Events</h4>
                            {actState.loading && <div className="flex justify-center py-4"><Loader2 size={20} className="text-blue-600 animate-spin" /></div>}
                            {!actState.loading && actState.docs.length === 0 && <div className="text-center py-3 text-xs text-slate-400 font-medium">No activity recorded yet</div>}
                            {!actState.loading && actState.docs.length > 0 && (
                              <div className="space-y-2.5">
                                {actState.docs.map(doc => (
                                  <div key={doc.id} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 shadow-sm space-y-1.5">
                                    <div className="flex items-center justify-between text-[10px] font-bold">
                                      <div className="flex items-center gap-1.5"><span className={`px-2 py-0.5 rounded-full border ${getEventTypeBadgeStyle(doc.eventType)}`}>{doc.eventType}</span></div>
                                      <span className="text-slate-400 font-semibold">{formatRelativeTime(doc.publishedAt || doc.date)}</span>
                                    </div>
                                    <h4 className="text-xs font-extrabold text-slate-900 dark:text-white line-clamp-1">{doc.title}</h4>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* ── Add Manual Competitor Modal ── */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-md w-full p-8 space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-extrabold text-slate-900 dark:text-white">Add a Competitor Manually</h2>
              <button onClick={() => setIsAddModalOpen(false)} className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"><X size={20} /></button>
            </div>
            <form onSubmit={handleAddManualCompetitor} className="space-y-4">
              {manualError && <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs font-semibold p-3 rounded-xl border border-red-200 dark:border-red-800">{manualError}</div>}
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">Company Name *</label>
                <input type="text" required value={manualName} onChange={(e) => setManualName(e.target.value)} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">Website URL *</label>
                <input type="text" required value={manualWebsite} onChange={(e) => setManualWebsite(e.target.value)} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div className="pt-4 flex items-center justify-end gap-3">
                <button type="button" onClick={() => setIsAddModalOpen(false)} className="px-4 py-2.5 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors">Cancel</button>
                <button type="submit" disabled={isSubmittingManual} className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-all shadow-md disabled:opacity-50">
                  {isSubmittingManual ? <><Loader2 className="w-4 h-4 animate-spin" /> Adding...</> : 'Add Competitor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Edit Competitor Modal ── */}
      {editComp && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-md w-full p-8 space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-extrabold text-slate-900 dark:text-white">Edit Competitor</h2>
              <button onClick={() => setEditComp(null)} className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"><X size={20} /></button>
            </div>
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">Company Name *</label>
                <input type="text" required value={editData.name} onChange={(e) => setEditData({...editData, name: e.target.value})} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">Website URL *</label>
                <input type="text" required value={editData.website} onChange={(e) => setEditData({...editData, website: e.target.value})} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">Private Notes</label>
                <textarea rows={3} value={editData.notes} onChange={(e) => setEditData({...editData, notes: e.target.value})} placeholder="Add private notes about this competitor..." className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div className="pt-4 flex items-center justify-end gap-3">
                <button type="button" onClick={() => setEditComp(null)} className="px-4 py-2.5 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors">Cancel</button>
                <button type="submit" disabled={actionLoading} className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-all shadow-md disabled:opacity-50">
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Archive Modal ── */}
      {archiveComp && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-sm w-full p-6 space-y-4">
            <h2 className="text-xl font-extrabold text-slate-900 dark:text-white">Archive {archiveComp.name || archiveComp.companyName}?</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">Archived competitors are not monitored and do not appear in your main list. All historical intelligence is preserved. You can restore them anytime.</p>
            <div className="pt-2 flex items-center justify-end gap-3">
              <button type="button" onClick={() => setArchiveComp(null)} className="px-4 py-2 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors">Cancel</button>
              <button onClick={handleArchive} disabled={actionLoading} className="inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 font-semibold px-6 py-2.5 rounded-xl text-sm transition-all shadow-md disabled:opacity-50">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Archive'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Modal ── */}
      {deleteComp && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-3 text-red-600">
              <AlertCircle size={24} />
              <h2 className="text-xl font-extrabold">Permanently delete {deleteComp.name || deleteComp.companyName}?</h2>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400">This cannot be undone. Intelligence history collected about this competitor will be preserved but unlinked.</p>
            <div className="pt-2">
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">Type <strong>{deleteComp.name || deleteComp.companyName}</strong> to confirm</label>
              <input type="text" value={deleteConfirmText} onChange={e => setDeleteConfirmText(e.target.value)} className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-red-500" />
            </div>
            <div className="pt-4 flex items-center justify-end gap-3">
              <button type="button" onClick={() => { setDeleteComp(null); setDeleteConfirmText(''); }} className="px-4 py-2 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors">Cancel</button>
              <button onClick={handleDelete} disabled={actionLoading || deleteConfirmText !== (deleteComp.name || deleteComp.companyName)} className="inline-flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-all shadow-md disabled:opacity-50">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
