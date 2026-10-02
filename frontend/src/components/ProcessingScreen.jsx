import { useState, useEffect, useRef } from 'react';
import { Loader2, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';
import { getSetupStatus, apiPost } from '../api';

export default function ProcessingScreen({ onComplete }) {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('Starting competitive analysis...');
  const [status, setStatus] = useState('PROCESSING'); // PROCESSING, PENDING, COMPLETED, FAILED
  const [errorMessage, setErrorMessage] = useState('');
  const [isRetrying, setIsRetrying] = useState(false);
  const intervalRef = useRef(null);
  const timeoutRef = useRef(null);

  const startPolling = () => {
    // Clear any existing interval before starting a new one
    if (intervalRef.current) clearInterval(intervalRef.current);

    const checkStatus = async () => {
      try {
        const data = await getSetupStatus();
        if (data) {
          if (typeof data.progress === 'number') {
            setProgress(data.progress);
          }
          if (data.currentStep) {
            setCurrentStep(data.currentStep);
          }

          const currentStatus = data.status || data.setupStatus;

          if (currentStatus === 'COMPLETED') {
            setStatus('COMPLETED');
            setProgress(100);
            setCurrentStep('Analysis Complete!');
            if (intervalRef.current) clearInterval(intervalRef.current);
            timeoutRef.current = setTimeout(() => {
              if (onComplete) onComplete();
            }, 1000);
          } else if (currentStatus === 'FAILED') {
            setStatus('FAILED');
            setErrorMessage(data.error || 'Something went wrong during setup.');
            if (intervalRef.current) clearInterval(intervalRef.current);
          }
        }
      } catch (err) {
        console.error('Polling setup-status error:', err);
        // Keep polling even if temporary network error occurs
      }
    };

    // Fetch immediately on start, then every 2 seconds
    checkStatus();
    intervalRef.current = setInterval(checkStatus, 2000);
  };

  useEffect(() => {
    startPolling();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const handleRetry = async () => {
    setIsRetrying(true);
    setErrorMessage('');
    try {
      await apiPost('/api/company/trigger-discovery', {});
      setStatus('PROCESSING');
      setProgress(5);
      setCurrentStep('Restarting competitive analysis...');
      startPolling();
    } catch (err) {
      console.error('Failed to trigger discovery retry:', err);
      setErrorMessage(err.message || 'Could not restart setup. Please try again.');
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-black text-slate-900 dark:text-slate-100 font-sans flex flex-col items-center justify-between p-6 md:p-12 relative overflow-hidden">
      
      {/* Top Header / App Logo */}
      <div className="w-full max-w-2xl flex items-center justify-center gap-3 py-4">
        <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-extrabold text-base shadow-md">
          Ae
        </div>
        <span className="font-extrabold text-2xl tracking-tight text-slate-900 dark:text-white">
          Aetheris
        </span>
      </div>

      {/* Main Card */}
      <div className="w-full max-w-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-xl p-8 md:p-12 my-auto text-center space-y-8 animate-fade-in relative z-10">
        
        {status === 'PROCESSING' && (
          <>
            <div>
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 mb-6 shadow-inner">
                <Loader2 className="w-8 h-8 animate-spin" />
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                Setting up your competitive intelligence dashboard
              </h1>
              <p className="text-slate-500 dark:text-slate-400 text-sm md:text-base mt-3 leading-relaxed">
                We are analyzing your market and discovering your competitors. This usually takes 1 to 2 minutes.
              </p>
            </div>

            {/* Progress Bar & Status */}
            <div className="space-y-4 pt-2">
              <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-3.5 overflow-hidden p-0.5 border border-slate-200/50 dark:border-slate-700/50">
                <div 
                  className="bg-blue-600 h-full rounded-full transition-all duration-500 ease-out shadow-sm"
                  style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                />
              </div>

              <div className="flex justify-between items-center text-xs font-semibold">
                <span className="text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping inline-block" />
                  {currentStep}
                </span>
                <span className="text-slate-400 dark:text-slate-500 font-mono">
                  {Math.round(progress)}%
                </span>
              </div>
            </div>

            {/* Estimated Time Note */}
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-xs font-medium text-slate-400 dark:text-slate-500">
              Estimated time: 1 to 2 minutes
            </div>
          </>
        )}

        {status === 'COMPLETED' && (
          <div className="py-6 space-y-6 animate-fade-in">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 mx-auto">
              <CheckCircle2 className="w-10 h-10 animate-bounce" />
            </div>
            <div>
              <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white">
                Your dashboard is ready!
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mt-2">
                Redirecting to your competitive intelligence workspace...
              </p>
            </div>
          </div>
        )}

        {status === 'FAILED' && (
          <div className="py-4 space-y-6 animate-fade-in">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 mx-auto">
              <AlertCircle className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                Something went wrong during setup.
              </h2>
              <p className="text-slate-500 dark:text-slate-400 text-sm mt-2 max-w-md mx-auto">
                {errorMessage || 'An error occurred while building your competitor report. Please try again.'}
              </p>
            </div>

            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-xl transition-all shadow-md hover:shadow-lg disabled:opacity-50"
            >
              {isRetrying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Restarting...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </>
              )}
            </button>
          </div>
        )}

      </div>

      {/* Footer Branding */}
      <div className="text-xs text-slate-400 dark:text-slate-600 font-medium">
        Powered by Aetheris Business Intelligence Agent
      </div>

    </div>
  );
}
