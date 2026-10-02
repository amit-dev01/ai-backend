/** Shared Swiss typographic design tokens & Intelligence utilities used across components. */

export const W = {
  sm:    'rounded-sm',
  md:    'rounded-md',
  lg:    'rounded-lg',
  pill:  'rounded-full',
  input: 'rounded-xl',
};

export const S = {
  hard:      'shadow-sm',
  hardSm:    'shadow-sm',
  hardLg:    'shadow-md',
  hardHover: 'shadow-md',
  none:      'shadow-none',
};

export const FOCUS_OPTIONS = ['products', 'pricing', 'positioning', 'social', 'seo'];
export const HISTORY_KEY = 'competitor-ai-history';
export const MAX_HISTORY = 10;
export const MY_COMPANY_KEY = 'my-company-analysis';
export const SECTIONS = ['mycompany', 'competitors', 'unifeed'];

// ── Intelligence Event Types ──
export const EVENT_TYPES = [
  'All Events',
  'Product Launch',
  'Pricing Change',
  'Funding',
  'Partnership',
  'Acquisition',
  'Hiring',
  'Layoff',
  'Expansion',
  'Technology',
  'Marketing',
  'Regulatory',
  'Customer Sentiment',
  'Other'
];

// ── Consistent Event Type Badge Styling ──
export const getEventTypeBadgeStyle = (eventType = '') => {
  const norm = eventType.trim().toLowerCase();
  if (norm.includes('product')) {
    return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border-purple-200 dark:border-purple-800';
  }
  if (norm.includes('pricing')) {
    return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800';
  }
  if (norm.includes('funding')) {
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800';
  }
  if (norm.includes('partner')) {
    return 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800';
  }
  if (norm.includes('acquisition') || norm.includes('merger')) {
    return 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300 border-rose-200 dark:border-rose-800';
  }
  if (norm.includes('hiring')) {
    return 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300 border-sky-200 dark:border-sky-800';
  }
  if (norm.includes('layoff')) {
    return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300 border-orange-200 dark:border-orange-800';
  }
  if (norm.includes('expansion')) {
    return 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300 border-violet-200 dark:border-violet-800';
  }
  if (norm.includes('tech')) {
    return 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-300 border-fuchsia-200 dark:border-fuchsia-800';
  }
  if (norm.includes('market')) {
    return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200 dark:border-amber-800';
  }
  if (norm.includes('regulat')) {
    return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700';
  }
  if (norm.includes('sentiment') || norm.includes('customer')) {
    return 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300 border-pink-200 dark:border-pink-800';
  }
  return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700';
};

// ── Consistent Impact Badge Styling (CRITICAL=red, HIGH=orange, MEDIUM=yellow, LOW=grey) ──
export const getImpactBadgeStyle = (impact = '') => {
  const norm = impact.trim().toUpperCase();
  switch (norm) {
    case 'CRITICAL':
      return 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 border-red-300 dark:border-red-800';
    case 'HIGH':
      return 'bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400 border-orange-300 dark:border-orange-800';
    case 'MEDIUM':
      return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400 border-amber-300 dark:border-amber-800';
    case 'LOW':
    default:
      return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-700';
  }
};

// ── Sentiment Indicator Helpers ──
export const getSentimentDotColor = (sentiment = '') => {
  const norm = sentiment.trim().toUpperCase();
  if (norm === 'POSITIVE') return 'bg-emerald-500';
  if (norm === 'NEGATIVE') return 'bg-red-500';
  return 'bg-slate-400';
};

// ── Date Formatting Helpers ──
export const formatRelativeTime = (dateInput) => {
  if (!dateInput) return 'Recently';
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  
  const diffMs = Date.now() - d.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 30) {
    return d.toLocaleDateString();
  }
  if (diffDays >= 1) {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  }
  if (diffHours >= 1) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  }
  if (diffMins >= 1) {
    return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
  }
  return 'Just now';
};

export const formatMonitoredTimestamp = (timestamp) => {
  if (!timestamp) return 'Monitoring will run daily at 8 AM';
  const d = new Date(timestamp);
  if (isNaN(d.getTime())) return 'Monitoring will run daily at 8 AM';

  const month = d.toLocaleString('en-US', { month: 'long' });
  const day = d.getDate();
  let hours = d.getHours();
  const minutes = d.getMinutes().toString().padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12 || 12;

  return `Last monitored: ${month} ${day} at ${hours}:${minutes} ${ampm}`;
};

export const formatBriefTimestamp = (timestamp) => {
  if (!timestamp) return '';
  const d = new Date(timestamp);
  if (isNaN(d.getTime())) return String(timestamp);

  const weekday = d.toLocaleString('en-US', { weekday: 'long' });
  const month = d.toLocaleString('en-US', { month: 'long' });
  const day = d.getDate();
  let hours = d.getHours();
  const minutes = d.getMinutes().toString().padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12 || 12;

  return `Generated on ${weekday} ${month} ${day} at ${hours}:${minutes} ${ampm}`;
};

// ── Phase 3: Trends, Anomalies, and Alerts Constants ──

export const getUrgencyBadgeStyle = (urgency = '') => {
  const norm = urgency.trim().toUpperCase();
  switch (norm) {
    case 'ACT_NOW':
      return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 border-red-200 dark:border-red-800';
    case 'MONITOR':
      return 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400 border-orange-200 dark:border-orange-800';
    case 'WATCH':
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400 border-blue-200 dark:border-blue-800';
    default:
      return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-700';
  }
};

export const getTypeBadgeStyle = (type = '') => {
  const norm = type.trim().toUpperCase();
  if (norm === 'TREND') {
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400 border-blue-200 dark:border-blue-800';
  }
  if (norm === 'ANOMALY') {
    return 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-400 border-purple-200 dark:border-purple-800';
  }
  return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border-slate-200 dark:border-slate-700';
};

export const getTrendHumanReadableLabel = (trendType = '') => {
  const labels = {
    'ACTIVITY_SPIKE': 'Activity Spike',
    'ACTIVITY_DECLINE': 'Activity Decline',
    'SENTIMENT_SHIFT_POSITIVE': 'Positive Sentiment Shift',
    'SENTIMENT_SHIFT_NEGATIVE': 'Negative Sentiment Shift',
    'EVENT_CLUSTER': 'Event Cluster',
    'HIRING_SURGE': 'Hiring Surge',
    'PRODUCT_ACCELERATION': 'Product Acceleration',
    'MARKET_EXPANSION': 'Market Expansion'
  };
  return labels[trendType.trim().toUpperCase()] || trendType.replace(/_/g, ' ') || 'Unknown Trend';
};

export const MULTI_SELECT_OPTIONS = {
  customer_segments: ['Startups', 'SMBs', 'Mid-market', 'Enterprise', 'Consumers', 'Government', 'Developers', 'Other'],
  geographies: ['India', 'United States', 'Europe', 'Asia-Pacific', 'Middle East', 'Global', 'Other'],
};
