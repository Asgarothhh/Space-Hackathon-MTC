import { useState, useEffect, useCallback } from 'react';
import {
  ChevronDown, Plus, ShieldOff, CheckCircle,
  Trash2, RefreshCw, FolderOpen, Server,
} from 'lucide-react';

import { GlassCard, Badge, ActionBtn, Spinner } from './UI';
import ProjectRow from './ProjectRow';
import CreateProjectModal from './CreateProjectModal';
import CreateServerModal from '../CreateServerModal';
import adminService from '../../service/Admin.service';

const UserRow = ({ user, onRefresh }) => {
  const [expanded, setExpanded]                   = useState(false);
  const [projects, setProjects]                   = useState([]);
  const [projLoading, setProjLoading]             = useState(false);
  const [loading, setLoading]                     = useState('');
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showCreateServer, setShowCreateServer]   = useState(false);

  const loadProjects = useCallback(async () => {
    setProjLoading(true);
    try {
      const data = await adminService.getProjectsByUser(user.id);
      setProjects(Array.isArray(data) ? data : []);
    } catch { setProjects([]); }
    finally { setProjLoading(false); }
  }, [user.id]);

  useEffect(() => { if (expanded) loadProjects(); }, [expanded, loadProjects]);

  const act = async (action) => {
    setLoading(action);
    try {
      if (action === 'disable') await adminService.disableUser(user.id);
      if (action === 'enable')  await adminService.activateUser(user.id);
      if (action === 'delete')  { await adminService.deleteUser(user.id); onRefresh(); return; }
      onRefresh();
    } catch (e) { alert(e.message); }
    finally { setLoading(''); }
  };

  const isActive = user.is_active;
  const isAdmin  = user.role === 'admin';

  return (
    <>
      {showCreateProject && (
        <CreateProjectModal
          userId={user.id}
          onClose={() => setShowCreateProject(false)}
          onCreated={loadProjects}
        />
      )}

      <CreateServerModal
        isOpen={showCreateServer}
        onClose={() => setShowCreateServer(false)}
        userId={user.id}
        onSuccess={() => {
          setShowCreateServer(false);
          if (expanded) loadProjects();
        }}
      />

      <GlassCard className="overflow-hidden">
        <div
          className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
          onClick={() => setExpanded(v => !v)}
        >
          {/* Avatar */}
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
            style={{
              background: isAdmin ? 'rgba(248,113,113,0.15)' : 'rgba(140,70,255,0.15)',
              color:      isAdmin ? 'rgba(252,165,165,0.9)'  : 'rgba(192,132,252,0.9)',
              border:     isAdmin ? '1px solid rgba(248,113,113,0.25)' : '1px solid rgba(140,70,255,0.25)',
            }}
          >
            {user.email[0].toUpperCase()}
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-white text-sm truncate">{user.email}</p>
            <p className="text-slate-600 text-xs">{user.id?.slice(0, 8)}…</p>
          </div>

          <Badge color={isAdmin ? 'red' : 'purple'}>{user.role}</Badge>
          <Badge color={isActive ? 'green' : 'gray'}>{isActive ? 'active' : 'blocked'}</Badge>

          {/* Action buttons */}
          <div className="flex gap-1.5 ml-2" onClick={e => e.stopPropagation()}>

            <ActionBtn
              color="purple"
              onClick={() => { setExpanded(true); setShowCreateProject(true); }}
              disabled={!!loading}
            >
              <Plus size={10}/> Проект
            </ActionBtn>

            <ActionBtn
              color="blue"
              onClick={() => setShowCreateServer(true)}
              disabled={!!loading}
            >
              <Server size={10}/> Сервер
            </ActionBtn>

            {isActive ? (
              <ActionBtn color="red" onClick={() => act('disable')} disabled={!!loading} title="Заблокировать">
                {loading === 'disable' ? <Spinner size={11}/> : <ShieldOff size={11}/>}
              </ActionBtn>
            ) : (
              <ActionBtn color="green" onClick={() => act('enable')} disabled={!!loading} title="Разблокировать">
                {loading === 'enable' ? <Spinner size={11}/> : <CheckCircle size={11}/>}
              </ActionBtn>
            )}

            {!isAdmin && (
              <ActionBtn color="gray" onClick={() => act('delete')} disabled={!!loading} title="Удалить">
                {loading === 'delete' ? <Spinner size={11}/> : <Trash2 size={11}/>}
              </ActionBtn>
            )}
          </div>

          <ChevronDown
            size={13}
            className={`text-slate-600 transition-transform flex-shrink-0 ${expanded ? 'rotate-180' : ''}`}
          />
        </div>

        {expanded && (
          <div className="border-t border-white/[0.05] px-5 py-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-slate-500 text-xs font-medium">Проекты пользователя</span>
              <button onClick={loadProjects} className="text-slate-500 hover:text-purple-400 transition-colors">
                <RefreshCw size={12}/>
              </button>
            </div>

            {projLoading ? (
              <div className="flex justify-center py-4"><Spinner /></div>
            ) : projects.length === 0 ? (
              <div className="text-center py-6">
                <FolderOpen size={24} className="text-slate-700 mx-auto mb-2" />
                <p className="text-slate-600 text-xs">Нет проектов. Создайте первый тенент.</p>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {projects.map(p => (
                  <ProjectRow key={p.id} project={p} userId={user.id} onRefresh={loadProjects} />
                ))}
              </div>
            )}
          </div>
        )}
      </GlassCard>
    </>
  );
};

export default UserRow;