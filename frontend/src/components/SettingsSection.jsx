import { useState, useEffect, useContext, useRef } from 'react';
import { 
  Building, Settings as SettingsIcon, Search, Activity, 
  Loader2, CheckCircle2, AlertCircle, X, Clock, Edit, Check 
} from 'lucide-react';
import { DbContext } from '../App';
import { 
  getCompanyProfile, updateCompanyProfile, 
  getCompanySettings, updateCompanySettings, triggerRediscovery, getCompanyActivity 
} from '../api';
import { MULTI_SELECT_OPTIONS } from '../constants';

function CompanyProfileTab({ showToast, setAppState }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [showRediscoverModal, setShowRediscoverModal] = useState(false);
  
  const [initialData, setInitialData] = useState(null);
  const [formData, setFormData] = useState({
    companyName: '',
    website: '',
    industry: '',
    description: '',
    productsOrServices: [],
    targetCustomers: '',
    companyStage: '',
    companySize: '',
    customerSegments: [],
    geographies: [],
    targetType: 'B2B',
  });

  const [productInput, setProductInput] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await getCompanyProfile();
        const comp = data.company || data;
        
        let segments = [];
        let targetType = 'B2B';
        if (comp.targetCustomers) {
          const parts = comp.targetCustomers.split(' - ');
          targetType = parts[0] || 'B2B';
          if (parts[1]) {
            segments = parts[1].split(', ').map(s => s.trim());
          }
        }

        const initial = {
          companyName: comp.companyName || comp.name || '',
          website: comp.website || '',
          industry: comp.industry || '',
          description: comp.description || '',
          productsOrServices: comp.productsOrServices ? comp.productsOrServices.split(', ').filter(Boolean) : [],
          targetType,
          customerSegments: segments,
          geographies: [], 
          companyStage: comp.companyStage || 'Startup',
          companySize: comp.companySize || '11-50'
        };
        
        setInitialData(initial);
        setFormData(initial);
      } catch (err) {
        setError('Failed to load company profile.');
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const updateForm = (key, value) => setFormData(prev => ({ ...prev, [key]: value }));
  const toggleMultiSelect = (key, val) => {
    setFormData(prev => {
      const arr = prev[key] || [];
      if (arr.includes(val)) return { ...prev, [key]: arr.filter(item => item !== val) };
      return { ...prev, [key]: [...arr, val] };
    });
  };

  const addProduct = () => {
    if (!productInput.trim()) return;
    setFormData(prev => ({
      ...prev,
      productsOrServices: [...(prev.productsOrServices || []), productInput.trim()]
    }));
    setProductInput('');
  };
  const removeProduct = (idx) => {
    setFormData(prev => ({
      ...prev,
      productsOrServices: prev.productsOrServices.filter((_, i) => i !== idx)
    }));
  };

  const isDirty = JSON.stringify(formData) !== JSON.stringify(initialData);

  const handleSave = async () => {
    if (!formData.companyName || formData.companyName.length < 2 || formData.companyName.length > 100) {
      showToast('Company name must be between 2 and 100 characters', 'error');
      return;
    }
    if (!formData.website || !formData.website.startsWith('http')) {
      showToast('Website must be a valid URL starting with http', 'error');
      return;
    }
    if (!formData.description || formData.description.length < 10) {
      showToast('Description must be at least 10 characters', 'error');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        companyName: formData.companyName,
        website: formData.website,
        industry: formData.industry,
        description: formData.description,
        productsOrServices: formData.productsOrServices.join(', '),
        targetCustomers: formData.targetType + (formData.customerSegments.length ? ' - ' + formData.customerSegments.join(', ') : ''),
        companyStage: formData.companyStage,
        companySize: formData.companySize,
      };

      const res = await updateCompanyProfile(payload);
      setInitialData(formData);
      showToast('Profile updated successfully', 'success');

      if (res.significantChange) {
        setShowRediscoverModal(true);
      }
    } catch (err) {
      console.error(err);
      showToast(err.message || 'Failed to update profile.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleRediscover = () => {
    setShowRediscoverModal(false);
    triggerRediscovery().then(() => {
       setAppState('PROCESSING');
    }).catch(err => showToast(err.message || 'Could not start rediscovery', 'error'));
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-6 w-1/3 bg-slate-200 dark:bg-slate-700 rounded"></div>
        <div className="grid grid-cols-2 gap-4"><div className="h-10 bg-slate-200 dark:bg-slate-700 rounded"></div><div className="h-10 bg-slate-200 dark:bg-slate-700 rounded"></div></div>
        <div className="h-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
      </div>
    );
  }

  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Company Basics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Company Name *</label>
            <input type="text" value={formData.companyName} onChange={e => updateForm('companyName', e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Website *</label>
            <input type="url" value={formData.website} onChange={e => updateForm('website', e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Industry *</label>
            <input type="text" value={formData.industry} onChange={e => updateForm('industry', e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Stage</label>
              <select value={formData.companyStage} onChange={e => updateForm('companyStage', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500">
                <option>Startup</option><option>Small Business</option><option>Mid-market</option><option>Enterprise</option><option>Other</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Size</label>
              <select value={formData.companySize} onChange={e => updateForm('companySize', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500">
                <option>1–10</option><option>11–50</option><option>51–200</option><option>201–500</option><option>501–1000</option><option>1000+</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Description</h2>
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Short Company Description *</label>
          <textarea value={formData.description} onChange={e => updateForm('description', e.target.value)} rows={3}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Market</h2>
        <div className="space-y-3">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Business Type</label>
          <div className="flex gap-4">
            {['B2B', 'B2C', 'Both'].map(type => (
              <label key={type} className="flex items-center gap-2 text-sm cursor-pointer text-slate-700 dark:text-slate-300">
                <input type="radio" name="target" value={type} checked={formData.targetType === type} onChange={() => updateForm('targetType', type)} className="text-blue-600 focus:ring-blue-500" />
                {type}
              </label>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Target Customer Segments</label>
          <div className="flex flex-wrap gap-2">
            {MULTI_SELECT_OPTIONS.customer_segments.map(opt => (
              <button key={opt} onClick={() => toggleMultiSelect('customerSegments', opt)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${formData.customerSegments?.includes(opt) ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600'}`}>
                {opt}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-3">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Geographic Markets</label>
          <div className="flex flex-wrap gap-2">
            {MULTI_SELECT_OPTIONS.geographies.map(opt => (
              <button key={opt} onClick={() => toggleMultiSelect('geographies', opt)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${formData.geographies?.includes(opt) ? 'bg-blue-600 border-blue-600 text-white' : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600'}`}>
                {opt}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Product</h2>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Main Products or Services</label>
          <div className="flex gap-2">
            <input type="text" value={productInput} onChange={e => setProductInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addProduct())}
              className="flex-1 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500" placeholder="e.g. AI Analytics Platform" />
            <button onClick={addProduct} className="px-4 py-2 bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 rounded-lg hover:bg-slate-800 dark:hover:bg-white font-medium text-sm">Add</button>
          </div>
          {formData.productsOrServices?.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.productsOrServices.map((prod, idx) => (
                <span key={idx} className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-md text-sm text-slate-800 dark:text-slate-200">
                  {prod} <button onClick={() => removeProduct(idx)} className="text-slate-400 hover:text-red-500"><X size={14} /></button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="pt-6 border-t border-slate-200 dark:border-slate-800 flex gap-3">
        <button 
          onClick={handleSave} 
          disabled={!isDirty || saving}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all shadow-sm disabled:opacity-50 flex items-center gap-2"
        >
          {saving ? <><Loader2 size={16} className="animate-spin" /> Saving...</> : 'Save Changes'}
        </button>
        <button 
          onClick={() => setFormData(initialData)} 
          disabled={!isDirty || saving}
          className="px-5 py-2.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
      </div>

      {showRediscoverModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 max-w-sm w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <AlertCircle className="text-blue-500 w-5 h-5" />
              Your competitive landscape may have changed
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              You updated core details about your business. Your current competitor list may no longer be accurate. Would you like to re-discover competitors with your updated profile?
            </p>
            <div className="flex gap-2 justify-end pt-2">
              <button onClick={() => setShowRediscoverModal(false)} className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
                Maybe Later
              </button>
              <button onClick={handleRediscover} className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-sm">
                Re-discover Competitors
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MonitoringPreferencesTab({ showToast }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingField, setSavingField] = useState('');
  const [showPauseModal, setShowPauseModal] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await getCompanySettings();
        setSettings(data);
      } catch (err) {
        showToast('Failed to load settings', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, [showToast]);

  const handleToggle = async (field, value) => {
    if (field === 'monitoringEnabled' && value === false) {
      setShowPauseModal(true);
      return;
    }
    await saveSetting(field, value);
  };

  const saveSetting = async (field, value) => {
    const prevValue = settings[field];
    // Optimistic
    setSettings(prev => ({ ...prev, [field]: value }));
    setSavingField(field);
    try {
      await updateCompanySettings({ [field]: value });
      showToast('Setting saved', 'success');
    } catch (err) {
      setSettings(prev => ({ ...prev, [field]: prevValue }));
      showToast('Failed to save setting', 'error');
    } finally {
      setSavingField('');
    }
  };

  const handleConfirmPause = () => {
    setShowPauseModal(false);
    saveSetting('monitoringEnabled', false);
  };

  const handleLimitChange = (e) => {
    let val = parseInt(e.target.value);
    if (isNaN(val)) val = 1;
    if (val < 1) val = 1;
    if (val > 25) val = 25;
    
    setSettings(prev => ({ ...prev, maxCompetitorsMonitored: val }));
    
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      saveSetting('maxCompetitorsMonitored', val);
    }, 500);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
        <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
        <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="space-y-6">
        
        {/* Toggle 1 */}
        <div className="flex items-start justify-between gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              Competitor Monitoring
              {savingField === 'monitoringEnabled' && <Loader2 size={14} className="animate-spin text-blue-500" />}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              When enabled, we check your competitors daily for news, product updates, and market activity.
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer shrink-0 mt-1">
            <input type="checkbox" className="sr-only peer" checked={!!settings?.monitoringEnabled} onChange={e => handleToggle('monitoringEnabled', e.target.checked)} />
            <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer dark:bg-slate-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Toggle 2 */}
        <div className="flex items-start justify-between gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              Weekly intelligence digest
              {savingField === 'emailDigestEnabled' && <Loader2 size={14} className="animate-spin text-blue-500" />}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Receive a summary of the week's competitive intelligence every Monday.
            </p>
            <p className="text-xs text-blue-500 font-medium mt-1">Email delivery coming soon</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer shrink-0 mt-1">
            <input type="checkbox" className="sr-only peer" checked={!!settings?.emailDigestEnabled} onChange={e => handleToggle('emailDigestEnabled', e.target.checked)} />
            <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer dark:bg-slate-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Toggle 3 */}
        <div className="flex items-start justify-between gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              Critical alert notifications
              {savingField === 'criticalAlertsEnabled' && <Loader2 size={14} className="animate-spin text-blue-500" />}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Get notified immediately when critical competitive events are detected.
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer shrink-0 mt-1">
            <input type="checkbox" className="sr-only peer" checked={!!settings?.criticalAlertsEnabled} onChange={e => handleToggle('criticalAlertsEnabled', e.target.checked)} />
            <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer dark:bg-slate-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-slate-600 peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Limit */}
        <div className="flex items-start justify-between gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              Maximum competitors to monitor
              {savingField === 'maxCompetitorsMonitored' && <Loader2 size={14} className="animate-spin text-blue-500" />}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Higher tiers monitor more competitors. We monitor your top competitors by competitive score.
            </p>
            <div className="mt-2 text-xs text-slate-500">
              You are monitoring {settings?.activeCompetitors || 0} competitors ({settings?.archivedCompetitors || 0} archived)
            </div>
          </div>
          <input type="number" min="1" max="25" value={settings?.maxCompetitorsMonitored || 5} onChange={handleLimitChange}
            className="w-20 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-center font-bold" />
        </div>

      </div>

      {showPauseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 max-w-sm w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Pause competitor monitoring?</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              We will stop collecting intelligence about your competitors. Historical data will be preserved. You can resume anytime.
            </p>
            <div className="flex gap-2 justify-end pt-2">
              <button onClick={() => setShowPauseModal(false)} className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
                Keep Monitoring
              </button>
              <button onClick={handleConfirmPause} className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-lg hover:bg-red-700 shadow-sm">
                Pause Monitoring
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function DiscoveryTab({ showToast, setAppState }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await getCompanySettings();
        setSettings(data);
      } catch (err) {
        showToast('Failed to load discovery info', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, [showToast]);

  const handleRun = async () => {
    setShowConfirm(false);
    setRunning(true);
    try {
      await triggerRediscovery();
      setAppState('PROCESSING');
    } catch (err) {
      if (err.message?.includes('429')) {
        showToast('You have reached your discovery run limit.', 'error');
      } else {
        showToast(err.message || 'Failed to start discovery.', 'error');
      }
      setRunning(false);
    }
  };

  if (loading) {
    return <div className="animate-pulse h-32 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>;
  }

  const runCount = settings?.discoveryRunCount || 0;
  const maxRuns = 3;
  const runsRemaining = maxRuns - runCount;
  const nextRunDate = new Date();
  nextRunDate.setMonth(nextRunDate.getMonth() + 1);

  return (
    <div className="space-y-8 animate-fade-in">
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 flex flex-col items-center justify-center text-center space-y-3">
          <Search size={32} className="text-blue-600" />
          <div>
            <h3 className="font-bold text-2xl text-slate-900 dark:text-white">{runsRemaining}</h3>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">runs remaining this period</p>
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Last discovery: {settings?.lastDiscoveryAt ? new Date(settings.lastDiscoveryAt).toLocaleDateString() : 'Never'}
          </div>
          
          <button 
            disabled={runsRemaining <= 0 || running}
            onClick={() => setShowConfirm(true)}
            className="mt-4 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all shadow-sm disabled:opacity-50 flex items-center gap-2"
          >
            {running ? <Loader2 size={16} className="animate-spin" /> : null}
            Run Discovery Again
          </button>
          
          {runsRemaining <= 0 && (
            <div className="text-xs text-amber-600 mt-2 font-medium">
              Next run available on {nextRunDate.toLocaleDateString()}
            </div>
          )}
        </div>

        <div className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 space-y-3">
          <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
            How competitor discovery works
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            We analyze your company profile and search the web for companies with similar products, customers, and markets. 
          </p>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Existing competitors are never duplicated. Your accepted, rejected, and customized competitors are always preserved.
          </p>
        </div>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 max-w-sm w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Re-run competitor discovery?</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              This will search for new competitors based on your current profile. Your existing competitors, notes, and customizations will not be affected. This uses 1 of your {maxRuns} monthly discovery runs.
            </p>
            <div className="flex gap-2 justify-end pt-2">
              <button onClick={() => setShowConfirm(false)} className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
                Cancel
              </button>
              <button onClick={handleRun} className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 shadow-sm">
                Run Discovery
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ActivityLogTab() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 20;

  useEffect(() => {
    const fetchInit = async () => {
      try {
        const data = await getCompanyActivity(limit, 0);
        const list = Array.isArray(data) ? data : data.activities || [];
        setActivities(list);
        if (list.length < limit) setHasMore(false);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchInit();
  }, []);

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const nextOffset = offset + limit;
      const data = await getCompanyActivity(limit, nextOffset);
      const list = Array.isArray(data) ? data : data.activities || [];
      setActivities(prev => [...prev, ...list]);
      setOffset(nextOffset);
      if (list.length < limit) setHasMore(false);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMore(false);
    }
  };

  const getIcon = (type) => {
    switch(type) {
      case 'PROFILE_UPDATED': return <Edit className="w-4 h-4 text-blue-500" />;
      case 'COMPETITOR_ADDED': return <Building className="w-4 h-4 text-emerald-500" />;
      case 'COMPETITOR_EDITED': return <Edit className="w-4 h-4 text-amber-500" />;
      case 'COMPETITOR_DELETED': return <Trash2 className="w-4 h-4 text-red-500" />;
      case 'COMPETITOR_REARCHIVED': return <Activity className="w-4 h-4 text-slate-500" />; 
      case 'COMPETITOR_RESTORED': return <Check className="w-4 h-4 text-emerald-500" />; 
      case 'DISCOVERY_RERUN': return <Search className="w-4 h-4 text-purple-500" />;
      case 'SETTINGS_UPDATED': return <SettingsIcon className="w-4 h-4 text-slate-500" />;
      default: return <Activity className="w-4 h-4 text-slate-400" />;
    }
  };

  const formatRelativeTime = (dateStr) => {
    if (!dateStr) return 'unknown';
    const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    const diff = new Date(dateStr).getTime() - Date.now();
    const diffDays = Math.round(diff / (1000 * 60 * 60 * 24));
    if (diffDays === 0) {
      const diffHours = Math.round(diff / (1000 * 60 * 60));
      if (diffHours === 0) return 'just now';
      return rtf.format(diffHours, 'hour');
    }
    return rtf.format(diffDays, 'day');
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
        <div className="h-16 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-500 dark:text-slate-400 space-y-4 text-center">
        <Clock className="w-12 h-12 opacity-50" />
        <p>No activity yet. Actions you take will appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in pb-8">
      {activities.map((act, i) => (
        <div key={act.id || i} className="flex items-start gap-4 p-4 border-b border-slate-100 dark:border-slate-800 last:border-0">
          <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0 mt-0.5">
            {getIcon(act.type)}
          </div>
          <div>
            <p className="text-sm font-medium text-slate-900 dark:text-white">{act.description}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{formatRelativeTime(act.createdAt)}</p>
          </div>
        </div>
      ))}
      
      {hasMore && (
        <div className="pt-4 flex justify-center">
          <button 
            onClick={loadMore} 
            disabled={loadingMore}
            className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
          >
            {loadingMore ? <Loader2 size={16} className="animate-spin" /> : null}
            Load More
          </button>
        </div>
      )}
    </div>
  );
}

function IntegrationsTab({ showToast }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingField, setSavingField] = useState('');
  const [jiraInput, setJiraInput] = useState('');
  const [extractedDomain, setExtractedDomain] = useState('');
  const debounceRef = useRef(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await getCompanySettings();
        setSettings(data);
        setJiraInput(data.jiraDomain || '');
      } catch (err) {
        showToast('Failed to load settings', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, [showToast]);

  const saveSetting = async (field, value) => {
    const prevValue = settings?.[field];
    setSettings(prev => ({ ...prev, [field]: value }));
    setSavingField(field);
    try {
      await updateCompanySettings({ [field]: value });
      showToast('Setting saved', 'success');
    } catch (err) {
      setSettings(prev => ({ ...prev, [field]: prevValue }));
      showToast('Failed to save setting', 'error');
    } finally {
      setSavingField('');
    }
  };

  const handleJiraDomainChange = (e) => {
    let val = e.target.value;
    setExtractedDomain('');
    
    // Auto-extract subdomain if full URL is pasted
    if (val.includes('atlassian.net')) {
      try {
        const url = new URL(val.startsWith('http') ? val : `https://${val}`);
        const hostParts = url.hostname.split('.');
        if (hostParts.length >= 3) {
          val = hostParts[0];
          setExtractedDomain(val);
        }
      } catch (err) {
        // ignore parsing error
      }
    }
    
    // basic sanitize
    val = val.replace(/[^a-zA-Z0-9-]/g, '');
    
    setJiraInput(val);
    
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      saveSetting('jiraDomain', val);
    }, 800);
  };

  if (loading) {
    return <div className="animate-pulse h-32 bg-slate-200 dark:bg-slate-700 rounded-xl"></div>;
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
              Jira Integration
              {savingField === 'jiraDomain' ? (
                <Loader2 size={14} className="animate-spin text-blue-500" />
              ) : (
                settings?.jiraDomain === jiraInput && jiraInput !== '' && <CheckCircle2 size={14} className="text-emerald-500" />
              )}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Enter your Jira subdomain to enable one-click task export.
              For example if your Jira URL is acme-corp.atlassian.net enter: <strong>acme-corp</strong>
            </p>
          </div>
          
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Jira Domain</label>
            <input 
              type="text" 
              value={jiraInput} 
              onChange={handleJiraDomainChange}
              placeholder="your-company"
              className="mt-1 w-full max-w-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500" 
            />
            
            {extractedDomain && (
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-2 font-medium">
                We extracted your subdomain: {extractedDomain}
              </p>
            )}
            {jiraInput && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 font-medium">
                Your Jira URL will be: {jiraInput}.atlassian.net
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SettingsSection() {
  const { setAppState } = useContext(DbContext);
  const [activeTab, setActiveTab] = useState('profile');
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const tabs = [
    { id: 'profile', label: 'Company Profile' },
    { id: 'monitoring', label: 'Monitoring Preferences' },
    { id: 'integrations', label: 'Integrations' },
    { id: 'discovery', label: 'Discovery' },
    { id: 'activity', label: 'Activity Log' }
  ];

  return (
    <div className="animate-fade-in-up max-w-5xl mx-auto space-y-6 relative pb-12">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white dark:bg-white dark:text-slate-900 px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-3 animate-fade-in text-sm font-semibold border border-slate-800 dark:border-slate-200">
          {toast.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 dark:text-emerald-600" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-400 dark:text-red-600" />
          )}
          <span>{toast.msg}</span>
        </div>
      )}

      <div className="flex items-center gap-3 mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
          <SettingsIcon className="w-8 h-8 text-blue-600" />
          Settings
        </h1>
      </div>

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm flex flex-col md:flex-row overflow-hidden">
        
        {/* Sidebar Nav */}
        <div className="md:w-64 border-b md:border-b-0 md:border-r border-slate-200 dark:border-slate-800 p-4 space-y-1 bg-slate-50/50 dark:bg-slate-950/50">
          {tabs.map(t => (
            <button 
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                activeTab === t.id 
                  ? 'bg-white dark:bg-slate-800 text-blue-600 shadow-sm border border-slate-200 dark:border-slate-700' 
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 p-6 md:p-8 min-h-[500px]">
          {activeTab === 'profile' && <CompanyProfileTab showToast={showToast} setAppState={setAppState} />}
          {activeTab === 'monitoring' && <MonitoringPreferencesTab showToast={showToast} />}
          {activeTab === 'integrations' && <IntegrationsTab showToast={showToast} />}
          {activeTab === 'discovery' && <DiscoveryTab showToast={showToast} setAppState={setAppState} />}
          {activeTab === 'activity' && <ActivityLogTab />}
        </div>
      </div>
    </div>
  );
}
