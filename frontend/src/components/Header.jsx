const NAV_ITEMS = ['Домены и хостинг', 'Облачные сервисы', 'Серверы', 'API'];

const Header = ({ onOpenLogin }) => (
  <header className="w-full sticky top-0 z-50 border-b border-white/10 bg-black backdrop-blur-xl">
    <div className="w-full px-4 md:px-10">
      <div className="flex justify-between items-center h-16">

        <div className="flex items-center gap-1 cursor-pointer pl-20">
          <img
            src="/logo.png"
            alt="Logo"
            className="w-8 h-8 object-contain filter drop-shadow-[0_0_8px_rgba(168,85,247,0.6)]"
          />
        </div>

        <nav className="hidden lg:flex items-center gap-1 border border-white/5 bg-white/5 rounded-full px-2 py-1">
          {NAV_ITEMS.map((item) => (
            <a
              key={item}
              href="#"
              className="px-4 py-1.5 text-[11px] uppercase tracking-wider text-neutral-400 hover:text-white hover:bg-white/5 rounded-full transition-all"
            >
              {item}
            </a>
          ))}
        </nav>

        <button 
          onClick={onOpenLogin} 
          className="group relative px-8 py-2 overflow-hidden rounded-full bg-black border border-white/20 transition-all duration-300 hover:border-white/40 active:scale-95"
        >
          {/* Анимация блеска (Shimmer) */}
          <div className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out">
            <div className="h-full w-1/2 bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-[-25deg]" />
          </div>

          {/* Текст кнопки */}
          <span className="relative z-10 text-[13px] text-white font-medium tracking-wide">
            Вход
          </span>

          {/* Еле заметное внутреннее свечение сверху */}
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        </button>

      </div>
    </div>
  </header>
);

export default Header;