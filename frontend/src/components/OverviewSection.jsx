import { useState, useEffect, useContext, useRef } from 'react';
import { DbContext } from '../App';
import { 
  AlertCircle, AlertTriangle, Lightbulb, ShieldAlert, Users, Target, Zap, Clock, RefreshCw, 
  Activity, TrendingUp, Loader2, CheckSquare, ChevronRight
} from 'lucide-react';
import { getCompanyProfile, getCompetitors, getIntelligenceJobs } from '../api';
import { formatMonitoredTimestamp, getEventTypeBadgeStyle } from '../constants';
import BounceCards from './BounceCards/BounceCards';

function KPICardCountUp({ value }) {
  const [count, setCount] = useState(0);
  const elementRef = useRef(null);
  const valueRef = useRef(value);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setCount(value);
      return;
    }

    let animated = false;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !animated && valueRef.current >= 0) {
          animated = true;
          let startTimestamp = null;
          const duration = 1000;
          const startVal = 0;
          const endVal = valueRef.current;

          if (endVal === 0) {
            setCount(0);
            return;
          }

          const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            setCount(Math.floor(startVal + easeProgress * (endVal - startVal)));
            if (progress < 1) {
              window.requestAnimationFrame(step);
            }
          };
          window.requestAnimationFrame(step);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    if (elementRef.current) {
      observer.observe(elementRef.current);
    }

    return () => observer.disconnect();
  }, [value]);

  return <span ref={elementRef}>{count}</span>;
}

