import React from 'react';
import { 
  PanelLeft, ChevronLeft, ChevronRight, RotateCw, Share, Plus, Copy,
  Bot, Users, Target, Rss, LayoutDashboard, Settings, LogOut, CheckSquare,
  ShieldAlert, Zap, Monitor, Activity, TrendingUp, Clock
} from 'lucide-react';
import Logo from './Logo';

export default function DashboardMockup() {
  return (
    <div className="rounded-t-2xl overflow-hidden bg-[#0c1322] shadow-[0_-20px_80px_rgba(0,0,0,0.35)] ring-1 ring-white/10 text-left font-sans text-white pb-6 w-full select-none">
      {/* Title Bar / Browser Chrome */}
      <div className="bg-[#172033] border-b border-white/5 px-4 py-2.5 flex items-center justify-between">
        {/* Left: Traffic Lights & Navigation */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
          </div>
          <div className="flex items-center gap-1.5 ml-2">
            <PanelLeft className="w-3.5 h-3.5 text-white/40" />
            <ChevronLeft className="w-3.5 h-3.5 text-white/40" />
            <ChevronRight className="w-3.5 h-3.5 text-white/25" />
          </div>
        </div>

        {/* Center: URL bar */}
        <div className="flex-1 max-w-[280px] mx-auto flex items-center justify-center gap-1.5 bg-[#090d16] rounded-md px-6 py-1 text-[10px] text-white/60">
          <Monitor className="w-3 h-3 text-white/40" />
          <span>aetheris.ai/dashboard</span>
        </div>

        {/* Right: Chrome Controls */}
        <div className="flex items-center gap-3 text-white/40">
          <RotateCw className="w-3.5 h-3.5" />
          <Share className="w-3.5 h-3.5" />
          <Plus className="w-3.5 h-3.5" />
          <Copy className="w-3.5 h-3.5" />
        </div>
      </div>

      <div className="flex min-h-[460px]">
        {/* Sidebar */}
        <aside className="w-[24%] shrink-0 border-r border-white/5 bg-[#0e1726] px-3 py-3.5 flex flex-col gap-4">
          {/* Logo Header */}
          <div className="flex items-center gap-2 px-2 text-white font-bold text-sm">
            <Logo className="w-6 h-6" />
            <span className="text-[11px] font-bold tracking-tight">Aetheris</span>
          </div>

          {/* Ask Agent Button */}
          <div className="px-1.5">
            <button className="w-full flex items-center justify-between gap-2 px-3 py-2 bg-white text-slate-900 shadow rounded-lg font-medium text-[10px] hover:bg-slate-100 transition-colors">
              <span className="flex items-center gap-1.5">
                <Bot size={13} className="text-blue-600" />
                Ask Agent
              </span>
              <ChevronRight size={11} className="opacity-50" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-col gap-1 px-1">
            <a href="#" className="flex items-center justify-between px-2.5 py-1.5 rounded bg-blue-600/10 text-[10px] text-blue-400 font-medium">
              <span className="flex items-center gap-2">
                <LayoutDashboard className="w-3.5 h-3.5 text-blue-400" />
                Overview
              </span>
              <ChevronRight size={11} className="opacity-40" />
            </a>
            <a href="#" className="flex items-center justify-between px-2.5 py-1.5 rounded text-[10px] text-white/60 font-medium hover:bg-white/[0.02]">
              <span className="flex items-center gap-2">
                <Users className="w-3.5 h-3.5 text-white/30" />
                Competitors
              </span>
            </a>
            <a href="#" className="flex items-center justify-between px-2.5 py-1.5 rounded text-[10px] text-white/60 font-medium hover:bg-white/[0.02]">
              <span className="flex items-center gap-2">
                <Rss className="w-3.5 h-3.5 text-white/30" />
                Market Intelligence
              </span>
            </a>
            <a href="#" className="flex items-center justify-between px-2.5 py-1.5 rounded text-[10px] text-white/60 font-medium hover:bg-white/[0.02]">
              <span className="flex items-center gap-2">
                <CheckSquare className="w-3.5 h-3.5 text-white/30" />
                Action Center
              </span>
            </a>
            <a href="#" className="flex items-center justify-between px-2.5 py-1.5 rounded text-[10px] text-white/60 font-medium hover:bg-white/[0.02]">
              <span className="flex items-center gap-2">
                <Target className="w-3.5 h-3.5 text-white/30" />
                AI Strategy
              </span>
            </a>
          </nav>

          {/* Settings / Log Out (sticky at bottom) */}
          <div className="mt-auto flex flex-col gap-1 px-1 pt-4 border-t border-white/5">
            <a href="#" className="flex items-center gap-2 px-2.5 py-1.5 rounded text-[9px] text-white/50 font-medium hover:bg-white/[0.02]">
              <Settings className="w-3.5 h-3.5" />
              Settings
            </a>
            <a href="#" className="flex items-center gap-2 px-2.5 py-1.5 rounded text-[9px] text-white/50 font-medium hover:bg-white/[0.02]">
              <LogOut className="w-3.5 h-3.5" />
              Log out
            </a>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 px-6 py-5 space-y-5 flex flex-col justify-between">
          <div>
            {/* Header / Brand block */}
            <div className="flex items-start justify-between">
              <div>
                <div className="text-[9px] font-bold uppercase tracking-wider text-blue-400">
                  Market Baseline & Intelligence
                </div>
                <h2 className="text-base font-extrabold text-white mt-0.5">
                  nike.com <span className="font-normal text-slate-400">Competitive Intelligence</span>
                </h2>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Real-time market surveillance
                </p>
              </div>

              <div className="flex items-center gap-1 text-[9px] text-slate-400 bg-white/[0.03] border border-white/5 px-2 py-1 rounded">
                <Clock size={11} />
                <span>Last checked: 8/15/2026</span>
              </div>
            </div>

            {/* KPI Cards Grid */}
            <div className="grid grid-cols-4 gap-3 mt-4">
              {/* Total Discovered */}
              <div className="rounded-xl p-3.5 bg-white/[0.02] border border-white/5">
                <div className="flex items-center justify-between text-[9px] font-bold text-slate-400 uppercase">
                  <span>Total Discovered</span>
                  <Users className="w-3.5 h-3.5 text-slate-500" />
                </div>
                <div className="text-lg font-black text-white mt-1">62</div>
                <div className="text-[8px] text-slate-500 mt-0.5">Discovered by AI</div>
              </div>

              {/* Direct Competitors */}
              <div className="rounded-xl p-3.5 bg-white/[0.02] border border-red-900/30">
                <div className="flex items-center justify-between text-[9px] font-bold text-red-400 uppercase">
                  <span>Direct threats</span>
                  <ShieldAlert className="w-3.5 h-3.5 text-red-500" />
                </div>
                <div className="text-lg font-black text-red-400 mt-1">12</div>
                <div className="text-[8px] text-red-500/80 mt-0.5">Primary threats</div>
              </div>

              {/* Indirect Competitors */}
              <div className="rounded-xl p-3.5 bg-white/[0.02] border border-amber-900/30">
                <div className="flex items-center justify-between text-[9px] font-bold text-amber-500 uppercase">
                  <span>Indirect competitors</span>
                  <Target className="w-3.5 h-3.5 text-amber-500" />
                </div>
                <div className="text-lg font-black text-amber-500 mt-1">412</div>
                <div className="text-[8px] text-amber-500/80 mt-0.5">Substitutes & adjacent</div>
              </div>

              {/* Emerging Threats */}
              <div className="rounded-xl p-3.5 bg-white/[0.02] border border-blue-900/30">
                <div className="flex items-center justify-between text-[9px] font-bold text-blue-400 uppercase">
                  <span>Emerging threats</span>
                  <Zap className="w-3.5 h-3.5 text-blue-500" />
                </div>
                <div className="text-lg font-black text-blue-400 mt-1">3</div>
                <div className="text-[8px] text-blue-500/80 mt-0.5">Fast-growing startups</div>
              </div>
            </div>
          </div>

          {/* Action Items Card */}
          <div className="rounded-xl p-4 bg-white/[0.02] border border-white/5 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-blue-600/10 flex items-center justify-center">
                <CheckSquare className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h3 className="font-bold text-white text-xs">Action Items</h3>
                <div className="flex items-center gap-3 text-[10px] mt-0.5 text-slate-400">
                  <span>Total active: 5</span>
                  <span className="font-bold text-red-400">Critical: 2</span>
                  <span className="font-bold text-red-400">Overdue: 1</span>
                </div>
              </div>
            </div>
            <ChevronRight className="text-slate-500 w-4 h-4" />
          </div>

          {/* Executive Brief Card */}
          <div className="rounded-xl p-4 bg-white/[0.02] border border-blue-900/30 space-y-2 mt-auto">
            <div className="flex items-center gap-2 text-blue-400 font-extrabold text-xs">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
              Executive Brief
            </div>
            <p className="text-slate-200 text-[10px] leading-relaxed font-medium">
              Nike's digital footprint is heavily anchored in emotional brand storytelling. Distill pricing models and supply chain bottlenecks to capture DTC markets.
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
