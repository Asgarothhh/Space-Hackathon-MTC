import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import AiChat from '../components/AiChat';

// Иконки для статистики и табов
import {
  Users, Server, FolderOpen, ShieldOff, Activity,
  CheckCircle, RefreshCw, AlertCircle
} from 'lucide-react';

// Общие компоненты
import UserBadge from '../components/UserBadge';

// UI атомы (экспортированы как именованные)
import { Badge, Spinner, GlassCard } from '../components/adminPageComponents/UI';

// Декомпозированные компоненты страницы (экспортированы как default)
import UserRow from '../components/adminPageComponents/UserRow';
import VmRow from '../components/adminPageComponents/VmRow';
// import ProjectRow импортируется внутри UserRow, здесь он обычно не нужен, 
// если только не выводится отдельным списком

// Сервисы
import authApi from '../service/auth.service';
import adminService from '../service/Admin.service';
import apiClient from '../service/api.service';



const AdminPage = () => {
  const navigate = useNavigate();
  const [users, setUsers]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [search, setSearch]       = useState('');
  const [tab, setTab]             = useState('users'); // users | disabled_vms | disabled_projects
  const [disabledVms, setDisabledVms]           = useState([]);
  const [disabledProjects, setDisabledProjects] = useState([]);
  const [tabLoading, setTabLoading]             = useState(false);

  useEffect(() => {
    if (!authApi.isAuthenticated()) { navigate('/'); return; }
    if (!authApi.isAdmin())         { navigate('/dashboard'); return; }
  }, [navigate]);

  const loadUsers = useCallback(async () => {
    setLoading(true); setError('');
    try {
      // GET /user/admin/list — список всех пользователей
      const { data } = await apiClient.get('/user/admin/list');
      setUsers(Array.isArray(data) ? data : []);
    } catch (e) {
      setError('Не удалось загрузить пользователей: ' + (e.response?.data?.detail || e.message));
    } finally { setLoading(false); }
  }, []);

  const loadDisabledVms = useCallback(async () => {
    setTabLoading(true);
    try {
      const data = await adminService.getDisabledServers();
      setDisabledVms(Array.isArray(data) ? data : []);
    } catch { setDisabledVms([]); }
    finally { setTabLoading(false); }
  }, []);

  const loadDisabledProjects = useCallback(async () => {
    setTabLoading(true);
    try {
      const data = await adminService.getDisabledProjects();
      setDisabledProjects(Array.isArray(data) ? data : []);
    } catch { setDisabledProjects([]); }
    finally { setTabLoading(false); }
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  useEffect(() => {
    if (tab === 'disabled_vms')      loadDisabledVms();
    if (tab === 'disabled_projects') loadDisabledProjects();
  }, [tab, loadDisabledVms, loadDisabledProjects]);

  const filtered = users.filter(u => u.email?.toLowerCase().includes(search.toLowerCase()));

  const stats = [
    { label: 'Всего пользователей', value: users.length,                          icon: Users,      color: '#a78bfa' },
    { label: 'Активных',            value: users.filter(u => u.is_active).length,  icon: CheckCircle,color: '#4ade80' },
    { label: 'Заблокировано',       value: users.filter(u => !u.is_active).length, icon: ShieldOff,  color: '#f87171' },
    { label: 'Администраторов',     value: users.filter(u => u.role === 'admin').length, icon: Activity, color: '#60a5fa' },
  ];

  return (
    <div className="w-full min-h-screen text-white" style={{ background: 'linear-gradient(160deg,#07040f 0%,#04020a 100%)' }}>
      <style>{`
        @keyframes orb { 0%,100%{transform:translate(-50%,-50%) scale(1)} 50%{transform:translate(-50%,-50%) scale(1.15)} }
        .orb { animation: orb 8s ease-in-out infinite; }
        ::-webkit-scrollbar { width:4px } ::-webkit-scrollbar-track { background:transparent }
        ::-webkit-scrollbar-thumb { background:rgba(140,70,255,0.3); border-radius:2px }
      `}</style>

      {/* Background orb */}
      <div aria-hidden className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="orb absolute top-1/3 left-1/2 w-[600px] h-[600px] rounded-full"
          style={{ background: 'radial-gradient(circle,rgba(80,20,160,0.18) 0%,transparent 70%)', transform:'translate(-50%,-50%)' }} />
      </div>

      {/* Layout */}
      <div className="relative z-10 flex flex-col min-h-screen">

        {/* Topbar */}
        <div className="flex items-center justify-between px-8 py-4 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <span className="text-slate-400 text-sm">Панель администратора</span>
          </div>
          <UserBadge />
        </div>

        <div className="flex-1 px-8 py-8 max-w-5xl mx-auto w-full">

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white tracking-tight mb-1">Управление платформой</h1>
            <p className="text-slate-500 text-sm">Пользователи, проекты и виртуальные машины</p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            {stats.map((s, i) => (
              <GlassCard key={i} className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-slate-500 text-xs">{s.label}</span>
                  <s.icon size={14} style={{ color: s.color }} />
                </div>
                <span className="text-2xl font-bold text-white">
                  {loading ? '—' : s.value}
                </span>
              </GlassCard>
            ))}
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mb-6 p-1 rounded-xl border border-white/[0.06] bg-white/[0.02] w-fit">
            {[
              { key: 'users',            label: 'Пользователи',        icon: Users },
              { key: 'disabled_vms',     label: 'Отключённые VM',      icon: Server },
              { key: 'disabled_projects',label: 'Отключённые проекты', icon: FolderOpen },
            ].map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all"
                style={{
                  background: tab === t.key ? 'rgba(140,70,255,0.2)' : 'transparent',
                  color: tab === t.key ? '#c084fc' : '#64748b',
                  border: tab === t.key ? '1px solid rgba(140,70,255,0.3)' : '1px solid transparent',
                }}
              >
                <t.icon size={13} /> {t.label}
              </button>
            ))}
          </div>

          {/* Tab: Users */}
          {tab === 'users' && (
            <>
              <div className="flex items-center gap-3 mb-4">
                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Поиск по email..."
                  className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-purple-500/40 placeholder:text-slate-600"
                />
                <button
                  onClick={loadUsers}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-slate-400 hover:text-white border border-white/[0.08] hover:border-white/20 transition-colors"
                >
                  <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                  Обновить
                </button>
              </div>

              {error && (
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl border border-red-500/25 bg-red-500/8 text-red-400 text-sm mb-4">
                  <AlertCircle size={14} /> {error}
                </div>
              )}

              {loading ? (
                <div className="flex justify-center py-20"><Spinner size={24} /></div>
              ) : filtered.length === 0 ? (
                <div className="text-center py-20">
                  <Users size={32} className="text-slate-700 mx-auto mb-3" />
                  <p className="text-slate-500">{search ? 'Пользователи не найдены' : 'Нет пользователей'}</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {filtered.map(u => (
                    <UserRow key={u.id} user={u} onRefresh={loadUsers} />
                  ))}
                </div>
              )}
            </>
          )}

          {/* Tab: Disabled VMs */}
          {tab === 'disabled_vms' && (
            <div>
              <div className="flex justify-end mb-4">
                <button onClick={loadDisabledVms}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-slate-400 hover:text-white border border-white/[0.08] transition-colors">
                  <RefreshCw size={13} className={tabLoading ? 'animate-spin' : ''} /> Обновить
                </button>
              </div>
              {tabLoading ? (
                <div className="flex justify-center py-20"><Spinner size={24} /></div>
              ) : disabledVms.length === 0 ? (
                <div className="text-center py-20">
                  <Server size={32} className="text-slate-700 mx-auto mb-3" />
                  <p className="text-slate-500">Нет отключённых VM</p>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {disabledVms.map(vm => <VmRow key={vm.id} vm={vm} onRefresh={loadDisabledVms} />)}
                </div>
              )}
            </div>
          )}

          {/* Tab: Disabled Projects */}
          {tab === 'disabled_projects' && (
            <div>
              <div className="flex justify-end mb-4">
                <button onClick={loadDisabledProjects}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-slate-400 hover:text-white border border-white/[0.08] transition-colors">
                  <RefreshCw size={13} className={tabLoading ? 'animate-spin' : ''} /> Обновить
                </button>
              </div>
              {tabLoading ? (
                <div className="flex justify-center py-20"><Spinner size={24} /></div>
              ) : disabledProjects.length === 0 ? (
                <div className="text-center py-20">
                  <FolderOpen size={32} className="text-slate-700 mx-auto mb-3" />
                  <p className="text-slate-500">Нет отключённых проектов</p>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {disabledProjects.map(p => (
                    <div key={p.id} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.05] text-sm">
                      <FolderOpen size={13} className="text-blue-400" />
                      <span className="text-white flex-1">{p.name}</span>
                      <span className="text-slate-500 text-xs">CPU {p.cpu_quota} / RAM {p.ram_quota}GB</span>
                      <Badge color="gray">{p.status}</Badge>
                      <button
                        onClick={async () => { await adminService.activateProject(p.id); loadDisabledProjects(); }}
                        className="text-[11px] px-2.5 py-1 rounded-lg border border-green-500/25 text-green-400 hover:bg-green-500/10 transition-colors">
                        Активировать
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
            <AiChat />
        </div>
      </div>
    </div>
  );
};

export default AdminPage;