function KPICard({ title, value, subtitle, icon: Icon, type, index }) {
  const { isVideoActive } = useContext(DbContext) || {};
  const cardRef = useRef(null);
  const [isHovered, setIsHovered] = useState(false);
  const target = useRef({ x: 0, y: 0 });
  const current = useRef({ x: 0, y: 0 });
  const rafId = useRef(null);

  // Styling based on card type
  let borderClass = '';
  let borderHoverClass = '';
  let titleColorClass = '';
  let countColorClass = '';
  let subtitleColorClass = '';
  let iconColorClass = '';
  let glowClass = '';
  let iconHoverClass = '';

  switch (type) {
    case 'direct':
      borderClass = 'border-[#E2E8F0] dark:border-red-900/30';
      borderHoverClass = 'border-red-300/80 dark:border-red-700/50';
      titleColorClass = 'text-red-600 dark:text-red-400';
      countColorClass = 'text-red-600 dark:text-red-400';
      subtitleColorClass = 'text-red-500/80';
      iconColorClass = 'text-red-500';
      glowClass = 'shadow-[0_12px_30px_-4px_rgba(239,68,68,0.12)]';
      iconHoverClass = 'rotate-12 scale-105';
      break;
    case 'indirect':
      borderClass = 'border-[#E2E8F0] dark:border-amber-900/30';
      borderHoverClass = 'border-amber-300/80 dark:border-amber-700/50';
      titleColorClass = 'text-amber-600 dark:text-amber-500';
      countColorClass = 'text-amber-600 dark:text-amber-500';
      subtitleColorClass = 'text-amber-500/80';
      iconColorClass = 'text-amber-500';
      glowClass = 'shadow-[0_12px_30px_-4px_rgba(245,158,11,0.12)]';
      iconHoverClass = 'scale-110';
      break;
    case 'emerging':
      borderClass = 'border-[#E2E8F0] dark:border-blue-900/30';
      borderHoverClass = 'border-blue-300/80 dark:border-blue-700/50';
      titleColorClass = 'text-blue-600 dark:text-blue-400';
      countColorClass = 'text-blue-600 dark:text-blue-400';
      subtitleColorClass = 'text-blue-500/80';
      iconColorClass = 'text-blue-500';
      glowClass = 'shadow-[0_12px_30px_-4px_rgba(59,130,246,0.12)]';
      iconHoverClass = 'translate-y-[-2px] scale-110';
      break;
    case 'total':
    default:
      borderClass = 'border-[#E2E8F0] dark:border-slate-800';
      borderHoverClass = 'border-slate-300 dark:border-slate-700';
      titleColorClass = 'text-slate-500 dark:text-slate-400';
      countColorClass = 'text-slate-900 dark:text-white';
      subtitleColorClass = 'text-slate-400';
      iconColorClass = 'text-slate-400';
      glowClass = 'shadow-[0_12px_30px_-4px_rgba(148,163,184,0.12)]';
      iconHoverClass = 'scale-110';
      break;
  }

  const startLoop = () => {
    if (rafId.current) return;
    const tick = () => {
      const dx = target.current.x - current.current.x;
      const dy = target.current.y - current.current.y;

      current.current.x += dx * 0.15;
      current.current.y += dy * 0.15;

      if (cardRef.current) {
        cardRef.current.style.transform = `perspective(1000px) rotateX(${current.current.x}deg) rotateY(${current.current.y}deg)`;
      }

      const isCloseX = Math.abs(current.current.x - target.current.x) < 0.01;
      const isCloseY = Math.abs(current.current.y - target.current.y) < 0.01;

      if (!isHovered && isCloseX && isCloseY) {
        current.current.x = 0;
        current.current.y = 0;
        if (cardRef.current) {
          cardRef.current.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
        }
        rafId.current = null;
      } else {
        rafId.current = requestAnimationFrame(tick);
      }
    };
    rafId.current = requestAnimationFrame(tick);
  };

  const onMouseMove = (e) => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const normX = (x / rect.width) - 0.5;
    const normY = (y / rect.height) - 0.5;

    target.current.x = normY * -3;
    target.current.y = normX * 3;
  };

  const onMouseEnter = () => {
    setIsHovered(true);
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    startLoop();
  };

  const onMouseLeave = () => {
    setIsHovered(false);
    target.current.x = 0;
    target.current.y = 0;
  };

  useEffect(() => {
    return () => {
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, []);

  const delay = index * 80;

  return (
    <div 
      className="kpi-card-entrance"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div 
        className={`transform transition-transform duration-300 ease-out ${isHovered ? '-translate-y-1' : 'translate-y-0'}`}
      >
        <div
          ref={cardRef}
          onMouseMove={onMouseMove}
          onMouseEnter={onMouseEnter}
          onMouseLeave={onMouseLeave}
          className={`rounded-2xl p-6 border cursor-default select-none
            transition-all duration-300 ease-out light-surface-kpi
            ${borderClass}
            ${isVideoActive 
              ? 'dark:bg-slate-900/60 dark:border-slate-800/50 dark:backdrop-blur-md dark:shadow-none' 
              : 'dark:bg-slate-900 dark:border-slate-800 dark:shadow-none'
            }
            ${isHovered ? `${borderHoverClass} ${glowClass}` : ''}
          `}
          style={{
            transformStyle: 'preserve-3d',
            backfaceVisibility: 'hidden',
          }}
        >
          <div 
            className="flex items-center justify-between text-xs font-bold uppercase tracking-wider mb-2"
            style={{ transform: 'translateZ(15px)' }}
          >
            <span className={titleColorClass}>{title}</span>
            <Icon 
              size={18} 
              className={`transition-transform duration-300 ease-out ${iconColorClass} ${isHovered ? iconHoverClass : ''}`} 
            />
          </div>
          <div 
            className={`text-3xl font-black ${countColorClass}`}
            style={{ transform: 'translateZ(25px)' }}
          >
            <KPICardCountUp value={value} />
          </div>
          <div 
            className={`text-xs mt-1 font-medium ${subtitleColorClass}`}
            style={{ transform: 'translateZ(10px)' }}
          >
            {subtitle}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function OverviewSection() {
  const context = useContext(DbContext) || {};
  const { 
    companyProfile, 
    intelligenceStats, 
    intelligenceAlerts,
    intelligenceTrends,
    acceptedCompetitors, 
    checkStatus,
    startCheck,
    setActiveSection,
    taskStats,
    isVideoActive
  } = context;

  const [profile, setProfile] = useState(companyProfile || null);
  const [competitorsData, setCompetitorsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Hero Animation State
  const [heroAnimated, setHeroAnimated] = useState(false);
  const heroRef = useRef(null);
  
  // Jobs State
  const [showJobsModal, setShowJobsModal] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  
  const fetchJobs = async () => {
    setJobsLoading(true);
    try {
      const data = await getIntelligenceJobs();
      setJobs(Array.isArray(data) ? data : data.jobs || []);
    } catch (err) {
      console.error('Failed to load jobs:', err);
    } finally {
      setJobsLoading(false);
    }
  };

  const handleOpenJobs = () => {
    setShowJobsModal(true);
    fetchJobs();
  };

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [profileRes, compRes] = await Promise.allSettled([
        getCompanyProfile(),
        getCompetitors()
      ]);

      if (profileRes.status === 'fulfilled') {
        const data = profileRes.value;
        setProfile(data?.company || data);
      }
      if (compRes.status === 'fulfilled') {
        setCompetitorsData(compRes.value);
      }
    } catch (err) {
      console.error('Failed to load Overview data:', err);
      setError('Could not load latest intelligence data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (loading) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setHeroAnimated(true);
      return;
    }

    let timeoutId = null;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          timeoutId = setTimeout(() => {
            setHeroAnimated(true);
          }, 50);
          observer.disconnect();
        }
      },
      { threshold: 0.05 }
    );

    if (heroRef.current) {
      observer.observe(heroRef.current);
    }

    return () => {
      observer.disconnect();
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [loading]);



  if (loading) {
    return (
      <div className="max-w-5xl space-y-8 animate-pulse">
        {/* Skeleton Header Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 space-y-4">
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/4" />
          <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/2" />
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
        </div>
        {/* Skeleton Brief Block */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 space-y-4">
          <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
          <div className="h-16 bg-slate-200 dark:bg-slate-800 rounded w-full" />
        </div>
        {/* Skeleton Counts */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 space-y-2">
              <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-1/2" />
              <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/3" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-red-200 dark:border-red-900/40 p-8 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
        <h3 className="text-xl font-bold text-slate-900 dark:text-white">{error}</h3>
        <button 
          onClick={fetchData} 
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl text-sm transition-colors"
        >
          <RefreshCw size={16} /> Retry Loading
        </button>
      </div>
    );
  }

  const companyName = profile?.companyName || profile?.company_name || 'Your Company';
  const executiveBrief = profile?.executiveBrief;
  const mainThreats = Array.isArray(profile?.mainThreats) ? profile.mainThreats : [];
  const keyOpportunity = profile?.keyOpportunity;
  const briefGeneratedAt = profile?.briefGeneratedAt;

  // Counts from GET /api/competitors
  const totalCount = competitorsData?.total ?? (competitorsData?.competitors?.length || 0);
  const directCount = competitorsData?.direct ?? (competitorsData?.competitors?.filter(c => (c.type || c.competitive_status)?.toUpperCase() === 'DIRECT')?.length || 0);
  const indirectCount = competitorsData?.indirect ?? (competitorsData?.competitors?.filter(c => (c.type || c.competitive_status)?.toUpperCase() === 'INDIRECT')?.length || 0);
  const emergingCount = competitorsData?.emerging ?? (competitorsData?.competitors?.filter(c => (c.type || c.competitive_status)?.toUpperCase() === 'EMERGING')?.length || 0);

  const documentsThisWeek = intelligenceStats?.documentsThisWeek ?? 0;
  const criticalEvents = intelligenceStats?.criticalEvents ?? 0;
  const highEvents = intelligenceStats?.highEvents ?? 0;
  const monitoredCompetitorsCount = acceptedCompetitors?.length ?? intelligenceStats?.monitoredCount ?? competitorsData?.competitors?.filter(c => c.isAccepted === true)?.length ?? 0;

  // Phase 3 Stats
  const activeTrendsCount = intelligenceTrends?.totalActive || 0;
  const unacknowledgedAlerts = intelligenceAlerts?.totalUnacknowledged || 0;

  // Most Active Competitors (up to 3 ordered by documentCount descending)
  const byComp = Array.isArray(intelligenceStats?.byCompetitor) ? intelligenceStats.byCompetitor : [];
  const mostActiveCompetitors = [...byComp]
    .sort((a, b) => (b.documentCount || 0) - (a.documentCount || 0))
    .slice(0, 3);

  // Use checkStatus.completedAt first, else fallback, else "No checks run yet"
  let lastMonitoredText = "No checks run yet";
  if (checkStatus?.completedAt) {
    lastMonitoredText = "Last checked: " + formatMonitoredTimestamp(checkStatus.completedAt);
  } else if (intelligenceStats?.lastMonitoredCompletedAt) {
    lastMonitoredText = "Last checked: " + formatMonitoredTimestamp(intelligenceStats.lastMonitoredCompletedAt);
  }

  return (
    <div className="animate-fade-in-up max-w-5xl space-y-8 pb-12">
      
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
      
      {/* ── Main Overview Heading ── */}
      <section 
        ref={heroRef}
        className={`hero-container rounded-2xl border p-8 relative overflow-hidden transition-all duration-300 light-surface-panel
          ${heroAnimated ? 'hero-animated' : ''} 
          ${isVideoActive 
            ? 'hero-video-active dark:bg-slate-900/60 dark:border-slate-800/50 dark:backdrop-blur-md dark:shadow-none' 
            : 'dark:bg-slate-900 dark:border-slate-800 dark:shadow-none'
          }`}
      >
        <div className="hero-ambient-glow pointer-events-none" />
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
          <div>
            <div className="hero-kicker text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 mb-1">
              Market Baseline & Intelligence
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              <span className="hero-title-part1 mr-2">{companyName}</span>
              <span className="hero-title-part2 font-normal text-slate-500">Competitive Intelligence</span>
            </h1>
            <p className="hero-subtitle text-slate-500 dark:text-slate-400 text-sm mt-1">
              {profile?.industry || profile?.description || 'Real-time market surveillance'}
            </p>
          </div>

          {briefGeneratedAt && (
            <div className="hero-meta flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 font-medium bg-slate-50 dark:bg-slate-800/50 px-3 py-1.5 rounded-lg border border-slate-100 dark:border-slate-800">
              <Clock size={14} />
              <span>Last updated: {new Date(briefGeneratedAt).toLocaleString()}</span>
            </div>
          )}
        </div>
      </section>

      {/* ── Competitor Summary Counts (Interactive Fan-out Deck) ── */}
      <section className="flex justify-center items-center py-6 w-full overflow-visible">
        <BounceCards
          containerWidth="100%"
          containerHeight={220}
          animationDelay={0.4}
          animationStagger={0.08}
          easeType="elastic.out(1, 0.6)"
          transformStyles={[
            "rotate(-8deg) translate(-140px)",
            "rotate(-3deg) translate(-45px)",
            "rotate(3deg) translate(45px)",
            "rotate(8deg) translate(140px)"
          ]}
          enableHover={true}
        >
          <KPICard 
            title="Total Discovered" 
            value={totalCount} 
            subtitle="Discovered by AI" 
            icon={Users} 
            type="total" 
            index={0} 
          />
          <KPICard 
            title="Direct Competitors" 
            value={directCount} 
            subtitle="Primary threats" 
            icon={ShieldAlert} 
            type="direct" 
            index={1} 
          />
          <KPICard 
            title="Indirect Competitors" 
            value={indirectCount} 
            subtitle="Substitutes & adjacent" 
            icon={Target} 
            type="indirect" 
            index={2} 
          />
          <KPICard 
            title="Emerging Threats" 
            value={emergingCount} 
            subtitle="Fast-growing startups" 
            icon={Zap} 
            type="emerging" 
            index={3} 
          />
        </BounceCards>
      </section>

      {/* ── Action Center Summary Card ── */}
      <section 
        onClick={() => setActiveSection && setActiveSection('tasks')}
        className={`rounded-2xl p-6 cursor-pointer hover:border-blue-500 transition-all duration-300 flex items-center justify-between border light-surface-panel
          ${isVideoActive 
            ? 'dark:bg-slate-900/60 dark:border-slate-800/50 dark:backdrop-blur-md dark:shadow-none' 
            : 'dark:bg-slate-900 dark:border-slate-800 dark:shadow-none'
          }`}
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
            <CheckSquare className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white text-lg">Action Items</h3>
            {(!taskStats || taskStats.totalActive === 0) ? (
              <p className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">No open action items</p>
            ) : (
              <div className="flex items-center gap-4 text-sm mt-1">
                <span className="font-medium text-slate-600 dark:text-slate-400">Total active: {taskStats.totalActive}</span>
                {taskStats.critical > 0 && <span className="font-bold text-red-500">Critical: {taskStats.critical}</span>}
                {taskStats.overdue > 0 && <span className="font-bold text-red-500">Overdue: {taskStats.overdue}</span>}
              </div>
            )}
          </div>
        </div>
        <ChevronRight className="text-slate-400 shrink-0" />
      </section>

      {/* ── AI Executive Brief Block ── */}
      {executiveBrief && (
        <section className={`rounded-2xl p-6 md:p-8 space-y-3 border transition-all duration-300 light-surface-panel
          ${isVideoActive 
            ? 'dark:bg-slate-900/60 dark:border-blue-900/30 dark:backdrop-blur-md dark:shadow-none' 
            : 'dark:bg-slate-900 dark:border-blue-900/40 dark:shadow-none'
          }`}
        >
          <div className="flex items-center gap-2.5 text-blue-600 dark:text-blue-400 font-extrabold text-lg">
            <span className="w-3 h-3 rounded-full bg-blue-600 animate-pulse" />
            Executive Brief
          </div>
          <p className="text-slate-700 dark:text-slate-200 text-base leading-relaxed font-medium">
            {executiveBrief}
          </p>
        </section>
      )}

      {/* ── Phase 2 & 3: Live Monitoring Stats Bar ── */}
      <section className="bg-gradient-to-r from-blue-900 to-slate-900 text-white rounded-3xl p-6 md:p-8 shadow-lg space-y-4 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-400 text-xs font-extrabold uppercase tracking-widest">
            <Activity size={16} className="animate-pulse" /> Intelligence Pulse
          </div>
          <div className="text-xs text-blue-300/80 font-medium">Updated After Checks</div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-6 pt-2">
          <div className="space-y-1">
            <div className="text-xs text-slate-300 font-medium">Events This Week</div>
            <div className="text-3xl font-black text-white">{documentsThisWeek}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-red-300 font-medium">Critical Events</div>
            <div className="text-3xl font-black text-red-400">{criticalEvents}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-orange-300 font-medium">High Priority</div>
            <div className="text-3xl font-black text-orange-400">{highEvents}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-blue-300 font-medium">Monitored Cos</div>
            <div className="text-3xl font-black text-blue-300">{monitoredCompetitorsCount}</div>
          </div>
          <div className="space-y-1 cursor-pointer hover:opacity-80 transition-opacity" onClick={() => setActiveSection && setActiveSection('trends')}>
            <div className="text-xs text-purple-300 font-medium flex items-center gap-1">Active Trends <TrendingUp size={12} /></div>
            <div className="text-3xl font-black text-purple-400">{activeTrendsCount}</div>
          </div>
          <div className="space-y-1 cursor-pointer hover:opacity-80 transition-opacity" onClick={() => setActiveSection && setActiveSection('alerts')}>
            <div className="text-xs text-red-300 font-medium flex items-center gap-1">Unread Alerts <AlertCircle size={12} /></div>
            <div className="text-3xl font-black text-red-400">{unacknowledgedAlerts}</div>
          </div>
        </div>
      </section>

      {/* ── Phase 2: Most Active Competitors Section ── */}
      {mostActiveCompetitors.length > 0 && (
        <section className="rounded-3xl border p-6 md:p-8 space-y-4 light-surface-panel dark:bg-slate-900 dark:border-slate-800 dark:shadow-none">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-900 dark:text-white font-extrabold text-lg">
              <TrendingUp size={22} className="text-blue-600 dark:text-blue-400" />
              Most Active Competitors This Week
            </div>
            <span className="text-xs text-slate-400 font-medium">Top 3 by document volume</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {mostActiveCompetitors.map((comp, idx) => (
              <div 
                key={comp.competitorId || idx}
                className="bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-extrabold text-slate-900 dark:text-white text-base">
                      {comp.competitorName}
                    </h3>
                    <span className="text-xs font-black text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 px-2.5 py-1 rounded-full">
                      {comp.documentCount} event{comp.documentCount !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 font-medium">
                    Activity detected across media & public sources.
                  </p>
                </div>

                {comp.latestEventType && (
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Latest Signal</span>
                    <span className={`text-[10px] font-extrabold px-2.5 py-1 rounded-md border uppercase ${getEventTypeBadgeStyle(comp.latestEventType)}`}>
                      {comp.latestEventType}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Main Threats & Key Opportunity Grid ── */}
      {(mainThreats.length > 0 || keyOpportunity) && (
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Main Threats Block */}
          {mainThreats.length > 0 && (
            <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 p-6 rounded-2xl shadow-sm space-y-4">
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-bold text-base">
                <AlertCircle size={22} />
                Main Threats
              </div>
              <ul className="space-y-3">
                {mainThreats.map((threat, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm text-slate-800 dark:text-slate-200 font-medium">
                    <AlertTriangle size={16} className="text-red-500 shrink-0 mt-0.5" />
                    <span>{threat}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Key Opportunity Block */}
          {keyOpportunity && (
            <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 p-6 rounded-2xl shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-base">
                <Lightbulb size={22} />
                Key Opportunity
              </div>
              <p className="text-slate-800 dark:text-slate-200 text-sm font-medium leading-relaxed">
                {keyOpportunity}
              </p>
            </div>
          )}

        </section>
      )}

      {/* ── Phase 2: Footer Last Monitored Timestamp & Refresh Button ── */}
      <section className="border rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4 light-surface-panel dark:bg-slate-900 dark:border-slate-800 dark:shadow-none">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-600 dark:text-slate-400">
            <Clock size={18} className="text-slate-400 shrink-0" />
            <span>{lastMonitoredText}</span>
          </div>
          <button 
            onClick={handleOpenJobs}
            className="text-xs text-blue-600 hover:text-blue-700 hover:underline font-bold transition-all"
          >
            View Check History
          </button>
        </div>

        <button
          onClick={startCheck}
          disabled={checkStatus?.status === 'RUNNING'}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
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
      </section>

      {/* ── JOBS MODAL ── */}
      {showJobsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 md:p-8 max-w-xl w-full shadow-2xl space-y-6 relative border border-slate-200 dark:border-slate-800 flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">System Jobs History</h2>
              <button 
                onClick={() => setShowJobsModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                Close
              </button>
            </div>
            
            <div className="overflow-y-auto flex-1 pr-2 space-y-3">
              {jobsLoading ? (
                <div className="flex justify-center p-8">
                  <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
                </div>
              ) : jobs.length === 0 ? (
                <div className="text-center p-8 text-slate-500 text-sm">
                  No sync jobs found.
                </div>
              ) : (
                jobs.map((job, idx) => (
                  <div key={job.id || idx} className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col gap-1 text-sm">
                    <div className="flex justify-between font-bold">
                      <span className="text-slate-900 dark:text-white">{job.type || 'Monitoring Sync'}</span>
                      <span className={`${job.status === 'COMPLETED' ? 'text-emerald-600' : job.status === 'FAILED' ? 'text-red-600' : 'text-blue-600'}`}>
                        {job.status}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">
                      Started: {new Date(job.startedAt || job.createdAt).toLocaleString()}
                    </div>
                    {job.completedAt && (
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        Completed: {new Date(job.completedAt).toLocaleString()}
                      </div>
                    )}
                    {job.error && (
                      <div className="text-xs text-red-500 mt-1">{job.error}</div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
