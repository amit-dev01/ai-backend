import { useState } from 'react';
import { Plus, Trash2, Sparkles, Globe, Building2, Users, Search } from 'lucide-react';
import { FOCUS_OPTIONS } from '../constants';

export default function InputForm({ 
  onSubmit, 
  title = "Configure Scan Parameters",
  subtitle = "Enter competitor details below to initialize automated web scraping and SWOT synthesis.",
  companyLabel = "Company Name",
  companyPlaceholder = "e.g. Nike, Shopify, Notion...",
  submitLabel = "Analyze Competitor"
}) {
  const [form, setForm] = useState({
    company_name: '',
    website_url: '',
    industry: '',
    our_company_context: '',
  });
  const [socialPairs, setSocialPairs] = useState([]);
  const [focusAreas, setFocusAreas] = useState([...FOCUS_OPTIONS]);
  const [errors, setErrors] = useState({});

  /* ── Handlers ──────────────────────────────────────────── */
  const update = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: null }));
  };

  const addSocialPair    = () => setSocialPairs(prev => [...prev, { platform: '', url: '' }]);
  const removeSocialPair = (i) => setSocialPairs(prev => prev.filter((_, idx) => idx !== i));
  const updateSocialPair = (i, field, value) =>
    setSocialPairs(prev => prev.map((p, idx) => idx === i ? { ...p, [field]: value } : p));

  const toggleFocus = (area) =>
    setFocusAreas(prev =>
      prev.includes(area) ? prev.filter(a => a !== area) : [...prev, area]
    );

  /* ── Validation ────────────────────────────────────────── */
  const validate = () => {
    const e = {};
    if (!form.company_name.trim()) e.company_name = 'Required';
    if (!form.website_url.trim()) e.website_url = 'Required';
    else if (!/^https?:\/\/.+\..+/.test(form.website_url)) e.website_url = 'Enter a valid URL (https://...)';
    if (!form.industry.trim()) e.industry = 'Required';
    if (focusAreas.length === 0) e.focus = 'Pick at least one';
    return e;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    // Build social_urls object from pairs
    const social_urls = {};
    socialPairs.forEach(p => {
      if (p.platform.trim() && p.url.trim()) social_urls[p.platform.trim().toLowerCase()] = p.url.trim();
    });

    onSubmit({
      ...form,
      social_urls,
      focus_areas: focusAreas,
    });
  };

  /* ── Shared input styles ───────────────────────────────── */
  const inputClass = (field) =>
    `w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl font-sans text-sm text-slate-900 dark:text-white
     placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
     transition-all ${errors[field] ? 'border-red-500 ring-1 ring-red-500' : ''}`;

  return (
    <div className="animate-fade-in-up max-w-3xl">
      {/* ── Hero ─────────────────────────────────────────── */}
      <div className="text-left mb-10">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          {title}
        </h1>
        <p className="text-sm text-slate-500">
          {subtitle}
        </p>
      </div>

      {/* ── Form Card ────────────────────────────────────── */}
      <form onSubmit={handleSubmit}>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-6 md:p-8">
          <div className="space-y-6">
            
            {/* ── Company Name ──────────────────────────── */}
            <div>
              <label className="font-heading text-xs font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 flex items-center gap-2 mb-2">
                <Building2 size={14} strokeWidth={3} /> {companyLabel} *
              </label>
              <input
                type="text"
                value={form.company_name}
                onChange={e => update('company_name', e.target.value)}
                placeholder={companyPlaceholder}
                className={inputClass('company_name')}
              />
              {errors.company_name && <span className="text-accent text-xs font-mono uppercase tracking-wider mt-1.5 block">Error: {errors.company_name}</span>}
            </div>

            {/* ── Website URL ──────────────────────────── */}
            <div>
              <label className="font-heading text-xs font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 flex items-center gap-2 mb-2">
                <Globe size={14} strokeWidth={3} /> Website URL *
              </label>
              <input
                type="url"
                value={form.website_url}
                onChange={e => update('website_url', e.target.value)}
                placeholder="https://www.example.com"
                className={inputClass('website_url')}
              />
              {errors.website_url && <span className="text-accent text-xs font-mono uppercase tracking-wider mt-1.5 block">Error: {errors.website_url}</span>}
            </div>

            {/* ── Industry ─────────────────────────────── */}
            <div>
              <label className="font-heading text-xs font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 flex items-center gap-2 mb-2">
                <Search size={14} strokeWidth={3} /> Industry *
              </label>
              <input
                type="text"
                value={form.industry}
                onChange={e => update('industry', e.target.value)}
                placeholder="e.g. Athletic Footwear & Apparel"
                className={inputClass('industry')}
              />
              {errors.industry && <span className="text-accent text-xs font-mono uppercase tracking-wider mt-1.5 block">Error: {errors.industry}</span>}
            </div>

            {/* ── Our Company Context ──────────────────── */}
            <div>
              <label className="font-heading text-xs font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 flex items-center gap-2 mb-2">
                <Users size={14} strokeWidth={3} /> Your Company Context
                <span className="opacity-50 text-[10px] lowercase font-mono"> (optional)</span>
              </label>
              <textarea
                value={form.our_company_context}
                onChange={e => update('our_company_context', e.target.value)}
                placeholder="Describe your positioning to customize differentiation recommendations..."
                rows={3}
                className={`${inputClass('our_company_context')} resize-none`}
              />
            </div>

            {/* ── Divider ──────────────────────────────── */}
            <hr className="border-t-2 border-black dark:border-white" />

            {/* ── Social URLs ──────────────────────────── */}
            <div>
              <label className="font-heading text-xs font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 block mb-3">
                Social Profiles <span className="opacity-50 text-[10px] lowercase font-mono">(optional)</span>
              </label>

              {socialPairs.length > 0 && (
                <div className="space-y-3 mb-4">
                  {socialPairs.map((pair, i) => (
                    <div key={i} className="flex gap-2 items-start animate-fade-in-up">
                      <input
                        type="text"
                        value={pair.platform}
                        onChange={e => updateSocialPair(i, 'platform', e.target.value)}
                        placeholder="platform"
                        className="w-1/3 px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <input
                        type="url"
                        value={pair.url}
                        onChange={e => updateSocialPair(i, 'url', e.target.value)}
                        placeholder="https://instagram.com/company"
                        className="flex-1 px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        type="button"
                        onClick={() => removeSocialPair(i)}
                        className="p-2.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors shrink-0"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <button
                type="button"
                onClick={addSocialPair}
                className="flex items-center gap-2 px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg
                           text-slate-600 dark:text-slate-400 text-sm font-medium
                           hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <Plus size={16} /> Add Social URL
              </button>
            </div>

            {/* ── Divider ──────────────────────────────── */}
            <hr className="border-t border-slate-100 dark:border-slate-800" />

            {/* ── Focus Areas ──────────────────────────── */}
            <div>
              <label className="font-heading text-xs font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 block mb-3">
                Focus Areas
              </label>
              <div className="flex flex-wrap gap-2">
                {FOCUS_OPTIONS.map(area => {
                  const active = focusAreas.includes(area);
                  return (
                    <button
                      key={area}
                      type="button"
                      onClick={() => toggleFocus(area)}
                      className={`px-4 py-2 text-xs font-medium rounded-lg capitalize transition-colors
                                  ${active
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
                                  }`}
                    >
                      {area}
                    </button>
                  );
                })}
              </div>
              {errors.focus && <span className="text-red-500 text-xs mt-2 block">{errors.focus}</span>}
            </div>
          </div>

          {/* ── Submit Button ──────────────────────────── */}
          <div className="mt-8 border-t border-slate-100 dark:border-slate-800 pt-6">
            <button
              type="submit"
              className="inline-flex items-center justify-center w-full md:w-auto gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-medium shadow-sm hover:bg-blue-700 transition-colors"
            >
              <Sparkles size={18} /> {submitLabel}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
