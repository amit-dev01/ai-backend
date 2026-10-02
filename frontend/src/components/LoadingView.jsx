import { useState, useEffect } from 'react';

const STEPS = [
  { label: 'Scraping website content…',      emoji: '🌐', duration: 5000 },
  { label: 'Extracting business signals…',    emoji: '🔍', duration: 8000 },
  { label: 'Running competitive analysis…',   emoji: '🧠', duration: 12000 },
  { label: 'Generating executive report…',    emoji: '📝', duration: 0 },      // stays until API returns
];

export default function LoadingView() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const timers = [];
    let elapsed = 0;
    STEPS.forEach((step, i) => {
      if (i === 0) return; // first step is immediately active
      elapsed += STEPS[i - 1].duration;
      if (step.duration > 0 || i === STEPS.length - 1) {
        timers.push(setTimeout(() => setActiveStep(i), elapsed));
      }
    });
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] animate-fade-in-up">
      {/* Main card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 md:p-12 w-full max-w-lg relative rounded-2xl shadow-sm">
        
        {/* Status indicator tag */}
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-6">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" /> Processing
        </div>

        <h2 className="text-xl md:text-2xl font-bold mb-8 text-slate-900 dark:text-white">
          Synthesizing Market Data
        </h2>

        {/* Steps checklist */}
        <ul className="space-y-6">
          {STEPS.map((step, i) => {
            const done    = i < activeStep;
            const current = i === activeStep;
            return (
              <li
                key={i}
                className={`flex items-start gap-4 transition-all duration-150
                            ${done ? 'opacity-50' : current ? 'opacity-100' : 'opacity-20'}`}
              >
                {/* Checkbox indicator */}
                <div
                  className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center transition-colors
                              ${done ? 'bg-blue-500 text-white' : 'bg-slate-100 dark:bg-slate-800'}`}
                >
                  {done && (
                    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" className="animate-fade-in">
                      <path d="M3 8.5 L6.5 12 L13 4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                  {current && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  )}
                </div>

                {/* Label & progress line */}
                <div className="flex-1">
                  <span className={`text-sm font-medium ${done ? 'text-slate-400 dark:text-slate-600' : 'text-slate-900 dark:text-white'}`}>
                    {step.emoji} {step.label}
                  </span>
                  {current && (
                    <div className="mt-3 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{
                          animation: 'draw-in linear forwards',
                          animationDuration: step.duration > 0 ? `${step.duration}ms` : '20000ms',
                        }}
                      />
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>

        {/* CSS keyframe inject for stark drawing loading indicator */}
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes draw-in {
            from { width: 0%; }
            to { width: 100%; }
          }
        `}} />

        {/* Bottom message */}
        <p className="text-xs text-slate-500 text-center mt-8 font-medium">
          Estimated completion: 30s - 90s
        </p>
      </div>
    </div>
  );
}
