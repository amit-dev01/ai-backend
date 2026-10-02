import { useState } from 'react';
import { ChevronRight, ChevronLeft, Check, Plus, X, Building, Target, Users, Loader2 } from 'lucide-react';
import { submitCompanyProfile } from '../api';
import { MULTI_SELECT_OPTIONS } from '../constants';

export default function OnboardingFlow({ onComplete }) {
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    // Step 1
    company_name: '',
    website_url: '',
    industry: '',
    description: '',
    stage: 'Startup',
    size: '1–10',
    // Step 2
    target_customers: 'B2B',
    customer_segments: [],
    geographies: [],
    products_services: [],
    problem_solved: '',
    // Step 3
    competitor_discovery: 'I\'ll do both',
    competitors: [{ name: '' }],
    non_competitors: [{ name: '' }],
  });

  const [productInput, setProductInput] = useState('');

  const updateForm = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleMultiSelect = (field, option) => {
    setFormData((prev) => {
      const current = prev[field];
      if (current.includes(option)) {
        return { ...prev, [field]: current.filter(o => o !== option) };
      }
      return { ...prev, [field]: [...current, option] };
    });
  };

  const addProduct = () => {
    if (productInput.trim() !== '') {
      updateForm('products_services', [...formData.products_services, productInput.trim()]);
      setProductInput('');
    }
  };

  const removeProduct = (index) => {
    updateForm('products_services', formData.products_services.filter((_, i) => i !== index));
  };

  const updateCompetitor = (type, index, value) => {
    const list = [...formData[type]];
    list[index].name = value;
    updateForm(type, list);
  };

  const addCompetitor = (type) => {
    updateForm(type, [...formData[type], { name: '' }]);
  };

  const removeCompetitor = (type, index) => {
    updateForm(type, formData[type].filter((_, i) => i !== index));
  };

  const handleNext = () => setStep((s) => s + 1);
  const handleBack = () => setStep((s) => s - 1);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const payload = {
        companyName: formData.company_name,
        website: formData.website_url,
        industry: formData.industry,
        description: formData.description,
        productsOrServices: formData.products_services,
        targetCustomers: formData.target_customers + (formData.customer_segments.length ? ' - ' + formData.customer_segments.join(', ') : ''),
        companyStage: formData.stage,
        companySize: formData.size,
      };

      const resData = await submitCompanyProfile(payload);
      if (resData?.id || resData?.company?.id) {
        sessionStorage.setItem('company_id', resData?.id || resData?.company?.id);
      }
      if (onComplete) onComplete(resData);
    } catch (err) {
      console.error(err);
      setIsSubmitting(false);
      alert(err.message || 'Failed to submit onboarding form. Please try again.');
    }
  };

  if (isSubmitting) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100 dark:bg-black p-6">
        <div className="flex flex-col items-center max-w-md text-center animate-fade-in-up">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-6" />
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Building your competitive landscape...</h2>
          <p className="text-slate-500 dark:text-slate-400">Analyzing your market and identifying relevant competitors. This will just take a moment.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-black text-slate-900 dark:text-slate-100 font-sans flex flex-col items-center pt-12 pb-24 px-4 sm:px-6">
      
      <div className="w-full max-w-3xl mb-8 flex justify-between items-center text-sm font-medium">
        <div className="flex items-center gap-2">
           <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-sm">
             Ae
           </div>
           <span className="font-bold text-slate-900 dark:text-white">Aetheris Setup</span>
        </div>
        <div className="text-slate-500 bg-white dark:bg-slate-900 px-3 py-1 rounded-full border border-slate-200 dark:border-slate-800">
          Step {step} of 4
        </div>
      </div>

      <div className="w-full max-w-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm p-6 sm:p-10 animate-fade-in-up relative overflow-hidden">
        
        <div className="absolute top-0 left-0 h-1 bg-blue-600 transition-all duration-300" style={{ width: `${(step / 4) * 100}%` }}></div>

        {step === 1 && (
          <div className="space-y-6">
            <div className="mb-8">
              <div className="flex items-center gap-3 text-blue-600 mb-2">
                <Building size={24} />
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Let's understand your business</h1>
              </div>
              <p className="text-slate-500 dark:text-slate-400">Your company profile helps our intelligence engine discover relevant competitors and market signals.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Company name *</label>
                <input type="text" value={formData.company_name} onChange={e => updateForm('company_name', e.target.value)} 
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Acme Corp" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Company website *</label>
                <input type="text" value={formData.website_url} onChange={e => updateForm('website_url', e.target.value)} 
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="https://acme.com" />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Industry *</label>
                <input type="text" value={formData.industry} onChange={e => updateForm('industry', e.target.value)} 
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g. B2B SaaS, E-commerce, Fintech" />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Short company description *</label>
                <p className="text-xs text-slate-500">What does the company do?</p>
                <textarea value={formData.description} onChange={e => updateForm('description', e.target.value)} rows={3}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="We provide AI-powered analytics for retail businesses..." />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Company stage</label>
                <select value={formData.stage} onChange={e => updateForm('stage', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>Startup</option><option>Small business</option><option>Mid-market</option><option>Enterprise</option><option>Other</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Company size</label>
                <select value={formData.size} onChange={e => updateForm('size', e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>1–10</option><option>11–50</option><option>51–200</option><option>201–500</option><option>501–1000</option><option>1000+</option>
                </select>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-100 dark:border-slate-800 flex justify-end">
              <button onClick={handleNext} disabled={!formData.company_name || !formData.website_url || !formData.industry || !formData.description}
                className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm">
                Continue <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div className="mb-8">
              <div className="flex items-center gap-3 text-blue-600 mb-2">
                <Target size={24} />
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Tell us who you serve</h1>
              </div>
            </div>

            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Primary target customers</label>
                <div className="flex gap-4">
                  {['B2B', 'B2C', 'Both'].map(type => (
                    <label key={type} className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border cursor-pointer transition-colors ${formData.target_customers === type ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400' : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50'}`}>
                      <input type="radio" name="target" value={type} checked={formData.target_customers === type} onChange={() => updateForm('target_customers', type)} className="sr-only" />
                      <span className="font-medium text-sm">{type}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Customer segments</label>
                <div className="flex flex-wrap gap-2">
                  {MULTI_SELECT_OPTIONS.customer_segments.map(opt => (
                    <button key={opt} onClick={() => toggleMultiSelect('customer_segments', opt)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors ${formData.customer_segments.includes(opt) ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600'}`}>
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Primary geographic markets</label>
                <div className="flex flex-wrap gap-2">
                  {MULTI_SELECT_OPTIONS.geographies.map(opt => (
                    <button key={opt} onClick={() => toggleMultiSelect('geographies', opt)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium border transition-colors ${formData.geographies.includes(opt) ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600'}`}>
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Main products/services *</label>
                <div className="flex gap-2">
                  <input type="text" value={productInput} onChange={e => setProductInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addProduct())}
                    className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g. AI Analytics Platform" />
                  <button onClick={addProduct} className="px-4 py-2 bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 rounded-xl hover:bg-slate-800 dark:hover:bg-white font-medium">Add</button>
                </div>
                {formData.products_services.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {formData.products_services.map((prod, idx) => (
                      <span key={idx} className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg text-sm text-slate-800 dark:text-slate-200">
                        {prod} <button onClick={() => removeProduct(idx)} className="text-slate-400 hover:text-red-500"><X size={14} /></button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">What problem does your company primarily solve? *</label>
                <textarea value={formData.problem_solved} onChange={e => updateForm('problem_solved', e.target.value)} rows={3}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Briefly describe the main problem your product fixes..." />
              </div>
            </div>

            <div className="pt-6 border-t border-slate-100 dark:border-slate-800 flex justify-between">
              <button onClick={handleBack} className="flex items-center gap-2 px-6 py-2.5 text-slate-600 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-colors">
                <ChevronLeft size={18} /> Back
              </button>
              <button onClick={handleNext} disabled={formData.products_services.length === 0 || !formData.problem_solved}
                className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm">
                Continue <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div className="mb-8">
              <div className="flex items-center gap-3 text-blue-600 mb-2">
                <Users size={24} />
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Help us understand your competitive landscape</h1>
              </div>
              <p className="text-slate-500 dark:text-slate-400">You can add competitors yourself, or let our intelligence engine discover them for you.</p>
            </div>

            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Do you already know your competitors?</label>
                <div className="flex flex-col gap-3">
                  {['Yes, I\'ll add them', 'No, discover them for me', 'I\'ll do both'].map(opt => (
                    <label key={opt} className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-colors ${formData.competitor_discovery === opt ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400' : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50'}`}>
                      <input type="radio" name="discovery" value={opt} checked={formData.competitor_discovery === opt} onChange={() => updateForm('competitor_discovery', opt)} className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-sm">{opt}</span>
                    </label>
                  ))}
                </div>
              </div>

              {(formData.competitor_discovery === 'Yes, I\'ll add them' || formData.competitor_discovery === 'I\'ll do both') && (
                <div className="space-y-3 p-5 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-100 dark:border-slate-800">
                  <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Add competitors (Name or Website)</label>
                  {formData.competitors.map((comp, idx) => (
                    <div key={idx} className="flex gap-2">
                      <input type="text" value={comp.name} onChange={e => updateCompetitor('competitors', idx, e.target.value)}
                        className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g. Salesforce or salesforce.com" />
                      {formData.competitors.length > 1 && (
                        <button onClick={() => removeCompetitor('competitors', idx)} className="px-3 text-slate-400 hover:text-red-500"><X size={20} /></button>
                      )}
                    </div>
                  ))}
                  <button onClick={() => addCompetitor('competitors')} className="text-sm text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1 hover:underline mt-2">
                    <Plus size={16} /> Add another competitor
                  </button>
                </div>
              )}

              <div className="space-y-3">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Are there any companies you DON'T consider competitors? <span className="text-slate-400 font-normal">(Optional)</span></label>
                <p className="text-xs text-slate-500">This prevents our discovery engine from repeatedly suggesting irrelevant companies.</p>
                {formData.non_competitors.map((comp, idx) => (
                  <div key={idx} className="flex gap-2">
                    <input type="text" value={comp.name} onChange={e => updateCompetitor('non_competitors', idx, e.target.value)}
                      className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Irrelevant company name" />
                    {formData.non_competitors.length > 1 && (
                      <button onClick={() => removeCompetitor('non_competitors', idx)} className="px-3 text-slate-400 hover:text-red-500"><X size={20} /></button>
                    )}
                  </div>
                ))}
                <button onClick={() => addCompetitor('non_competitors')} className="text-sm text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1 hover:underline mt-2">
                  <Plus size={16} /> Add another
                </button>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-100 dark:border-slate-800 flex justify-between">
              <button onClick={handleBack} className="flex items-center gap-2 px-6 py-2.5 text-slate-600 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-colors">
                <ChevronLeft size={18} /> Back
              </button>
              <button onClick={handleNext}
                className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors shadow-sm">
                Review <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-8">
            <div className="text-center max-w-lg mx-auto mb-8">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 text-green-600 mx-auto rounded-full flex items-center justify-center mb-4">
                <Check size={32} />
              </div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Ready to build your dashboard</h1>
              <p className="text-slate-500 dark:text-slate-400">Review your information before we initialize your competitive intelligence engine.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-slate-50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-800">
              <div className="space-y-4">
                <h3 className="font-bold text-slate-800 dark:text-slate-200 border-b border-slate-200 dark:border-slate-700 pb-2">Your company</h3>
                <div>
                  <div className="text-sm font-medium text-slate-900 dark:text-white">{formData.company_name}</div>
                  <div className="text-xs text-slate-500 mt-1">{formData.industry}</div>
                  <div className="text-xs text-slate-500 mt-1">{formData.stage} · {formData.size}</div>
                  <div className="text-xs text-slate-500 mt-1">{formData.geographies.join(', ') || 'Global'}</div>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-bold text-slate-800 dark:text-slate-200 border-b border-slate-200 dark:border-slate-700 pb-2">Products</h3>
                <ul className="text-sm space-y-1 text-slate-600 dark:text-slate-300">
                  {formData.products_services.map((p, i) => <li key={i}>• {p}</li>)}
                </ul>
              </div>

              <div className="space-y-4">
                <h3 className="font-bold text-slate-800 dark:text-slate-200 border-b border-slate-200 dark:border-slate-700 pb-2">Target customers</h3>
                <div className="text-sm text-slate-600 dark:text-slate-300 mb-2">{formData.target_customers}</div>
                <ul className="text-sm space-y-1 text-slate-600 dark:text-slate-300">
                  {formData.customer_segments.map((c, i) => <li key={i}>• {c}</li>)}
                </ul>
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-900/30 p-5 rounded-2xl flex items-start gap-4">
              <div className="text-blue-600 mt-1"><Target size={20} /></div>
              <div>
                <h3 className="font-bold text-blue-900 dark:text-blue-100 text-sm mb-1">Competitive intelligence plan</h3>
                <div className="text-sm text-blue-800 dark:text-blue-300 flex flex-col gap-1">
                  {formData.competitor_discovery.includes('discover') || formData.competitor_discovery.includes('both') ? (
                    <span>✓ Automatically discover competitors</span>
                  ) : null}
                  {formData.competitor_discovery.includes('add') || formData.competitor_discovery.includes('both') ? (
                    <span>✓ Monitor {formData.competitors.filter(c => c.name).length} selected competitors</span>
                  ) : null}
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center">
              <button onClick={handleBack} className="flex items-center gap-2 px-6 py-2.5 text-slate-600 dark:text-slate-400 font-medium hover:text-slate-900 dark:hover:text-white transition-colors">
                <ChevronLeft size={18} /> Back
              </button>
              <button onClick={handleSubmit}
                className="px-8 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 text-lg">
                Build my intelligence dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
