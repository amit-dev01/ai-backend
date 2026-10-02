import { useState, useEffect, useContext } from 'react';
import { DbContext } from '../App';
import { 
  CheckSquare, Loader2, Plus, LayoutList, LayoutGrid, Clock, 
  AlertCircle, ExternalLink, Bot, User, X, ChevronDown, Trash2
} from 'lucide-react';
import { 
  getTasks, createTask, updateTask, updateTaskStatus, 
  getJiraLink, deleteTask
} from '../api';

const PRIORITY_COLORS = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-orange-500',
  MEDIUM: 'bg-yellow-500',
  LOW: 'bg-slate-400 dark:bg-slate-500'
};

const CATEGORIES = {
  RESPOND_TO_COMPETITOR: { label: 'Respond', color: 'bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-800' },
  MONITOR_SITUATION: { label: 'Monitor', color: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800' },
  UPDATE_STRATEGY: { label: 'Strategy', color: 'bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800' },
  RESEARCH_FURTHER: { label: 'Research', color: 'bg-indigo-100 text-indigo-700 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800' },
  PRICING_RESPONSE: { label: 'Pricing', color: 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800' },
  PRODUCT_RESPONSE: { label: 'Product', color: 'bg-cyan-100 text-cyan-700 border-cyan-200 dark:bg-cyan-900/30 dark:text-cyan-300 dark:border-cyan-800' },
  INTERNAL_ACTION: { label: 'Internal', color: 'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800' },
  CUSTOM: { label: 'Custom', color: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700' }
};

const getRelativeDateStr = (dateString) => {
  if (!dateString) return null;
  const due = new Date(dateString);
  const now = new Date();
  const diffTime = due - now;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
  
  if (diffDays < 0) return `Overdue · was due ${Math.abs(diffDays)} day${Math.abs(diffDays) === 1 ? '' : 's'} ago`;
  if (diffDays === 0) return 'Due today';
  if (diffDays === 1) return 'Due tomorrow';
  if (diffDays <= 3) return `Due in ${diffDays} days`;
  return due.toLocaleDateString();
};

const isOverdue = (dateString, status) => {
  if (!dateString || status === 'DONE' || status === 'DISMISSED') return false;
  return new Date(dateString) < new Date();
};

const STATUS_MAP = {
  'TODO': 'To Do',
  'IN_PROGRESS': 'In Progress',
  'DONE': 'Done',
  'DISMISSED': 'Dismissed'
};

export default function ActionCenterSection() {
  const { showToast, acceptedCompetitors, setActiveSection, lastFetchedAt } = useContext(DbContext);
  
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'board'
  
  const [filters, setFilters] = useState({
    status: 'All Active',
    priority: 'All Priorities',
    source: 'All',
    competitor: 'All Competitors'
  });

  const [stats, setStats] = useState({
    todo: 0, inProgress: 0, completedThisWeek: 0, generatedThisWeek: 0
  });

  const [selectedTask, setSelectedTask] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const fetchTasksData = async () => {
    setLoading(true);
    try {
      const data = await getTasks(filters);
      const list = Array.isArray(data) ? data : data.tasks || [];
      
      // Calculate derived stats just from the fetched active list?
      // Actually we have `/api/tasks/stats` for real stats, but we can just use length if needed.
      // Wait, the API should return what we need. If not, we just show what we have.
      setTasks(list);
      
      // We can compute stats from context or if returned in this payload:
      if (data.stats) {
        setStats(data.stats);
      } else {
        const todo = list.filter(t => t.status === 'TODO').length;
        const inProgress = list.filter(t => t.status === 'IN_PROGRESS').length;
        // Approximation if backend doesn't send:
        setStats(prev => ({ ...prev, todo, inProgress }));
      }
    } catch (err) {
      showToast('Failed to load tasks', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasksData();
    // eslint-disable-next-line
  }, [filters, lastFetchedAt]);

  const handleStatusChange = async (taskId, newStatus) => {
    const previousTasks = [...tasks];
    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: newStatus } : t));
    
    if (selectedTask && selectedTask.id === taskId) {
      setSelectedTask(prev => ({ ...prev, status: newStatus }));
    }

    try {
      await updateTaskStatus(taskId, newStatus);
      showToast('Task updated', 'success');
      // If we filtered out the task by status, maybe it disappears (expected)
      // fetchTasksData(); // optional refetch
    } catch (err) {
      setTasks(previousTasks);
      if (selectedTask && selectedTask.id === taskId) {
        setSelectedTask(previousTasks.find(t => t.id === taskId));
      }
      showToast('Failed to update task', 'error');
    }
  };

  const handleJiraLink = async (taskId) => {
    try {
      showToast('Generating Jira link...', 'success');
      const res = await getJiraLink(taskId);
      if (res && res.jiraUrl) {
        window.open(res.jiraUrl, '_blank', 'noopener,noreferrer');
      } else {
        throw new Error('No URL returned');
      }
    } catch (err) {
      if (err.status === 400 || err.message?.includes('configured') || err.message?.includes('domain')) {
        showToast('Please configure your Jira domain in Settings first', 'error');
        // Optional: route to settings
        // setActiveSection('settings');
      } else {
        showToast('Failed to generate Jira link', 'error');
      }
    }
  };

  const StatusDropdown = ({ task }) => (
    <div className="relative group inline-block">
      <select 
        value={task.status} 
        onChange={(e) => handleStatusChange(task.id, e.target.value)}
        onClick={(e) => e.stopPropagation()}
        className={`appearance-none outline-none cursor-pointer pl-3 pr-8 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
          task.status === 'TODO' ? 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300' :
          task.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/40 dark:text-blue-400' :
          task.status === 'DONE' ? 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-400' :
          'bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-800 dark:text-slate-500'
        }`}
      >
        <option value="TODO">To Do</option>
        <option value="IN_PROGRESS">In Progress</option>
        <option value="DONE">Done</option>
        <option value="DISMISSED">Dismiss</option>
      </select>
      <ChevronDown size={14} className="absolute right-2.5 top-2 pointer-events-none opacity-50" />
    </div>
  );

  return (
    <div className="animate-fade-in-up max-w-6xl mx-auto space-y-6 relative pb-12">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
            <CheckSquare className="w-8 h-8 text-blue-600" />
            Action Center
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            AI generated action items from your competitive intelligence
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl mr-2">
            <button 
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-white dark:bg-slate-700 shadow-sm text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
            >
              <LayoutList size={18} />
            </button>
            <button 
              onClick={() => setViewMode('board')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'board' ? 'bg-white dark:bg-slate-700 shadow-sm text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
            >
              <LayoutGrid size={18} />
            </button>
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-sm"
          >
            <Plus size={16} /> Add Task
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex flex-wrap gap-3">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-slate-400"></div>
          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Open: <strong className="text-slate-900 dark:text-white">{stats.todo}</strong> tasks</span>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-blue-500"></div>
          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">In Progress: <strong className="text-slate-900 dark:text-white">{stats.inProgress}</strong> tasks</span>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Done this week: <strong className="text-slate-900 dark:text-white">{stats.completedThisWeek || 0}</strong> tasks</span>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-purple-500"></div>
          <span className="text-sm font-medium text-slate-600 dark:text-slate-400">AI Generated this week: <strong className="text-slate-900 dark:text-white">{stats.generatedThisWeek || 0}</strong> tasks</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm overflow-x-auto">
        <div className="flex items-center gap-1">
          {['All Active', 'To Do', 'In Progress', 'Done', 'Dismissed'].map(s => (
            <button 
              key={s}
              onClick={() => setFilters(prev => ({ ...prev, status: s }))}
              className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors whitespace-nowrap ${filters.status === s ? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
            >
              {s}
            </button>
          ))}
        </div>
        
        <div className="flex items-center gap-3">
          <select 
            value={filters.priority}
            onChange={e => setFilters(prev => ({ ...prev, priority: e.target.value }))}
            className="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-700 dark:text-slate-300 outline-none"
          >
            <option>All Priorities</option>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
          <select 
            value={filters.source}
            onChange={e => setFilters(prev => ({ ...prev, source: e.target.value }))}
            className="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-700 dark:text-slate-300 outline-none"
          >
            <option>All</option>
            <option>AI Generated</option>
            <option>Manual</option>
          </select>
          <select 
            value={filters.competitor}
            onChange={e => setFilters(prev => ({ ...prev, competitor: e.target.value }))}
            className="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-700 dark:text-slate-300 outline-none max-w-[150px] truncate"
          >
            <option>All Competitors</option>
            {acceptedCompetitors.map(c => (
              <option key={c.id || c.name} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : tasks.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-4 shadow-sm">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
            <CheckSquare size={32} />
          </div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-white">
            {filters.status === 'All Active' ? 'No open action items' : 
             filters.status === 'Done' ? 'No completed tasks yet' :
             filters.status === 'Dismissed' ? 'No dismissed tasks' :
             'No tasks match your filters'}
          </h3>
          {filters.status === 'All Active' && (
            <>
              <p className="text-slate-500 dark:text-slate-400 max-w-md">
                AI will generate tasks automatically when significant competitive events are detected. Run a check to get started.
              </p>
              <button 
                onClick={() => setActiveSection('overview')}
                className="mt-2 px-5 py-2.5 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors"
              >
                Go to Overview
              </button>
            </>
          )}
        </div>
      ) : viewMode === 'list' ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
          <div className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {tasks.map(task => {
              const cat = CATEGORIES[task.category] || CATEGORIES.CUSTOM;
              const overdue = isOverdue(task.dueDate, task.status);
              
              return (
                <div 
                  key={task.id} 
                  className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors flex items-center gap-4 group cursor-pointer"
                  onClick={() => setSelectedTask(task)}
                >
                  <div className="flex items-center justify-center shrink-0 w-8">
                    <div className={`w-3 h-3 rounded-full shadow-sm ${PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.LOW}`} title={task.priority}></div>
                  </div>
                  
                  <div className="flex-1 min-w-0 flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                    <div className="flex-1 truncate">
                      <div className="font-bold text-slate-900 dark:text-white truncate">
                        {task.title}
                      </div>
                      <div className="flex items-center gap-3 mt-1.5 text-xs">
                        {task.competitorName && (
                          <span className="font-medium text-slate-600 dark:text-slate-400 border dark:border-slate-700 px-2 py-0.5 rounded-md">
                            {task.competitorName}
                          </span>
                        )}
                        <span className={`px-2 py-0.5 rounded-md font-bold uppercase tracking-wider border ${cat.color} text-[10px]`}>
                          {cat.label}
                        </span>
                        <div className="flex items-center text-slate-400">
                          {task.source === 'AI_GENERATED' ? <Bot size={12} className="mr-1" /> : <User size={12} className="mr-1" />}
                          {task.source === 'AI_GENERATED' ? 'AI' : 'Manual'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 md:w-64 shrink-0">
                      <div className={`flex items-center gap-1.5 text-xs font-semibold ${overdue ? 'text-red-500' : 'text-slate-500 dark:text-slate-400'}`}>
                        {task.dueDate && <Clock size={12} />}
                        {getRelativeDateStr(task.dueDate)}
                        {overdue && <AlertCircle size={12} className="ml-0.5" />}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 shrink-0">
                    <StatusDropdown task={task} />
                    
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleJiraLink(task.id); }}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-blue-600 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 dark:text-blue-400 transition-colors"
                    >
                      Jira <ExternalLink size={12} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Board View */
        <div className="flex gap-6 overflow-x-auto pb-4 h-[70vh]">
          {['TODO', 'IN_PROGRESS', 'DONE'].map(colStatus => {
            const colTasks = tasks.filter(t => t.status === colStatus);
            return (
              <div key={colStatus} className="flex-shrink-0 w-80 flex flex-col bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-slate-800">
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                  <h3 className="font-bold text-slate-900 dark:text-white">
                    {STATUS_MAP[colStatus]}
                  </h3>
                  <span className="text-xs font-black text-slate-500 bg-slate-200 dark:bg-slate-800 px-2.5 py-1 rounded-full">
                    {colTasks.length}
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-3">
                  {colTasks.map(task => {
                    const cat = CATEGORIES[task.category] || CATEGORIES.CUSTOM;
                    const overdue = isOverdue(task.dueDate, task.status);
                    return (
                      <div 
                        key={task.id}
                        onClick={() => setSelectedTask(task)}
                        className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4 shadow-sm cursor-pointer hover:border-blue-400 transition-colors group relative"
                      >
                        <div className={`absolute top-4 right-4 w-2.5 h-2.5 rounded-full ${PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.LOW}`} title={task.priority}></div>
                        
                        <div className="font-bold text-slate-900 dark:text-white pr-6 text-sm mb-1 leading-snug">
                          {task.title}
                        </div>
                        {task.competitorName && (
                          <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-3">
                            {task.competitorName}
                          </div>
                        )}
                        
                        <div className="flex items-center justify-between mt-4">
                          <span className={`px-2 py-0.5 rounded-md font-bold uppercase tracking-wider border ${cat.color} text-[9px]`}>
                            {cat.label}
                          </span>
                          
                          <div className="flex items-center gap-2">
                            {task.dueDate && (
                              <div className={`text-[10px] font-semibold flex items-center gap-1 ${overdue ? 'text-red-500' : 'text-slate-400'}`}>
                                <Clock size={10} /> {new Date(task.dueDate).toLocaleDateString(undefined, {month:'short', day:'numeric'})}
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700 flex justify-between items-center" onClick={e => e.stopPropagation()}>
                          <StatusDropdown task={task} />
                          <button 
                            onClick={(e) => { e.stopPropagation(); handleJiraLink(task.id); }}
                            className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                          >
                            Jira <ExternalLink size={10} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* View Dismissed link if Board */}
      {viewMode === 'board' && (
        <div className="text-center pt-2">
          <button 
            onClick={() => { setViewMode('list'); setFilters(prev => ({...prev, status: 'Dismissed'})); }}
            className="text-sm font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-300 underline"
          >
            View dismissed tasks
          </button>
        </div>
      )}

      {/* Modals placeholders - to be implemented next */}
      {selectedTask && (
        <TaskDetailModal 
          task={selectedTask} 
          onClose={() => setSelectedTask(null)}
          onStatusChange={handleStatusChange}
          onJiraLink={() => handleJiraLink(selectedTask.id)}
          refresh={fetchTasksData}
        />
      )}

      {showCreateModal && (
        <CreateTaskModal 
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => { setShowCreateModal(false); fetchTasksData(); }}
          acceptedCompetitors={acceptedCompetitors}
        />
      )}

    </div>
  );
}

// ── Modals ──

function TaskDetailModal({ task, onClose, onStatusChange, onJiraLink, refresh }) {
  const { showToast } = useContext(DbContext);
  const [dueDate, setDueDate] = useState(task.dueDate ? task.dueDate.split('T')[0] : '');
  const [jiraUrl, setJiraUrl] = useState(task.jiraIssueUrl || '');
  const [saving, setSaving] = useState(false);
  const [showDismissConfirm, setShowDismissConfirm] = useState(false);

  const handleUpdate = async (field, value) => {
    try {
      setSaving(true);
      await updateTask(task.id, { [field]: value });
      refresh();
    } catch (err) {
      showToast(`Failed to update ${field}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete this task?")) return;
    try {
      await deleteTask(task.id);
      showToast('Task deleted', 'success');
      onClose();
      refresh();
    } catch (err) {
      showToast('Failed to delete task', 'error');
    }
  };

  const cat = CATEGORIES[task.category] || CATEGORIES.CUSTOM;

  return (
    <div className="fixed inset-0 z-[100] flex justify-end bg-black/30 backdrop-blur-sm animate-fade-in" onClick={onClose}>
      <div className="w-full max-w-lg bg-white dark:bg-slate-900 h-full shadow-2xl flex flex-col border-l border-slate-200 dark:border-slate-800 animate-slide-in-right" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.LOW}`}></div>
            <select 
              value={task.status}
              onChange={(e) => onStatusChange(task.id, e.target.value)}
              className="bg-transparent font-bold text-sm outline-none cursor-pointer"
            >
              <option value="TODO">To Do</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="DONE">Done</option>
              <option value="DISMISSED">Dismissed</option>
            </select>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          <div>
            <h2 className="text-xl font-extrabold text-slate-900 dark:text-white leading-snug">
              {task.title}
            </h2>
            <div className="flex items-center gap-2 mt-3">
              {task.competitorName && (
                <span className="text-xs font-bold bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md text-slate-600 dark:text-slate-300">
                  {task.competitorName}
                </span>
              )}
              <span className={`px-2 py-1 rounded-md font-bold uppercase tracking-wider border ${cat.color} text-[10px]`}>
                {cat.label}
              </span>
            </div>
          </div>

          {task.description && (
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Context</label>
              <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                {task.description}
              </p>
            </div>
          )}

          {task.recommendedSteps && (
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Recommended Steps</label>
              <div className="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30 p-4 rounded-xl">
                <ul className="text-sm text-slate-700 dark:text-slate-300 space-y-2">
                  {task.recommendedSteps.split('\n').map((step, i) => {
                    const cleanStep = step.replace(/^-/, '').trim();
                    if (!cleanStep) return null;
                    return (
                      <li key={i} className="flex gap-2 items-start">
                        <span className="text-blue-500 mt-0.5">•</span>
                        <span>{cleanStep}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>
          )}

          {(task.sourceDocumentId || task.sourceTrendId || task.sourceAnomalyId) && (
            <div className="space-y-2 border-t border-slate-100 dark:border-slate-800 pt-6">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Bot size={14} /> Intelligence Source
              </label>
              <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                <p>Generated by AI analysis.</p>
                {/* Could add link to actual source document if we had it in full context */}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-6 border-t border-slate-100 dark:border-slate-800 pt-6">
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Due Date</label>
              <input 
                type="date"
                value={dueDate}
                onChange={e => {
                  setDueDate(e.target.value);
                  handleUpdate('dueDate', e.target.value ? new Date(e.target.value).toISOString() : null);
                }}
                className="w-full text-sm font-semibold bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-2 rounded-lg outline-none"
              />
            </div>
          </div>

          <div className="space-y-2 border-t border-slate-100 dark:border-slate-800 pt-6">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-400">Jira Issue</label>
            {jiraUrl ? (
              <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-2 rounded-lg">
                <a href={jiraUrl} target="_blank" rel="noreferrer" className="text-sm text-blue-600 font-semibold hover:underline">
                  Open in Jira ↗
                </a>
                <button onClick={() => {setJiraUrl(''); handleUpdate('jiraIssueUrl', null)}} className="text-slate-400 hover:text-red-500">
                  <X size={14} />
                </button>
              </div>
            ) : (
              <input 
                type="url"
                placeholder="Paste your Jira issue URL here..."
                value={jiraUrl}
                onChange={e => setJiraUrl(e.target.value)}
                onBlur={() => { if(jiraUrl) handleUpdate('jiraIssueUrl', jiraUrl) }}
                className="w-full text-sm font-medium bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 px-3 py-2 rounded-lg outline-none placeholder:text-slate-400"
              />
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 space-y-3">
          {showDismissConfirm ? (
            <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
              <p className="text-xs font-bold text-slate-700 dark:text-slate-300">Dismiss this task?</p>
              <div className="flex gap-2">
                <button 
                  onClick={() => { onStatusChange(task.id, 'DISMISSED'); setShowDismissConfirm(false); }}
                  className="flex-1 py-1.5 bg-slate-600 text-white text-xs font-bold rounded-lg"
                >
                  Dismiss
                </button>
                <button 
                  onClick={() => setShowDismissConfirm(false)}
                  className="flex-1 py-1.5 bg-white dark:bg-slate-700 text-slate-700 dark:text-white border border-slate-300 dark:border-slate-600 text-xs font-bold rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <button 
                onClick={onJiraLink}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition-colors flex justify-center items-center gap-2"
              >
                Create in Jira <ExternalLink size={16} />
              </button>
              
              <div className="flex gap-2">
                {task.status === 'TODO' && (
                  <button onClick={() => onStatusChange(task.id, 'IN_PROGRESS')} className="flex-1 py-2 bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-sm font-bold rounded-xl hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors">
                    Start Working
                  </button>
                )}
                {task.status === 'IN_PROGRESS' && (
                  <button onClick={() => onStatusChange(task.id, 'DONE')} className="flex-1 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold rounded-xl transition-colors">
                    Mark Done
                  </button>
                )}
                {(task.status === 'TODO' || task.status === 'IN_PROGRESS') && (
                  <button onClick={() => setShowDismissConfirm(true)} className="px-4 py-2 bg-slate-100 dark:bg-slate-800/50 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 text-sm font-bold rounded-xl transition-colors border border-slate-200 dark:border-slate-700">
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          )}

          {task.source === 'MANUAL' && (
            <div className="text-center pt-2">
              <button onClick={handleDelete} className="text-xs font-bold text-red-500 hover:underline flex items-center justify-center gap-1 w-full">
                <Trash2 size={12} /> Delete Task
              </button>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

function CreateTaskModal({ onClose, onSuccess, acceptedCompetitors }) {
  const { showToast } = useContext(DbContext);
  const [saving, setSaving] = useState(false);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    recommendedSteps: '',
    priority: 'MEDIUM',
    category: 'CUSTOM',
    competitorName: '',
    dueDate: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || formData.title.length < 2) {
      showToast('Title must be at least 2 characters', 'error');
      return;
    }
    
    try {
      setSaving(true);
      const payload = {
        ...formData,
        dueDate: formData.dueDate ? new Date(formData.dueDate).toISOString() : null,
        competitorName: formData.competitorName === 'None' ? null : formData.competitorName
      };
      
      await createTask(payload);
      showToast('Task created successfully', 'success');
      onSuccess();
    } catch (err) {
      showToast('Failed to create task', 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex justify-center items-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in" onClick={onClose}>
      <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]" onClick={e => e.stopPropagation()}>
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-900">
          <h2 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Plus size={20} className="text-blue-500" /> Create Task
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-5 flex-1">
          
          <div className="space-y-1.5">
            <label className="text-sm font-bold text-slate-700 dark:text-slate-300 flex justify-between">
              Title * <span className="text-slate-400 font-normal">{formData.title.length}/80</span>
            </label>
            <input 
              type="text"
              maxLength={80}
              required
              placeholder="What needs to be done?"
              value={formData.title}
              onChange={e => setFormData({...formData, title: e.target.value})}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Priority</label>
              <select 
                value={formData.priority}
                onChange={e => setFormData({...formData, priority: e.target.value})}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
            
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Category</label>
              <select 
                value={formData.category}
                onChange={e => setFormData({...formData, category: e.target.value})}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
              >
                {Object.entries(CATEGORIES).map(([key, val]) => (
                  <option key={key} value={key}>{val.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Description</label>
            <textarea 
              rows={3}
              placeholder="Add context about why this task is important..."
              value={formData.description}
              onChange={e => setFormData({...formData, description: e.target.value})}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Recommended Steps</label>
            <textarea 
              rows={3}
              placeholder="List the specific steps to take..."
              value={formData.recommendedSteps}
              onChange={e => setFormData({...formData, recommendedSteps: e.target.value})}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Competitor (Optional)</label>
              <select 
                value={formData.competitorName}
                onChange={e => setFormData({...formData, competitorName: e.target.value})}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="None">None</option>
                {acceptedCompetitors.map(c => (
                  <option key={c.id || c.name} value={c.name}>{c.name}</option>
                ))}
              </select>
            </div>
            
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Due Date</label>
              <input 
                type="date"
                value={formData.dueDate}
                onChange={e => setFormData({...formData, dueDate: e.target.value})}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

        </form>

        <div className="p-5 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex justify-end gap-3">
          <button 
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleSubmit}
            disabled={saving}
            className="px-5 py-2.5 font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-colors flex items-center gap-2 disabled:opacity-50 shadow-sm"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : null}
            Create Task
          </button>
        </div>
      </div>
    </div>
  );
}
