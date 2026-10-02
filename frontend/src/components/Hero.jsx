import React from 'react';
import { ArrowUp, Sparkles, ShieldAlert, Target, TrendingUp, ChevronRight } from 'lucide-react';
import Navbar from './Navbar';
import ScaledDashboard from './ScaledDashboard';
import DashboardMockup from './DashboardMockup';

export default function Hero() {
  const bgImageUrl = 'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260611_133301_d5f2a94a-b22e-4e4a-a6b6-eacdddf1f5b0.png&w=1280&q=85';

  const handleSubmit = (e) => {
    e.preventDefault();
    window.location.href = '/signup/';
  };

  return (
    <div 
      className="relative min-h-[100svh] overflow-hidden bg-cover bg-center flex flex-col justify-between"
      style={{ backgroundImage: `url(${bgImageUrl})` }}
    >
      {/* Navbar Header */}
      <Navbar />

      {/* Spacer */}
      <div className="flex-1 min-h-8 sm:min-h-12 lg:min-h-16 shrink-0" />

      {/* Main Content Area */}
      <div className="relative z-10 px-5 flex flex-col items-center text-center max-w-4xl mx-auto w-full">
        {/* Eyebrow */}
        <span className="block text-xs sm:text-[13px] font-extrabold uppercase tracking-wider text-blue-600 mb-3 animate-fade-up">
          AI-Powered Competitive Intelligence
        </span>

        {/* Headline */}
        <h1 className="text-slate-900 font-normal leading-[1.05] tracking-tight text-[40px] min-[400px]:text-[44px] sm:text-6xl lg:text-7xl xl:text-[80px]">
          <span className="block animate-fade-up">Know your competitors</span>
          <span className="block font-serif italic text-slate-500 animate-fade-up [animation-delay:100ms]">better than they do.</span>
        </h1>

        {/* Supporting Description */}
        <p className="animate-fade-up [animation-delay:220ms] mt-6 sm:mt-8 text-slate-600 text-sm sm:text-base lg:text-lg leading-relaxed max-w-2xl mx-auto">
          Drop in any competitor's URL. Our system scrapes, structures, and generates an objective boardroom-ready strategy report in 60 seconds.
        </p>

        {/* Primary/Secondary Call-to-Actions */}
        <div className="animate-fade-up [animation-delay:340ms] mt-8 sm:mt-10 flex flex-wrap items-center justify-center gap-4">
          <a 
            href="/signup/" 
            className="bg-gray-900 text-white text-sm font-semibold px-7 py-3 rounded-full hover:bg-gray-800 hover:shadow-lg transition-all hover:scale-[1.02] text-center"
          >
            Get started
          </a>
          <a 
            href="/dashboard/" 
            className="bg-transparent text-slate-800 text-sm font-semibold px-7 py-3 rounded-full ring-1 ring-slate-300 hover:bg-white/50 hover:ring-slate-400 transition-colors text-center"
          >
            Book a demo
          </a>
        </div>
      </div>

      {/* Floating Card 1: Competitor Discovery (Left) */}
      <div className="hidden xl:block absolute top-32 left-8 lg:left-12 xl:left-24 w-60 p-4 bg-white border border-slate-200/60 rounded-2xl shadow-[0_15px_30px_rgba(0,0,0,0.06)] animate-float-1 select-none pointer-events-none opacity-95">
        <div className="flex items-center gap-2 mb-3.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs">Ae</div>
          <div>
            <div className="text-[10px] font-bold text-slate-900">nike.com</div>
            <div className="text-[8px] font-bold uppercase tracking-wider text-red-500 mt-0.5">Direct threat</div>
          </div>
        </div>
        <div className="space-y-1.5 text-[9px] text-slate-500 font-medium">
          <div className="flex justify-between">
            <span>Discovered</span>
            <span className="text-slate-800">Just now</span>
          </div>
          <div className="flex justify-between">
            <span>Threat level</span>
            <span className="text-red-500 font-bold">HIGH</span>
          </div>
        </div>
      </div>

      {/* Floating Card 2: Market Intelligence (Right) */}
      <div className="hidden xl:block absolute bottom-72 right-8 lg:right-12 xl:right-24 w-60 p-4 bg-white border border-slate-200/60 rounded-2xl shadow-[0_15px_30px_rgba(0,0,0,0.06)] animate-float-2 select-none pointer-events-none opacity-95">
        <div className="flex items-center justify-between text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-2">
          <span>Market Intelligence</span>
          <Target className="w-3.5 h-3.5 text-blue-500" />
        </div>
        <div className="text-slate-900 font-extrabold text-base mb-1.5">
          48% <span className="text-[10px] font-bold text-emerald-500 ml-1">↑ 12% growth</span>
        </div>
        <div className="space-y-1.5 text-[9px] text-slate-500 font-medium pt-2 border-t border-slate-100">
          <div className="flex justify-between">
            <span>Positioning</span>
            <span className="text-slate-800 font-semibold">Strong</span>
          </div>
          <div className="flex justify-between">
            <span>Threat Level</span>
            <span className="text-slate-800">3 / 10</span>
          </div>
        </div>
      </div>

      {/* Floating Card 3: AI Strategy (Left Bottom) */}
      <div className="hidden xl:block absolute bottom-24 left-8 lg:left-12 xl:left-24 w-64 p-4 bg-white border border-slate-200/60 rounded-2xl shadow-[0_15px_30px_rgba(0,0,0,0.06)] animate-float-3 select-none pointer-events-none opacity-95">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-6 h-6 rounded-full bg-blue-50 flex items-center justify-center">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          </div>
          <span className="text-[10px] font-extrabold text-slate-800 uppercase tracking-wider">AI Strategy</span>
        </div>
        <div className="text-[10px] font-medium text-slate-700 leading-relaxed mb-3">
          Pricing opportunity detected in European markets.
        </div>
        <div className="text-[9px] font-extrabold text-blue-600 flex items-center gap-1">
          View recommendation <ChevronRight size={12} />
        </div>
      </div>

      {/* Spacer */}
      <div className="flex-1 min-h-10 sm:min-h-12 lg:min-h-16 shrink-0" />

      {/* Dashboard Preview Section */}
      <div className="animate-hero-rise [animation-delay:620ms] relative z-0 w-[92%] sm:w-[84%] lg:w-[72%] max-w-4xl mx-auto shrink-0 -mb-10 sm:-mb-20 lg:-mb-32">
        <ScaledDashboard>
          <DashboardMockup />
        </ScaledDashboard>
      </div>

    </div>
  );
}
