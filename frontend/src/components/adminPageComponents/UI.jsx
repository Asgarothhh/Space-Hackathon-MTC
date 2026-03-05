import { Loader2 } from 'lucide-react';

/* ── цветовые токены ────────────────────────────────────
   Один источник истины для всех компонентов.
   border — граница, color — текст/иконка, hover — фон при наведении
─────────────────────────────────────────────────────── */
export const COLOR = {
  purple: { border: 'rgba(140,70,255,0.3)',   color: 'rgba(192,132,252,0.9)',  hover: 'rgba(140,70,255,0.1)'  },
  green:  { border: 'rgba(74,222,128,0.25)',  color: 'rgba(134,239,172,0.85)', hover: 'rgba(74,222,128,0.1)'  },
  red:    { border: 'rgba(248,113,113,0.25)', color: 'rgba(252,165,165,0.85)', hover: 'rgba(248,113,113,0.1)' },
  blue:   { border: 'rgba(96,165,250,0.25)',  color: 'rgba(147,197,253,0.85)', hover: 'rgba(96,165,250,0.1)'  },
  yellow: { border: 'rgba(251,191,36,0.25)',  color: 'rgba(253,224,71,0.85)',  hover: 'rgba(251,191,36,0.1)'  },
  gray:   { border: 'rgba(255,255,255,0.1)',  color: 'rgba(148,163,184,0.7)',  hover: 'rgba(255,255,255,0.06)'},
};

/* ── Badge ──────────────────────────────────────────── */
export const Badge = ({ children, color = 'purple' }) => {
  const t = COLOR[color] ?? COLOR.gray;
  return (
    <span style={{
      display:        'inline-flex',
      alignItems:     'center',
      padding:        '2px 8px',
      borderRadius:   '999px',
      fontSize:       '10px',
      fontWeight:     600,
      letterSpacing:  '0.07em',
      textTransform:  'uppercase',
      background:     'transparent',
      border:         `1px solid ${t.border}`,
      color:           t.color,
      backdropFilter: 'blur(4px)',
      whiteSpace:     'nowrap',
    }}>
      {children}
    </span>
  );
};

/* ── ActionBtn ──────────────────────────────────────────
   Единая кнопка действия для всех строк таблицы.
   color: 'purple' | 'green' | 'red' | 'blue' | 'gray'
   Поддерживает иконки и текст, disabled state.
─────────────────────────────────────────────────────── */
export const ActionBtn = ({
  children,
  color    = 'gray',
  onClick,
  disabled = false,
  title,
}) => {
  const t = COLOR[color] ?? COLOR.gray;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      style={{
        display:        'inline-flex',
        alignItems:     'center',
        gap:            '4px',
        padding:        '4px 10px',
        borderRadius:   '8px',
        fontSize:       '11px',
        fontWeight:     500,
        background:     'transparent',
        border:         `1px solid ${t.border}`,
        color:           t.color,
        cursor:          disabled ? 'not-allowed' : 'pointer',
        opacity:         disabled ? 0.4 : 1,
        transition:     'background 0.15s, border-color 0.15s',
        whiteSpace:     'nowrap',
        backdropFilter: 'blur(4px)',
      }}
      onMouseEnter={e => { if (!disabled) e.currentTarget.style.background = t.hover; }}
      onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
    >
      {children}
    </button>
  );
};

/* ── Spinner ────────────────────────────────────────── */
export const Spinner = ({ size = 16 }) => (
  <Loader2 size={size} className="animate-spin text-purple-400" />
);

/* ── GlassCard ──────────────────────────────────────── */
export const GlassCard = ({ children, className = '', style = {} }) => (
  <div
    className={`rounded-2xl border border-white/[0.07] backdrop-blur-sm ${className}`}
    style={{ background: 'rgba(255,255,255,0.03)', ...style }}
  >
    {children}
  </div>
);