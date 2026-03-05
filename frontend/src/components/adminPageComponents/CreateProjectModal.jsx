import { useState } from 'react';
import { X, Minus, Plus, ArrowLeft } from 'lucide-react';
import { Spinner } from './UI';
import adminService from '../../service/Admin.service';

// Вспомогательный компонент для круговых диаграмм
const CircularProgress = ({ value, max, label, unit, color = "#4ade80" }) => {
  const radius = 18;
  const dashArray = 2 * Math.PI * radius;
  const dashOffset = dashArray - (dashArray * value) / max;

  return (
    <div className="flex items-center gap-3">
      <div className="relative w-10 h-10">
        <svg className="w-full h-full rotate-[-90deg]">
          <circle cx="20" cy="20" r={radius} fill="transparent" stroke="rgba(255,255,255,0.1)" strokeWidth="3" />
          <circle 
            cx="20" cy="20" r={radius} fill="transparent" stroke={color} strokeWidth="3" 
            strokeDasharray={dashArray} strokeDashoffset={dashOffset} strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
      </div>
      <div className="flex flex-col">
        <span className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">{label}</span>
        <span className="text-xs text-white font-bold">{value}/{max} {unit}</span>
      </div>
    </div>
  );
};

const CreateProjectModal = ({ userId, onClose, onCreated }) => {
  const [form, setForm] = useState({ name: '', cpu_quota: 8, ram_quota: 16, ssd_quota: 200 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateQuota = (key, delta, min = 1) => {
    setForm(prev => ({ ...prev, [key]: Math.max(min, prev[key] + delta) }));
  };

  const handleCreate = async () => {
    if (!form.name.trim()) return;
    setLoading(true); setError('');
    try {
      await adminService.addProject(userId, { ...form });
      onCreated();
      onClose();
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-4xl bg-[#050308] rounded-[32px] overflow-hidden border border-white/5 shadow-2xl">
        
        {/* Header */}
        <div className="flex justify-between items-center px-8 py-6">
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <ArrowLeft size={20} />
          </button>
          <h2 className="text-2xl font-bold text-white tracking-tight">Создание нового тенанта</h2>
          <div className="w-8" /> {/* Spacer */}
        </div>

        <div className="px-8 pb-8 flex flex-col gap-6">
          
          {/* Main Grid */}
          <div className="grid grid-cols-12 gap-6">
            
            {/* Left Column: Image & Basic Info */}
            <div className="col-span-3 space-y-6">
              <div className="aspect-square rounded-2xl bg-black border border-white/[0.05] flex items-center justify-center relative overflow-hidden group">
                <img src="/tor.png" alt="Tor" className="w-3/4 h-3/4 object-contain animate-pulse" />
                <div className="absolute inset-0 bg-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="text-[10px] text-slate-500 uppercase font-bold mb-2 block">Название тенанта</label>
                  <input 
                    placeholder="Введите название"
                    value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-4 py-2 text-sm text-white outline-none focus:border-purple-500/50"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 uppercase font-bold mb-2 block">ID клиента</label>
                  <div className="bg-white/[0.03] border border-white/10 rounded-lg px-4 py-2 text-[11px] text-slate-400 font-mono truncate">
                    {userId}
                  </div>
                </div>
              </div>
            </div>

            {/* Middle Column: Quota Controls */}
            <div className="col-span-5 bg-white/[0.02] border border-white/[0.05] rounded-3xl p-6 space-y-8">
              <h3 className="text-sm font-bold text-white">Квоты на ресурсы</h3>
              
              <div className="space-y-6">
                {[
                  { label: 'RAM (ГБ)', key: 'ram_quota', step: 4, max: 128 },
                  { label: 'CPU (Ядра)', key: 'cpu_quota', step: 1, max: 47 },
                ].map(q => (
                  <div key={q.key}>
                    <label className="text-[10px] text-slate-500 uppercase font-bold mb-2 block">{q.label} <span className="text-[8px] opacity-50 ml-1">(ОТ 1 ДО {q.max})</span></label>
                    <div className="flex items-center gap-4">
                      <button onClick={() => updateQuota(q.key, -q.step)} className="w-8 h-8 rounded-full bg-purple-600/20 text-purple-400 flex items-center justify-center hover:bg-purple-600/40 transition-colors"><Minus size={14}/></button>
                      <div className="flex-1 text-center text-xl font-bold text-white leading-none">{form[q.key]}</div>
                      <button onClick={() => updateQuota(q.key, q.step)} className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center hover:bg-slate-200 transition-colors"><Plus size={14}/></button>
                    </div>
                  </div>
                ))}

                <div>
                  <label className="text-[10px] text-slate-500 uppercase font-bold mb-2 block">Размер Диска (ГБ) <span className="text-[8px] opacity-50 ml-1">(ОТ 3 ДО 1536)</span></label>
                  <div className="flex gap-2">
                    <div className="flex-1 bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2 flex items-center justify-between">
                       <button onClick={() => updateQuota('ssd_quota', -10, 3)} className="text-purple-400"><Minus size={14}/></button>
                       <span className="text-lg font-bold text-white">{form.ssd_quota}</span>
                       <button onClick={() => updateQuota('ssd_quota', 10)} className="text-white"><Plus size={14}/></button>
                    </div>
                    <div className="w-24 bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2 flex items-center justify-center text-slate-300 font-bold text-sm uppercase">SSD</div>
                  </div>
                </div>
              </div>
              <button className="w-full py-3 rounded-xl border border-white/10 text-slate-400 text-xs font-bold uppercase tracking-widest hover:bg-white/5 transition-colors">Добавить диск</button>
            </div>

            {/* Right Column: Visualization */}
            <div className="col-span-4 flex flex-col justify-between py-2 pl-4">
              <div className="flex justify-between items-center">
                 <span className="text-xs text-slate-400 font-medium">Статус</span>
                 <div className="px-4 py-1.5 rounded-lg bg-white/5 border border-white/10 text-[10px] font-bold text-green-400 uppercase tracking-widest">Активен</div>
              </div>

              <div className="space-y-6">
                <CircularProgress label="RAM использовано (ГБ)" value={form.ram_quota} max={128} unit="" color="#c084fc" />
                <CircularProgress label="CPU использовано (vCPU)" value={form.cpu_quota} max={47} unit="" color="#4ade80" />
                <CircularProgress label="SSD использовано (ГБ)" value={form.ssd_quota} max={1536} unit="" color="#f87171" />
              </div>
            </div>
          </div>

          {/* Bottom Banner */}
          <div className="bg-gradient-to-r from-[#201040] to-[#0d0920] rounded-[24px] p-6 border border-white/5 flex items-center justify-between relative overflow-hidden group">
            <div className="flex gap-12 relative z-10">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded border border-white/20 bg-purple-500/20" />
                <span className="text-xs text-slate-300 font-medium">Выделен пользователю</span>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Дата создания</p>
                <div className="bg-white/5 border border-white/10 rounded-lg px-4 py-1 text-xs text-white">02.03.2026</div>
              </div>
              <div className="flex gap-8">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Текущее кол-во тенантов</p>
                  <div className="bg-white/5 border border-white/10 rounded-lg px-4 py-1 text-xs text-white w-20 text-center">100</div>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Текущее кол-во пользователей</p>
                  <div className="bg-white/5 border border-white/10 rounded-lg px-4 py-1 text-xs text-white w-20 text-center">70</div>
                </div>
              </div>
            </div>
            
            <button 
              onClick={handleCreate}
              disabled={loading || !form.name.trim()}
              className="relative z-10 px-8 py-3 rounded-xl bg-white/10 border border-white/20 text-slate-300 font-bold text-xs uppercase hover:bg-white/20 transition-all active:scale-95 disabled:opacity-30"
            >
              {loading ? <Spinner size={14} /> : 'Подтвердить создание'}
            </button>

            {/* Background Decor */}
            <img src="/tor.png" className="absolute -right-4 -bottom-8 w-40 opacity-20 rotate-12 blur-sm group-hover:scale-110 transition-transform" />
          </div>

        </div>
        {error && <div className="absolute bottom-4 left-8 text-red-400 text-[10px] font-bold uppercase">{error}</div>}
      </div>
    </div>
  );
};

export default CreateProjectModal;