import { useState } from 'react';
import { Bot, X, Send } from 'lucide-react';

export default function AIAgentModal({ isOpen, onClose }) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    { role: 'agent', content: 'Hello! I am your Intelligence Agent. I can help you analyze competitors, summarize market changes, or formulate strategic recommendations.' }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  if (!isOpen) return null;

  const handleSend = () => {
    if (!query.trim()) return;
    
    setMessages([...messages, { role: 'user', content: query }]);
    const currentQuery = query;
    setQuery('');
    setIsTyping(true);

    // Mock AI response
    setTimeout(() => {
      let response = "Based on the latest intelligence, this is an area we should monitor closely. I recommend reviewing our pricing strategy in response.";
      if (currentQuery.toLowerCase().includes('stripe') || currentQuery.toLowerCase().includes('competitor a')) {
        response = "Stripe has recently launched a lower-priced enterprise plan. This could create pricing pressure in our enterprise segment. I recommend we emphasize our premium features and consider a targeted campaign for dissatisfied customers.";
      }
      setMessages(prev => [...prev, { role: 'agent', content: response }]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/20 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md h-full bg-white dark:bg-slate-900 shadow-2xl flex flex-col border-l border-slate-200 dark:border-slate-800 transform transition-transform translate-x-0">
        
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-blue-50/50 dark:bg-blue-900/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center">
              <Bot size={18} />
            </div>
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white leading-tight">Intelligence Agent</h2>
              <p className="text-xs text-blue-600 dark:text-blue-400 font-medium">Online</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-950/50">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl p-4 text-sm shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-sm' 
                  : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 rounded-tl-sm'
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          {isTyping && (
             <div className="flex justify-start">
               <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl rounded-tl-sm p-4 shadow-sm flex gap-1">
                 <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                 <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                 <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
               </div>
             </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <div className="relative">
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about competitors, trends..."
              className="w-full bg-slate-100 dark:bg-slate-800 border-none rounded-xl py-3 pl-4 pr-12 text-sm focus:ring-2 focus:ring-blue-500 outline-none dark:text-white placeholder:text-slate-500"
            />
            <button 
              onClick={handleSend}
              className="absolute right-2 top-1.5 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Send size={16} />
            </button>
          </div>
          <div className="mt-3 flex gap-2 overflow-x-auto pb-1 no-scrollbar">
            {["Compare pricing", "What changed recently?", "Threat analysis"].map(s => (
              <button 
                key={s} 
                onClick={() => setQuery(s)}
                className="whitespace-nowrap px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-300 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
