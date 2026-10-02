import { useState, useEffect, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  ComposedChart, Line, Area, Cell
} from 'recharts';
import { Loader2, AlertCircle, Calendar } from 'lucide-react';
import { getIntelligenceMetrics } from '../api';

export default function CompetitorCharts({ competitorId }) {
  const [days, setDays] = useState(30);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchMetrics = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getIntelligenceMetrics(competitorId, days);
      setMetrics(data);
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError('Failed to load metrics data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (competitorId) fetchMetrics();
  }, [competitorId, days]);

  // Memoize chart data formatting to prevent unnecessary re-renders
  const { activityData, sentimentData, eventTypeData } = useMemo(() => {
    if (!metrics || !metrics.timeseries) {
      return { activityData: [], sentimentData: [], eventTypeData: [] };
    }

    const ts = metrics.timeseries;
    
    // Activity Chart Data (with reference lines logic handled by UI)
    const activityData = ts.map(point => {
      // Simplify date label for x-axis
      const d = new Date(point.date);
      const label = `${d.getMonth() + 1}/${d.getDate()}`;
      return {
        date: label,
        fullDate: point.date,
        documentCount: point.documentCount,
        criticalCount: point.criticalCount,
        highCount: point.highCount,
        // Calculate standard events (not high/crit) for stacked bar if we wanted it
        normalCount: point.documentCount - point.criticalCount - point.highCount
      };
    });

    // Sentiment Chart Data
    const sentimentData = ts.map(point => {
      const d = new Date(point.date);
      const label = `${d.getMonth() + 1}/${d.getDate()}`;
      return {
        date: label,
        Positive: point.positiveSentimentCount,
        Negative: point.negativeSentimentCount,
        Neutral: point.neutralSentimentCount
      };
    });

    // Event Type Breakdown (aggregate over the period)
    const eventCounts = {};
    ts.forEach(point => {
      if (point.eventTypeCounts) {
        Object.entries(point.eventTypeCounts).forEach(([type, count]) => {
          eventCounts[type] = (eventCounts[type] || 0) + count;
        });
      }
    });

    const eventTypeData = Object.entries(eventCounts)
      .map(([name, value]) => ({ name, value }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);

    return { activityData, sentimentData, eventTypeData };
  }, [metrics]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3 rounded-lg shadow-lg text-xs font-semibold">
          <p className="text-slate-500 mb-2">{payload[0]?.payload?.fullDate || label}</p>
          {payload.map((entry, index) => (
            <p key={`item-${index}`} style={{ color: entry.color }} className="flex justify-between gap-4">
              <span>{entry.name}:</span>
              <span>{entry.value}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Determine standard colors based on theme context or hardcoded
  // We'll use reliable tailwind hex colors
  const COLORS = {
    blue: '#3b82f6',
    red: '#ef4444',
    orange: '#f97316',
    emerald: '#10b981',
    slate: '#94a3b8',
    gridLight: '#f1f5f9',
    gridDark: '#1e293b',
    textLight: '#64748b',
    textDark: '#94a3b8'
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-100 dark:border-slate-800">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-red-500 bg-red-50 dark:bg-red-900/10 rounded-2xl border border-red-100 dark:border-red-900/20">
        <AlertCircle className="w-8 h-8 mb-2" />
        <p className="text-sm font-bold">{error}</p>
        <button onClick={fetchMetrics} className="mt-4 text-xs bg-red-100 dark:bg-red-900/40 px-3 py-1.5 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/60 transition-colors">
          Retry
        </button>
      </div>
    );
  }

  if (!metrics || metrics.totalDocuments === 0 || activityData.length < 7) {
    return (
      <div className="bg-slate-50 dark:bg-slate-900/50 rounded-2xl p-8 text-center border border-slate-200 dark:border-slate-800 space-y-3">
        <BarChart3Icon className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto" />
        <h4 className="text-sm font-extrabold text-slate-900 dark:text-white">Not enough data yet for charts</h4>
        <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
          Charts will appear after 7 days of monitoring. We need sufficient data points to establish a baseline.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* ── CONTROLS & STATS ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        
        {/* Stats Row */}
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-0.5">Total Events</div>
            <div className="text-lg font-black text-slate-900 dark:text-white leading-none">{metrics.totalDocuments}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-0.5">Daily Avg</div>
            <div className="text-lg font-black text-slate-900 dark:text-white leading-none">{metrics.averageDailyActivity}</div>
          </div>
          {metrics.peakDayCount > 0 && (
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-500 mb-0.5">Peak Day ({new Date(metrics.peakDay).toLocaleDateString()})</div>
              <div className="text-lg font-black text-blue-600 dark:text-blue-400 leading-none">{metrics.peakDayCount} events</div>
            </div>
          )}
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
          {[7, 14, 30, 90].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                days === d 
                  ? 'bg-white dark:bg-slate-950 text-blue-600 dark:text-blue-400 shadow-sm' 
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              {d}D
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* ── CHART 1: Daily Activity (2/3 width) ── */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
          <h4 className="text-xs font-extrabold text-slate-900 dark:text-white uppercase tracking-wider mb-4 flex items-center gap-2">
            <Calendar size={14} className="text-blue-500" /> Daily Activity
          </h4>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={activityData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-slate-100 dark:text-slate-800" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 10, fill: 'currentColor' }} 
                  className="text-slate-400"
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                />
                <YAxis 
                  tick={{ fontSize: 10, fill: 'currentColor' }} 
                  className="text-slate-400"
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Area for overall volume */}
                <Area type="monotone" dataKey="documentCount" name="Total Events" fill={COLORS.blue} fillOpacity={0.1} stroke={COLORS.blue} strokeWidth={2} />
                
                {/* Highlight Bars for High/Crit */}
                <Bar dataKey="highCount" name="High Priority" fill={COLORS.orange} stackId="a" barSize={8} radius={[2, 2, 0, 0]} />
                <Bar dataKey="criticalCount" name="Critical Priority" fill={COLORS.red} stackId="a" barSize={8} radius={[2, 2, 0, 0]} />
                
                {/* Baseline Average Line */}
                <Line 
                  type="monotone" 
                  dataKey={() => metrics.averageDailyActivity} 
                  stroke={COLORS.slate} 
                  strokeDasharray="4 4" 
                  dot={false} 
                  activeDot={false} 
                  name="Average" 
                  strokeWidth={1.5}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ── CHART 2: Sentiment Distribution (1/3 width) ── */}
        <div className="bg-white dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
          <h4 className="text-xs font-extrabold text-slate-900 dark:text-white uppercase tracking-wider mb-4">
            Sentiment Trends
          </h4>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-slate-100 dark:text-slate-800" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 10, fill: 'currentColor' }} 
                  className="text-slate-400"
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                />
                <YAxis 
                  tick={{ fontSize: 10, fill: 'currentColor' }} 
                  className="text-slate-400"
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="Positive" stackId="a" fill={COLORS.emerald} radius={[0, 0, 2, 2]} />
                <Bar dataKey="Neutral" stackId="a" fill={COLORS.slate} />
                <Bar dataKey="Negative" stackId="a" fill={COLORS.red} radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
      
      {/* ── CHART 3: Event Type Breakdown ── */}
      {eventTypeData.length > 0 && (
        <div className="bg-white dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
          <h4 className="text-xs font-extrabold text-slate-900 dark:text-white uppercase tracking-wider mb-4">
            Event Types Distribution
          </h4>
          <div className="flex flex-wrap gap-3">
             {eventTypeData.map((item, i) => {
               const percentage = ((item.value / metrics.totalDocuments) * 100).toFixed(0);
               return (
                 <div key={item.name} className="flex-1 min-w-[120px] bg-slate-50 dark:bg-slate-900 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                   <div className="flex justify-between items-start mb-2">
                     <span className="text-[10px] font-black uppercase text-slate-500 line-clamp-1">{item.name}</span>
                     <span className="text-[10px] font-bold bg-white dark:bg-slate-800 px-1.5 py-0.5 rounded text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                       {percentage}%
                     </span>
                   </div>
                   <div className="text-xl font-black text-slate-800 dark:text-slate-200">
                     {item.value}
                   </div>
                   <div className="w-full bg-slate-200 dark:bg-slate-800 h-1 mt-2 rounded-full overflow-hidden">
                     <div className="bg-blue-500 h-full rounded-full" style={{ width: `${percentage}%` }} />
                   </div>
                 </div>
               );
             })}
          </div>
        </div>
      )}

    </div>
  );
}

function BarChart3Icon(props) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 3v18h18" />
      <path d="M18 17V9" />
      <path d="M13 17V5" />
      <path d="M8 17v-3" />
    </svg>
  );
}
