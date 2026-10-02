import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Copy, Download, FileJson, ChevronRight, Shield, AlertTriangle,
  TrendingUp, Target, Zap, Award, BarChart3, Lightbulb, Check,
} from 'lucide-react';

/* ═══════════════════════════════════════════════════════════
   SMALL HELPERS
   ═══════════════════════════════════════════════════════════ */

function AnimatedCount({ to, duration = 600 }) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (to === 0) return;
    let start = 0;
    const step = Math.ceil(to / (duration / 30));
    const id = setInterval(() => {
      start += step;
      if (start >= to) { setCount(to); clearInterval(id); }
      else setCount(start);
    }, 30);
    return () => clearInterval(id);
  }, [to, duration]);
  return <>{count}</>;
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text);
}

function downloadFile(content, filename, type = 'text/markdown') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

/* ═══════════════════════════════════════════════════════════
   SECTION COMPONENTS
   ═══════════════════════════════════════════════════════════ */

/* ── Stats Bar ──────────────────────────────────────────── */
function StatsBar({ result }) {
  const stats = [
    { label: 'Strengths',     value: result.strengths?.length || 0, isAccent: false },
    { label: 'Weaknesses',    value: result.weaknesses?.length || 0, isAccent: false },
    { label: 'Opportunities', value: result.opportunities?.length || 0, isAccent: false },
    { label: 'Threats',       value: result.threats?.length || 0, isAccent: false },
    { label: 'Next Steps',    value: result.next_steps?.length || 0, isAccent: true }, // Highlight next steps with Swiss Red background!
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8 stagger">
      {stats.map(s => (
        <div
          key={s.label}
          className={`text-left p-4 rounded-xl border transition-colors ${s.isAccent ? 'bg-blue-600 text-white border-blue-600 shadow-md' : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md hover:border-blue-500'}`}
        >
          <div className={`text-3xl font-bold ${s.isAccent ? 'text-white' : 'text-slate-900 dark:text-white'}`}>
            <AnimatedCount to={s.value} />
          </div>
          <div className={`text-xs font-semibold uppercase tracking-wider mt-1 ${s.isAccent ? 'text-blue-100' : 'text-slate-500 dark:text-slate-400'}`}>
            {s.label}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Section Card wrapper ───────────────────────────────── */
function SectionCard({ title, icon: Icon, children, className = '', bgColor = 'bg-white dark:bg-slate-900', sectionNum = '' }) {
  return (
    <div
      className={`${bgColor} border border-slate-200 dark:border-slate-800 shadow-sm p-6 relative animate-fade-in-up rounded-2xl ${className}`}
    >
      {title && (
        <h3 className="text-lg font-bold mb-6 flex items-center gap-2 text-slate-900 dark:text-white">
          {Icon && <Icon size={20} className={bgColor.includes('bg-blue-600') ? 'text-blue-200' : 'text-blue-600'} />} {title}
        </h3>
      )}
      {children}
    </div>
  );
}

/* ── Bullet List ────────────────────────────────────────── */
function BulletList({ items, bulletColor = '#3B82F6' }) {
  return (
    <ul className="space-y-4 stagger">
      {items.map((item, i) => (
        <li
          key={i}
          className="flex items-start gap-3 font-sans text-sm md:text-base leading-relaxed animate-fade-in-up text-slate-700 dark:text-slate-300"
        >
          <ChevronRight size={20} className="shrink-0 mt-0.5" style={{ color: bulletColor }} />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

/* ── SWOT Matrix ────────────────────────────────────────── */
function SwotMatrix({ swot }) {
  const quadrants = [
    { key: 'Strengths',     label: 'Strengths',     bg: 'bg-white dark:bg-slate-900', color: '#3B82F6', icon: Award },
    { key: 'Weaknesses',    label: 'Weaknesses',    bg: 'bg-slate-50 dark:bg-slate-800/50', color: '#64748B', icon: AlertTriangle },
    { key: 'Opportunities', label: 'Opportunities', bg: 'bg-slate-50 dark:bg-slate-800/50', color: '#64748B', icon: TrendingUp },
    { key: 'Threats',       label: 'Threats',        bg: 'bg-white dark:bg-slate-900', color: '#3B82F6', icon: Shield },
  ];
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {quadrants.map(q => (
        <div
          key={q.key}
          className={`border border-slate-200 dark:border-slate-800 p-5 rounded-xl hover:shadow-md transition-shadow ${q.bg}`}
        >
          <h4 className="text-sm font-bold mb-3 flex items-center gap-2" style={{ color: q.color }}>
            <q.icon size={16} />
            <span>{q.label}</span>
          </h4>
          <ul className="space-y-2">
            {(swot[q.key] || []).map((item, i) => (
              <li key={i} className="font-sans text-sm flex items-start gap-2 leading-relaxed text-slate-700 dark:text-slate-300">
                <span className="text-blue-500">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

/* ── Next Steps Table ───────────────────────────────────── */
function NextStepsTable({ steps }) {
  const priorityStyle = (p) => {
    const lower = (p || '').toLowerCase();
    if (lower.includes('p0')) return { border: '#EF4444', badge: 'P0', text: 'text-red-600' };
    if (lower.includes('p1')) return { border: '#F59E0B', badge: 'P1', text: 'text-amber-600' };
    return { border: '#3B82F6', badge: 'P2', text: 'text-blue-600' };
  };

  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full border-collapse font-sans text-sm border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden hidden md:table">
        <thead>
          <tr className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
            {['Priority', 'Action', 'Owner', 'Impact', 'Rationale'].map(h => (
              <th key={h} className="text-xs font-semibold text-slate-500 text-left px-4 py-3 uppercase">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {steps.map((s, i) => {
            const ps = priorityStyle(s.priority);
            return (
              <tr
                key={i}
                className="border-b border-slate-100 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors"
              >
                <td className="px-4 py-4">
                  <span
                    className={`inline-block px-2.5 py-1 font-bold text-xs rounded-md bg-opacity-10 border ${ps.text}`}
                    style={{ borderColor: ps.border }}
                  >
                    {ps.badge}
                  </span>
                </td>
                <td className="px-4 py-4 font-semibold text-slate-900 dark:text-white">{s.action}</td>
                <td className="px-4 py-4 text-xs uppercase text-slate-500">{s.owner_suggestion}</td>
                <td className="px-4 py-4 font-medium text-slate-700 dark:text-slate-300">{s.expected_impact}</td>
                <td className="px-4 py-4 text-xs text-slate-500">{s.rationale}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="md:hidden space-y-4">
        {/* Mobile card view for table fallback */}
        {steps.map((s, i) => {
            const ps = priorityStyle(s.priority);
            return (
              <div key={i} className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 bg-white dark:bg-slate-900">
                <div className="flex items-center gap-3 mb-2">
                   <span
                    className={`inline-block px-2.5 py-1 font-bold text-xs rounded-md bg-opacity-10 border ${ps.text}`}
                    style={{ borderColor: ps.border }}
                  >
                    {ps.badge}
                  </span>
                  <span className="font-bold text-slate-900 dark:text-white">{s.action}</span>
                </div>
                <div className="text-sm text-slate-700 dark:text-slate-300 mb-2">{s.expected_impact}</div>
                <div className="text-xs text-slate-500 flex justify-between">
                  <span className="uppercase">{s.owner_suggestion}</span>
                  <span>{s.rationale}</span>
                </div>
              </div>
            );
        })}
      </div>
    </div>
  );
}

/* ── Snapshot Grid ──────────────────────────────────────── */
function SnapshotGrid({ snapshot }) {
  if (!snapshot || Object.keys(snapshot).length === 0) return null;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
      {Object.entries(snapshot).map(([key, value]) => (
        <div
          key={key}
          className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 p-4 rounded-xl"
        >
          <div className="text-xs font-semibold text-slate-500 uppercase">{key}</div>
          <div className="text-sm font-medium mt-1 text-slate-900 dark:text-white">{value}</div>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN RESULTS VIEW
   ═══════════════════════════════════════════════════════════ */

export default function ResultsView({ result, onNewAnalysis }) {
  const [copied, setCopied] = useState(false);
  const topRef = useRef(null);

  useEffect(() => { topRef.current?.scrollIntoView({ behavior: 'smooth' }); }, []);

  const handleCopy = () => {
    copyToClipboard(result.full_markdown_report || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMd = () => {
    downloadFile(
      result.full_markdown_report || '',
      `${result.company_name.toLowerCase().replace(/\s+/g, '-')}-report.md`,
    );
  };

  const handleExportJson = () => {
    downloadFile(
      JSON.stringify(result, null, 2),
      `${result.company_name.toLowerCase().replace(/\s+/g, '-')}-analysis.json`,
      'application/json',
    );
  };

  return (
    <div ref={topRef} className="space-y-8">
      {/* ── Header ──────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-slate-200 dark:border-slate-800 animate-fade-in-up">
        <div>
          <span className="text-xs font-bold text-blue-600 uppercase tracking-wider block mb-1">Analysis Complete</span>
          <h2 className="text-4xl font-bold text-slate-900 dark:text-white">
            {result.company_name}
          </h2>
          <p className="text-xs text-slate-500 mt-2">
            Generated: {new Date(result.generated_at).toLocaleString()}
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 flex-wrap">
          {[
            { label: copied ? 'Copied!' : 'Copy report', icon: copied ? Check : Copy, action: handleCopy },
            { label: 'Download .md', icon: Download, action: handleDownloadMd },
            { label: 'Export JSON', icon: FileJson, action: handleExportJson },
          ].map(btn => (
            <button
              key={btn.label}
              onClick={btn.action}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700
                         text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700
                         transition-colors rounded-lg shadow-sm"
            >
              <btn.icon size={16} className="text-blue-600 dark:text-blue-400" /> {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Stats Bar ───────────────────────────────────── */}
      <StatsBar result={result} />

      {/* ── Executive Summary ───────────────────────────── */}
      <SectionCard title="Executive Summary" icon={Zap} sectionNum="02.1 // REPORT_SUMMARY">
        <p className="font-sans text-base md:text-lg leading-relaxed text-black dark:text-white">{result.executive_summary}</p>
      </SectionCard>

      {/* ── Competitor Snapshot ──────────────────────────── */}
      <SectionCard title="Competitor Metrics" icon={BarChart3} sectionNum="02.2 // META_METRICS">
        <SnapshotGrid snapshot={result.snapshot} />
      </SectionCard>

      {/* ── Strengths & Weaknesses ──────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SectionCard title="Strengths & Advantages" icon={Award} sectionNum="02.3 // ADVANTAGES">
          <BulletList items={result.strengths || []} bulletColor="#FF3000" />
        </SectionCard>
        <SectionCard title="Weaknesses & Vulnerabilities" icon={AlertTriangle} sectionNum="02.4 // VULNERABILITIES">
          <BulletList items={result.weaknesses || []} bulletColor="#000000" />
        </SectionCard>
      </div>

      {/* ── SWOT Matrix ─────────────────────────────────── */}
      <SectionCard title="SWOT Matrix Grid" icon={Target} sectionNum="02.5 // SWOT_GRID">
        <SwotMatrix swot={result.swot || {}} />
      </SectionCard>

      {/* ── Opportunities & Threats ─────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SectionCard title="Opportunities" icon={TrendingUp} sectionNum="02.6 // OPPORTUNITIES">
          <BulletList items={result.opportunities || []} bulletColor="#FF3000" />
        </SectionCard>
        <SectionCard title="Threats & Defensive strategy" icon={Shield} sectionNum="02.7 // DEFENSIVE">
          <BulletList items={result.threats || []} bulletColor="#000000" />
        </SectionCard>
      </div>

      {/* ── Next Steps ──────────────────────────────────── */}
      <SectionCard title="Prioritized Next Steps" icon={ChevronRight} sectionNum="02.8 // ACTION_PIPELINE">
        <NextStepsTable steps={result.next_steps || []} />
      </SectionCard>

      {/* ── Differentiation Strategy ────────────────────── */}
      <SectionCard title="Recommended Brand Positioning" icon={Lightbulb} sectionNum="" bgColor="bg-blue-600 text-white">
        <p className="text-xl md:text-2xl font-bold leading-tight text-white">
          "{result.differentiation_strategy}"
        </p>
      </SectionCard>

      {/* ── Full Markdown Report ────────────────────────── */}
      <SectionCard title="Detailed Analysis" icon={BarChart3} sectionNum="">
        <div className="markdown-report">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {result.full_markdown_report || ''}
          </ReactMarkdown>
        </div>

        {/* Bottom action bar */}
        <div className="flex gap-3 mt-8 pt-6 border-t border-slate-200 dark:border-slate-800 flex-wrap">
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl
                       text-sm font-medium hover:bg-blue-700 transition-colors shadow-sm"
          >
            {copied ? <Check size={18} /> : <Copy size={18} />}
            {copied ? 'Copied!' : 'Copy to Clipboard'}
          </button>
          <button
            onClick={handleDownloadMd}
            className="flex items-center gap-2 px-5 py-2.5 bg-white text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700
                       text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors rounded-xl shadow-sm"
          >
            <Download size={18} /> Download as .md
          </button>
        </div>
      </SectionCard>

      {/* ── Bottom CTA ──────────────────────────────────── */}
      <div className="text-center py-12 border-t-4 border-black dark:border-white">
        <p className="font-mono text-[10px] text-slate-500 uppercase tracking-widest mb-6">
          [ PIPELINE_END // VERIFY DATA BEFORE STRATEGIC DECISION ]
        </p>
        <button
          onClick={onNewAnalysis}
          className="inline-flex items-center gap-3 px-8 py-4 bg-black text-white dark:bg-white dark:text-black border-2 border-black dark:border-white
                     font-heading text-sm font-black uppercase tracking-widest hover:bg-accent hover:text-white dark:hover:bg-accent dark:hover:text-white transition-colors rounded-none"
        >
          Initialize Another Scan
        </button>
      </div>
    </div>
  );
}
