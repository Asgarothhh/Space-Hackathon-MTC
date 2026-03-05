import { useState, useRef, useEffect } from 'react';
import { ArrowLeft, ChevronDown, AlertCircle, Loader2, Plus, Minus } from 'lucide-react';
import vmService from '../service/vm.service';
import torusImg from '/tor.png';

/* ─────────────────────────────────────────────
   Counter: ручной ввод + кнопки + / -
───────────────────────────────────────────── */
const Counter = ({ value, onChange, min = 0, max = 9999 }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
    <button onClick={() => onChange(Math.max(min, value - 1))} style={ctrBtn}>
      <Minus size={12} />
    </button>
    <input
      type="number"
      value={value}
      onChange={e => {
        const v = parseInt(e.target.value, 10);
        if (!isNaN(v)) onChange(Math.max(min, Math.min(max, v)));
      }}
      style={ctrInput}
    />
    <button
      onClick={() => onChange(Math.min(max, value + 1))}
      style={{ ...ctrBtn, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.12)' }}
    >
      <Plus size={12} />
    </button>
  </div>
);

/* ─────────────────────────────────────────────
   Toggle switch
───────────────────────────────────────────── */
const Toggle = ({ checked, onChange }) => (
  <div
    onClick={() => onChange(!checked)}
    style={{
      width: 38, height: 21, borderRadius: 11, flexShrink: 0,
      background: checked ? '#7c3aed' : 'rgba(255,255,255,0.08)',
      border: '1px solid rgba(255,255,255,0.1)',
      cursor: 'pointer', position: 'relative', transition: 'background 0.2s',
    }}
  >
    <div style={{
      position: 'absolute', top: 2,
      left: checked ? 19 : 2,
      width: 15, height: 15, borderRadius: '50%',
      background: '#fff', transition: 'left 0.2s',
    }} />
  </div>
);

/* ─────────────────────────────────────────────
   OS selector — единая кнопка (название + версия)
───────────────────────────────────────────── */
const OsDropdown = ({ os, isSelected, onSelect }) => {
  const [open, setOpen] = useState(false);
  const [version, setVersion] = useState('');
  const ref = useRef(null);

  // закрываем по клику вне
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const pick = (v) => { setVersion(v); setOpen(false); onSelect(os.id, v); };
  const handleClick = () => { onSelect(os.id, version || os.versions[0]); setOpen(p => !p); };

  return (
    <div ref={ref} style={{ flex: 1, position: 'relative' }}>
      {/* Единая кнопка */}
      <div
        onClick={handleClick}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 14px', borderRadius: 12, cursor: 'pointer',
          border: `1px solid ${isSelected ? 'rgba(140,70,255,0.55)' : 'rgba(255,255,255,0.08)'}`,
          background: isSelected
            ? 'linear-gradient(135deg, rgba(110,40,200,0.35) 0%, rgba(70,20,140,0.2) 100%)'
            : 'rgba(255,255,255,0.03)',
          transition: 'all 0.2s',
          gap: 8,
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, overflow: 'hidden' }}>
          <span style={{
            fontSize: 12, fontWeight: 600, letterSpacing: '0.04em',
            color: isSelected ? '#e9d5ff' : '#9ca3af', textTransform: 'lowercase',
          }}>
            {os.label}
          </span>
          <span style={{
            fontSize: 11, color: version ? (isSelected ? '#c4b5fd' : '#9ca3af') : '#4b5563',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            {version || 'Версия'}
          </span>
        </div>
        <ChevronDown
          size={13}
          style={{
            color: isSelected ? '#a78bfa' : '#4b5563',
            transform: open ? 'rotate(180deg)' : 'none',
            transition: 'transform 0.2s', flexShrink: 0,
          }}
        />
      </div>

      {/* Dropdown */}
      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 6px)', left: 0, right: 0, zIndex: 400,
          background: '#0a0618', border: '1px solid rgba(140,70,255,0.3)',
          borderRadius: 12, overflow: 'hidden', boxShadow: '0 12px 40px rgba(0,0,0,0.7)',
        }}>
          {os.versions.map(v => (
            <div
              key={v} onClick={() => pick(v)}
              style={{ padding: '10px 14px', fontSize: 12, cursor: 'pointer', color: '#d1d5db', transition: 'background 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(110,40,200,0.22)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              {v}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/* ─────────────────────────────────────────────
   Styled select
───────────────────────────────────────────── */
const StyledSelect = ({ value, onChange, options, placeholder }) => (
  <select
    value={value}
    onChange={e => onChange(e.target.value)}
    style={{
      background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 10, color: value ? '#fff' : '#6b7280',
      fontSize: 13, padding: '9px 12px', cursor: 'pointer',
      outline: 'none', width: '100%', appearance: 'none',
    }}
  >
    {placeholder && <option value="">{placeholder}</option>}
    {options.map(o => <option key={o} value={o} style={{ background: '#0d0820' }}>{o}</option>)}
  </select>
);

/* ─────────────────────────────────────────────
   UI primitives
───────────────────────────────────────────── */
const Card = ({ children, style }) => (
  <div style={{
    background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: 16, padding: '18px 20px', ...style,
  }}>
    {children}
  </div>
);

const SecTitle = ({ children }) => (
  <div style={{ fontSize: 12, fontWeight: 600, color: '#a78bfa', marginBottom: 14, letterSpacing: '0.05em' }}>
    {children}
  </div>
);

const Lbl = ({ children }) => (
  <div style={{ fontSize: 10, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
    {children}
  </div>
);

const TxtInput = ({ value, onChange, placeholder }) => (
  <input
    value={value} onChange={onChange} placeholder={placeholder}
    style={{
      width: '100%', boxSizing: 'border-box',
      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 10, color: '#fff', fontSize: 13, padding: '10px 14px', outline: 'none',
    }}
    onFocus={e => e.target.style.borderColor = 'rgba(140,70,255,0.5)'}
    onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
  />
);

/* ─────────────────────────────────────────────
   DATA
───────────────────────────────────────────── */
const OS_LIST = [
  { id: 'debian', label: 'debian', versions: ['Debian 10 Buster', 'Debian 11 Bullseye', 'Debian 12 Bookworm'] },
  { id: 'ubuntu', label: 'ubuntu', versions: ['Ubuntu 20.04 LTS', 'Ubuntu 22.04 LTS', 'Ubuntu 24.04 LTS'] },
  { id: 'centos', label: 'centos', versions: ['CentOS 7', 'CentOS 8 Stream', 'CentOS 9 Stream'] },
];

/* ─────────────────────────────────────────────
   MAIN MODAL
───────────────────────────────────────────── */
const CreateServerModal = ({ isOpen, onClose, onSuccess }) => {
  const [serverName, setServerName] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [selectedOS, setSelectedOS] = useState({ id: 'debian', ver: 'Debian 12 Bookworm' });
  const [region, setRegion] = useState('');
  const [ram, setRam] = useState(1);
  const [cpu, setCpu] = useState(1);
  const [accessLogin, setAccessLogin] = useState(false);
  const [accessCloud, setAccessCloud] = useState(false);
  const [netSpeed, setNetSpeed] = useState(1);
  const [netType, setNetType] = useState('Интернет');
  const [diskSize, setDiskSize] = useState(3);
  const [diskType, setDiskType] = useState('SSD');
  const [autoBackup, setAutoBackup] = useState(false);
  const [backupTime, setBackupTime] = useState('03:16');
  const [dailyOn, setDailyOn] = useState(false);
  const [dailyCnt, setDailyCnt] = useState(0);
  const [weeklyOn, setWeeklyOn] = useState(false);
  const [weeklyCnt, setWeeklyCnt] = useState(0);
  const [monthlyOn, setMonthlyOn] = useState(false);
  const [monthlyCnt, setMonthlyCnt] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleCreate = async () => {
    if (!serverName.trim()) return setError('Укажите название сервера');
    setLoading(true); setError('');
    try {
      const result = await vmService.createVm({ name: serverName, cpu, ram, ssd: diskSize, os: selectedOS.ver });
      if (onSuccess) onSuccess(result);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка создания сервера');
    } finally { setLoading(false); }
  };

  return (
    <>
      <style>{`
        .csm-ov { animation: cFade .2s ease }
        .csm-bx { animation: cSlide .25s cubic-bezier(.2,1,.3,1) }
        @keyframes cFade  { from{opacity:0} to{opacity:1} }
        @keyframes cSlide { from{opacity:0;transform:translateY(20px) scale(.98)} to{opacity:1;transform:none} }
        .csm-bx::-webkit-scrollbar{width:4px}
        .csm-bx::-webkit-scrollbar-thumb{background:rgba(140,70,255,.3);border-radius:4px}
        .add-btn{width:100%;padding:9px 0;border-radius:10px;font-size:13px;cursor:pointer;transition:all .2s;
          background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);color:#9ca3af}
        .add-btn:hover{background:rgba(255,255,255,.09);color:#d1d5db}
        .ssh-btn{width:100%;padding:9px 0;border-radius:10px;font-size:13px;cursor:pointer;transition:all .2s;
          background:rgba(110,40,200,.2);border:1px solid rgba(140,70,255,.3);color:#c4b5fd}
        .ssh-btn:hover{background:rgba(110,40,200,.38)}
        .sub-btn{width:100%;padding:14px 0;border-radius:14px;font-size:15px;font-weight:600;cursor:pointer;
          letter-spacing:.02em;border:none;color:#fff;
          background:linear-gradient(135deg,#7c3aed,#4f1f99);transition:all .2s}
        .sub-btn:hover{background:linear-gradient(135deg,#8b45f5,#5e25b8);
          box-shadow:0 6px 24px rgba(110,40,200,.5)}
        .sub-btn:disabled{opacity:.5;cursor:not-allowed}
        .chk{accent-color:#7c3aed;width:15px;height:15px;cursor:pointer;flex-shrink:0}
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button{-webkit-appearance:none;margin:0}
        input[type=number]{-moz-appearance:textfield}
        @keyframes spin{to{transform:rotate(360deg)}}
        .spin{animation:spin 1s linear infinite;display:inline-block}
      `}</style>

      {/* Overlay */}
      <div
        className="csm-ov"
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          background: 'rgba(0,0,0,0.82)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
          padding: '24px 16px', overflowY: 'auto',
        }}
      >
        <div
          className="csm-bx"
          onClick={e => e.stopPropagation()}
          style={{
            width: '100%', maxWidth: 880,
            background: '#000',
            border: '1px solid rgba(140,70,255,0.15)',
            borderRadius: 24, padding: '24px 28px 28px',
            color: '#fff', position: 'relative', overflowY: 'auto',
          }}
        >
          {/* Glow */}
          <div style={{ position:'absolute',top:0,right:0,width:300,height:300,background:'rgba(110,40,200,0.07)',filter:'blur(100px)',pointerEvents:'none',borderRadius:'50%' }} />
          <div style={{ position:'absolute',bottom:0,left:0,width:200,height:200,background:'rgba(60,10,140,0.05)',filter:'blur(80px)',pointerEvents:'none',borderRadius:'50%' }} />

          {/* Header */}
          <div style={{ display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:22,position:'relative',zIndex:1 }}>
            <button onClick={onClose} style={{ background:'none',border:'none',color:'#6b7280',cursor:'pointer',padding:4 }}>
              <ArrowLeft size={20} />
            </button>
            <h2 style={{ margin:0,fontSize:20,fontWeight:400,color:'#f1f5f9',letterSpacing:'0.01em' }}>
              Создание нового сервера
            </h2>
            <div style={{ width:28 }} />
          </div>


          {/* ══════════════════════════════════════════════════════
              GRID: 2 колонки сверху + 2 колонки снизу
              Используем CSS grid 2×2, левая колонка уже правой
          ══════════════════════════════════════════════════════ */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '220px 1fr',
            gridTemplateRows: 'auto auto',
            gap: 14,
            marginBottom: 18,
            position: 'relative', zIndex: 1,
          }}>

            {/* ── ДИВ 1: Картинка + название сервера (без фона) ── */}
            <div style={{ display:'flex', flexDirection:'column', gap:16, padding:'4px 0' }}>
              {/* Тор — прямо на чёрном фоне */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:150 }}>
                <img
                  src={torusImg} alt="server"
                  style={{ width:'90%', objectFit:'contain', filter:'drop-shadow(0 0 28px rgba(140,70,255,0.3))' }}
                />
              </div>
              <div>
                <Lbl>Название сервера</Lbl>
                <TxtInput value={serverName} onChange={e => setServerName(e.target.value)} placeholder="Введите название" />
              </div>
            </div>

            {/* ── ДИВ 2: ОС + Регион + Ресурсы + Доступы (фиолетовый градиент снизу → чёрный сверху) ── */}
            <div style={{
              borderRadius: 18,
              padding: '22px 24px',
              background: 'linear-gradient(to top, rgba(88,28,220,0.55) 0%, rgba(40,10,90,0.35) 45%, rgba(0,0,0,0) 100%)',
              border: '1px solid rgba(140,70,255,0.18)',
              display: 'flex', flexDirection: 'column', gap: 18,
            }}>

              {/* OS */}
              <div>
                <Lbl>Операционная система</Lbl>
                <div style={{ display:'flex', gap:10 }}>
                  {OS_LIST.map(os => (
                    <OsDropdown
                      key={os.id} os={os}
                      isSelected={selectedOS.id === os.id}
                      onSelect={(id, ver) => setSelectedOS({ id, ver })}
                    />
                  ))}
                </div>
              </div>

              {/* Регион + Доступы */}
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
                <div>
                  <Lbl>Регион</Lbl>
                  <StyledSelect
                    value={region} onChange={setRegion}
                    options={['Авто','Москва','Санкт-Петербург','Новосибирск']}
                    placeholder="Авто"
                  />
                </div>
                <div style={{
                  background:'rgba(90,30,180,0.15)',
                  border:'1px solid rgba(140,70,255,0.2)',
                  borderRadius:12, padding:'12px 14px',
                }}>
                  <SecTitle>Доступы</SecTitle>
                  <div style={{ display:'flex', flexDirection:'column', gap:9 }}>
                    <label style={{ display:'flex', alignItems:'center', gap:9, cursor:'pointer' }}>
                      <input className="chk" type="checkbox" checked={accessLogin} onChange={e => setAccessLogin(e.target.checked)} />
                      <span style={{ fontSize:13, color:'#d1d5db' }}>Логин и пароль</span>
                    </label>
                    <label style={{ display:'flex', alignItems:'center', gap:9, cursor:'pointer' }}>
                      <input className="chk" type="checkbox" checked={accessCloud} onChange={e => setAccessCloud(e.target.checked)} />
                      <span style={{ fontSize:13, color:'#d1d5db' }}>cognifycloud</span>
                    </label>
                    <button className="ssh-btn" style={{ marginTop:4 }}>Добавить SSH ключ</button>
                  </div>
                </div>
              </div>

              {/* Ресурсы */}
              <div>
                <Lbl>Ресурсы</Lbl>
                <div style={{ display:'flex', gap:36, flexWrap:'wrap' }}>
                  <div>
                    <div style={{ fontSize:10, color:'#6b7280', marginBottom:6 }}>RAM (от 1 до 126 ГБ)</div>
                    <Counter value={ram} onChange={setRam} min={1} max={126} />
                  </div>
                  <div>
                    <div style={{ fontSize:10, color:'#6b7280', marginBottom:6 }}>CPU (от 1 до 47 ядер)</div>
                    <Counter value={cpu} onChange={setCpu} min={1} max={47} />
                  </div>
                </div>
              </div>

            </div>

            {/* ── ДИВ 3: Сеть + Диск (тот же градиент что у дива 2, под первым дивом) ── */}
            <div style={{
              borderRadius: 18,
              padding: '22px 24px',
              background: 'linear-gradient(to top, rgba(88,28,220,0.55) 0%, rgba(40,10,90,0.35) 45%, rgba(0,0,0,0) 100%)',
              border: '1px solid rgba(140,70,255,0.18)',
              display: 'flex', flexDirection: 'column', gap: 20,
            }}>

              {/* Сеть */}
              <div>
                <SecTitle>Сеть</SecTitle>
                <div style={{ display:'flex', gap:14, alignItems:'flex-end', flexWrap:'wrap' }}>
                  <div>
                    <div style={{ fontSize:10, color:'#6b7280', marginBottom:6 }}>Скорость (от 1 до 300 Мбпс)</div>
                    <Counter value={netSpeed} onChange={setNetSpeed} min={1} max={300} />
                  </div>
                  <div style={{ flex:1, minWidth:110 }}>
                    <div style={{ fontSize:10, color:'#6b7280', marginBottom:6 }}>Тип сети</div>
                    <StyledSelect value={netType} onChange={setNetType} options={['Интернет','Приватная','Гибридная']} />
                  </div>
                </div>
                <button className="add-btn" style={{ marginTop:12 }}>Добавить интерфейс</button>
              </div>

              {/* Разделитель */}
              <div style={{ height:1, background:'rgba(140,70,255,0.12)' }} />

              {/* Диск */}
              <div>
                <SecTitle>Диск</SecTitle>
                <div style={{ display:'flex', gap:14, alignItems:'flex-end', flexWrap:'wrap' }}>
                  <div>
                    <div style={{ fontSize:10, color:'#6b7280', marginBottom:6 }}>Размер (от 3 до 1536 ГБ)</div>
                    <Counter value={diskSize} onChange={setDiskSize} min={3} max={1536} />
                  </div>
                  <div style={{ flex:1, minWidth:110 }}>
                    <div style={{ fontSize:10, color:'#6b7280', marginBottom:6 }}>Тип диска</div>
                    <StyledSelect value={diskType} onChange={setDiskType} options={['SSD','NVMe','HDD']} />
                  </div>
                </div>
                <button className="add-btn" style={{ marginTop:12 }}>Добавить диск</button>
              </div>

            </div>

            {/* ── ДИВ 4: Дополнительные услуги (без фона) ── */}
            <div style={{ padding:'4px 8px', display:'flex', flexDirection:'column', gap:16 }}>

              <SecTitle>Дополнительные услуги</SecTitle>

              {/* Auto backup toggle */}
              <div style={{ display:'flex', alignItems:'flex-start', gap:12 }}>
                <Toggle checked={autoBackup} onChange={setAutoBackup} />
                <div>
                  <div style={{ fontSize:14, color:'#d1d5db', lineHeight:1.3 }}>Автоматическое резервное копирование</div>
                  <div style={{ fontSize:11, color:'#4b5563', marginTop:3 }}>стоимость зависит от объёма хранимых данных</div>
                </div>
              </div>

              {/* Backup time */}
              <div>
                <div style={{ fontSize:11, color:'#6b7280', marginBottom:6 }}>Время бекапирования</div>
                <input
                  type="time" value={backupTime} onChange={e => setBackupTime(e.target.value)}
                  disabled={!autoBackup}
                  style={{
                    background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.1)',
                    borderRadius:10, color: autoBackup ? '#fff' : '#4b5563',
                    fontSize:13, padding:'9px 14px', outline:'none', width:160,
                  }}
                />
              </div>

              {/* Copy rows */}
              {[
                { label:'Хранить ежедневные копии (шт):', on:dailyOn, setOn:setDailyOn, cnt:dailyCnt, setCnt:setDailyCnt, max:365 },
                { label:'Хранить еженедельные копии (шт):', on:weeklyOn, setOn:setWeeklyOn, cnt:weeklyCnt, setCnt:setWeeklyCnt, max:52 },
                { label:'Хранить ежемесячные копии (шт):', on:monthlyOn, setOn:setMonthlyOn, cnt:monthlyCnt, setCnt:setMonthlyCnt, max:24 },
              ].map(row => (
                <div key={row.label} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:12 }}>
                  <label style={{ display:'flex', alignItems:'center', gap:9, flex:1, cursor: autoBackup ? 'pointer' : 'default' }}>
                    <input
                      className="chk" type="checkbox"
                      checked={row.on} onChange={e => row.setOn(e.target.checked)}
                      disabled={!autoBackup}
                    />
                    <span style={{ fontSize:13, color: autoBackup ? '#d1d5db' : '#4b5563' }}>{row.label}</span>
                  </label>
                  <Counter value={row.cnt} onChange={row.setCnt} min={0} max={row.max} />
                </div>
              ))}

            </div>

          </div>

          {/* Error */}
          {error && (
            <div style={{ display:'flex',alignItems:'center',gap:8,color:'#f87171',fontSize:12,marginBottom:12,position:'relative',zIndex:1 }}>
              <AlertCircle size={14} /> {error}
            </div>
          )}

          {/* Submit */}
          <div style={{ position:'relative',zIndex:1 }}>
            <button className="sub-btn" onClick={handleCreate} disabled={loading}>
              {loading
                ? <Loader2 size={16} className="spin" />
                : 'Подтвердить создание'}
            </button>
          </div>

        </div>
      </div>
    </>
  );
};

const ctrBtn = {
  width:28,height:28,borderRadius:'50%',display:'flex',
  alignItems:'center',justifyContent:'center',cursor:'pointer',
  background:'rgba(110,40,200,0.3)',border:'1px solid rgba(140,70,255,0.35)',
  color:'#fff',flexShrink:0,padding:0,
};

const ctrInput = {
  width:48,textAlign:'center',background:'transparent',
  border:'1px solid rgba(255,255,255,0.1)',borderRadius:8,
  color:'#fff',fontSize:14,padding:'5px 0',outline:'none',
};

export default CreateServerModal;