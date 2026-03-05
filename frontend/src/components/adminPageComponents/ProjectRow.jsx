import { useState, useEffect, useCallback } from 'react';
import { ChevronRight, FolderOpen, RefreshCw, Trash2 } from 'lucide-react';
import { Badge, ActionBtn, Spinner } from './UI';
import VmRow from './VmRow';
import adminService from '../../service/Admin.service';

const ProjectRow = ({ project, userId, onRefresh }) => {
  const [expanded, setExpanded]   = useState(false);
  const [vms, setVms]             = useState([]);
  const [vmsLoading, setVmsLoading] = useState(false);
  const [loading, setLoading]     = useState('');

  const loadVms = useCallback(async () => {
    setVmsLoading(true);
    try {
      const data = await adminService.getServersByProject(project.id);
      setVms(Array.isArray(data) ? data : []);
    } catch { setVms([]); }
    finally { setVmsLoading(false); }
  }, [project.id]);

  useEffect(() => { if (expanded) loadVms(); }, [expanded, loadVms]);

  const act = async (action) => {
    setLoading(action);
    try {
      if (action === 'disable') await adminService.disableProject(project.id);
      if (action === 'enable')  await adminService.activateProject(project.id);
      if (action === 'delete')  await adminService.deleteProject(project.id);
      onRefresh();
    } catch (e) { alert(e.message); }
    finally { setLoading(''); }
  };

  const isActive = project.status?.toLowerCase() === 'active';

  return (
    <div className="rounded-xl border border-white/[0.06] overflow-hidden">
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-white/[0.03] transition-colors"
        onClick={() => setExpanded(v => !v)}
      >
        <ChevronRight
          size={13}
          className={`text-slate-500 transition-transform flex-shrink-0 ${expanded ? 'rotate-90' : ''}`}
        />
        <FolderOpen size={13} className="text-blue-400 flex-shrink-0" />
        <span className="text-white text-sm flex-1 truncate">{project.name}</span>
        <span className="text-slate-500 text-xs">
          CPU {project.cpu_quota} / RAM {project.ram_quota}GB / SSD {project.ssd_quota}GB
        </span>

        <Badge color={isActive ? 'green' : 'gray'}>{project.status}</Badge>

        <div className="flex gap-1.5 ml-1" onClick={e => e.stopPropagation()}>
          {isActive ? (
            <ActionBtn color="red" onClick={() => act('disable')} disabled={!!loading}>
              {loading === 'disable' ? <Spinner size={11}/> : 'Выкл'}
            </ActionBtn>
          ) : (
            <ActionBtn color="green" onClick={() => act('enable')} disabled={!!loading}>
              {loading === 'enable' ? <Spinner size={11}/> : 'Вкл'}
            </ActionBtn>
          )}

          <ActionBtn color="gray" onClick={() => act('delete')} disabled={!!loading} title="Удалить">
            {loading === 'delete' ? <Spinner size={11}/> : <Trash2 size={11}/>}
          </ActionBtn>
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-3 border-t border-white/[0.04]">
          <div className="flex items-center justify-between mt-3 mb-2">
            <span className="text-slate-500 text-xs">Виртуальные машины</span>
            <button onClick={loadVms} className="text-slate-500 hover:text-purple-400 transition-colors">
              <RefreshCw size={11}/>
            </button>
          </div>

          {vmsLoading ? (
            <div className="flex justify-center py-3"><Spinner /></div>
          ) : vms.length === 0 ? (
            <p className="text-slate-600 text-xs text-center py-3">Нет виртуальных машин</p>
          ) : (
            <div className="flex flex-col gap-1.5">
              {vms.map(vm => <VmRow key={vm.id} vm={vm} onRefresh={loadVms} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectRow;