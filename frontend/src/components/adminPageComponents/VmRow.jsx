import { useState } from 'react';
import { Server, Trash2 } from 'lucide-react';
import { Badge, ActionBtn, Spinner } from './UI';
import adminService from '../../service/Admin.service';

const VmRow = ({ vm, onRefresh }) => {
  const [loading, setLoading] = useState('');

  const act = async (action) => {
    setLoading(action);
    try {
      if (action === 'disable') await adminService.disableServer(vm.id);
      if (action === 'enable')  await adminService.activateServer(vm.id);
      if (action === 'delete')  await adminService.deleteServer(vm.id);
      onRefresh();
    } catch (e) { alert(e.message); }
    finally { setLoading(''); }
  };

  const statusColor =
    vm.status === 'RUNNING'  ? 'green' :
    vm.status === 'STOPPED'  ? 'gray'  : 'yellow';

  return (
    <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl border border-white/[0.05] text-sm"
      style={{ background: 'rgba(255,255,255,0.02)' }}
    >
      <Server size={13} className="text-slate-500 flex-shrink-0" />
      <span className="text-white flex-1 truncate">{vm.name}</span>
      <span className="text-slate-500 text-xs">{vm.cpu}vCPU / {vm.ram}GB / {vm.ssd}GB</span>

      <Badge color={statusColor}>{vm.status}</Badge>

      <div className="flex gap-1.5 ml-2">
        {vm.status !== 'STOPPED' ? (
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
  );
};

export default VmRow;