import { Building2, Users, Rss } from 'lucide-react';

const TABS = [
  { id: 'mycompany',   label: 'My Company',  icon: Building2, num: '01' },
  { id: 'competitors', label: 'Competitors', icon: Users,     num: '02' },
  { id: 'unifeed',     label: 'UniFeed',     icon: Rss,       num: '03' },
];

export default function DashboardNav({ active, onChange }) {
  return (
    <nav className="sticky top-[65px] z-30 bg-white dark:bg-black border-b-4 border-black dark:border-white">
      <div className="max-w-6xl mx-auto px-6 flex items-stretch gap-0">
        {TABS.map((tab) => {
          const isActive = active === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`
                relative flex items-center gap-2 px-6 py-4 font-heading text-xs font-black uppercase tracking-widest
                transition-all duration-150 border-r-2 border-black dark:border-white last:border-r-0
                ${isActive
                  ? 'bg-black text-white dark:bg-white dark:text-black'
                  : 'bg-white text-black dark:bg-black dark:text-white hover:bg-accent hover:text-white dark:hover:bg-accent dark:hover:text-white'
                }
              `}
            >
              <span className="font-mono text-[9px] opacity-50">{tab.num}</span>
              <tab.icon size={13} strokeWidth={3} />
              <span className="hidden sm:inline">{tab.label}</span>
              {isActive && (
                <span className="absolute bottom-0 left-0 right-0 h-[3px] bg-accent" />
              )}
            </button>
          );
        })}

        {/* Filler */}
        <div className="flex-1 border-l-2 border-black dark:border-white" />

        {/* Live badge */}
        <div className="flex items-center gap-2 px-4">
          <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          <span className="font-mono text-[9px] uppercase tracking-widest text-slate-500 dark:text-slate-400 hidden md:block">
            LIVE SESSION
          </span>
        </div>
      </div>
    </nav>
  );
}
