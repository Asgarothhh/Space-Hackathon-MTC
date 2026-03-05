import { Twitter, Youtube, Instagram } from 'lucide-react';

const SECTIONS = [
  { title: 'Product',   links: ['Features', 'Integration', 'Updates', 'FAQ', 'Pricing'] },
  { title: 'Company',   links: ['About', 'Blog', 'Careers', 'Manifesto', 'Press', 'Contract'] },
  { title: 'Resources', links: ['Examples', 'Community', 'Guides', 'Docs', 'Press'] },
  { title: 'Legal',     links: ['Privacy', 'Terms', 'Security'] },
];

const SOCIAL = [
  { icon: <Twitter size={18} />, href: '#' },
  { icon: <Instagram size={18} />, href: '#' },
  { icon: <Youtube size={18} />, href: '#' },
];

const Footer = () => (
  <footer className="w-full bg-black border-t border-white/5 pt-16 pb-8">
    <div className="w-full px-6 md:px-12">

      <div className="flex flex-col lg:flex-row justify-between gap-12 mb-16">
        <div className="max-w-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center gap-1 cursor-pointer">
              <img
                src="/logo.png"
                alt="Logo"
                className="w-8 h-8 object-contain filter drop-shadow-[0_0_8px_rgba(168,85,247,0.6)]"
              />
            </div>
            <span className="text-white font-mono tracking-tighter font-bold text-lg">IaaS системы</span>
          </div>
          <p className="text-neutral-500 text-sm leading-relaxed font-mono">
            Инфраструктура как сервис. Полный контроль.
            Мгновенное развертывание
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-12 gap-y-10">
          {SECTIONS.map(({ title, links }) => (
            <div key={title}>
              <h3 className="text-white font-bold text-xs uppercase tracking-[0.2em] mb-6">{title}</h3>
              <ul className="space-y-4">
                {links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-neutral-500 hover:text-purple-400 text-xs transition-colors duration-300 font-mono">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6">
        <p className="text-[10px] text-neutral-600 font-mono uppercase tracking-widest">© 2026 COGNIFY</p>
        <div className="flex items-center gap-6">
          {SOCIAL.map(({ icon, href }, i) => (
            <a key={i} href={href} className="text-neutral-500 hover:text-white transition-colors">
              {icon}
            </a>
          ))}
        </div>
      </div>

    </div>
  </footer>
);

export default Footer;