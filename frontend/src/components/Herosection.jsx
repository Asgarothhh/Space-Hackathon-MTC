import { motion } from 'framer-motion';

const CARDS = [
  {
    icon: "/1.png",
    title: 'Экспертная поддержка 24/7',
    desc: 'Проактивный мониторинг и системные инженеры работают в режиме 24/7 и на связи в любое время дня и ночи.',
  },
  {
    icon: "/2.png",
    title: 'Оптимизация расходов',
    desc: 'Поминутная тарификация и никаких затрат на собственное оборудование и его обслуживание.',
  },
  {
    icon: "/3.png",
    title: 'Упрощение IT-процессов',
    desc: 'Устанавливайте готовые решения и развивайте свои продукты, экономя время IT-специалистов.',
  },
  {
    icon: "/4.png",
    title: 'Аттестованный контур',
    desc: (
      <>
        Возможность размещения проектов в облаке{' '}
        с повышенными стандартами безопасности
        для хранения и обработки персональных данных.
      </>
    ),
  },
  {
    icon: "/5.png",
    title: 'Прозрачность и предсказуемость',
    desc: 'Наглядные дашборды для контроля мощностей и прогноза расходов.',
  },
  {
    icon: "/6.png",
    title: 'Гибкое управление',
    desc: (
      <>
        Увеличивайте и уменьшайте выделенные ресурсы исходя из изменения нагрузки на ваши{' '}
        <span className="font-semibold text-white">онлайн-проекты</span>.
      </>
    ),
  },
];

const cardStyle = {
  background: 'linear-gradient(145deg, black 0%, #0e0a1a 100%)',
  border: '1px solid rgba(120,60,220,0.2)',
  boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
};

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: 'easeOut', delay: i * 0.08 },
  }),
};

const HeroSection = () => (
  <main className="w-full bg-black min-h-screen relative overflow-hidden">

    {/* Rotating gradient orb — крутится бесконечно */}
    <style>{`
      @keyframes spin-gradient {
        0%   { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
      }
      .rotating-gradient {
        animation: spin-gradient 12s linear infinite;
      }
    `}</style>

    {/* Контейнер орба: фиксированный размер, overflow скрыт снаружи */}
    <div
      aria-hidden
      className="pointer-events-none absolute top-[18%] left-1/2"
      style={{ width: 0, height: 0 }}
    >
      <div
        className="rotating-gradient"
        style={{
          position: 'absolute',
          width: '900px',
          height: '900px',
          borderRadius: '50%',
          background: `conic-gradient(
            from 0deg,
            rgba(110,40,200,0)    0%,
            rgba(110,40,200,0.55) 20%,
            rgba(60,10,140,0.35)  40%,
            rgba(140,60,240,0.45) 60%,
            rgba(80,20,180,0.3)   80%,
            rgba(110,40,200,0)    100%
          )`,
          filter: 'blur(72px)',
        }}
      />
    </div>

    {/* Hero text */}
    <section className="relative w-full flex flex-col items-center text-center pt-20 pb-12 px-6">

      <motion.div
        className="relative mb-8 flex items-center gap-2 border border-purple-500/40 bg-purple-950/50 rounded-full px-4 py-1.5"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={0}
      >
        <span className="bg-purple-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full tracking-widest">AI</span>
        <span className="text-purple-300 text-xs font-mono tracking-wide">Спросите ассистента</span>
      </motion.div>

      <motion.h1
        className="relative text-white  text-4xl md:text-5xl leading-tight max-w-3xl"
          variants={fadeUp}
          initial="hidden"
        animate="visible"
        custom={1}
      >
        Инфраструктура как сервис. Полный контроль.
        <br />
        <span className="text-purple-400">Мгновенное развертывание</span>
      </motion.h1>

      <motion.p
        className="relative mt-6 text-neutral-400 text-base max-w-xl leading-relaxed"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={2}
      >
        Предсказуемая производительность, изоляция проектов,
        <br className="hidden md:block" /> прозрачный биллинг
      </motion.p>

      <motion.button
        className="relative mt-10 px-8 py-3 border border-white/30 rounded-lg text-white text-sm font-medium hover:bg-white/5 transition-colors duration-200 tracking-wide"
        variants={fadeUp}
        initial="hidden"
        animate="visible"
        custom={3}
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
      >
        Узнать подробности
      </motion.button>
    </section>

    {/* Cards */}
    <section className="relative w-full px-4 md:px-10 pb-20 pt-20">
      <div className="relative w-full max-w-6xl mx-auto flex gap-4 items-stretch">

        <motion.div
          className="hidden lg:flex flex-shrink-0 w-44 rounded-2xl overflow-hidden"
          style={cardStyle}
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          custom={0}
        >
          <img src="/heroSectionBlocks.jpg" alt="Hero visual" className="w-full h-full object-cover" />
        </motion.div>

        <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {CARDS.map((card, i) => (
            <motion.div
              key={i}
              className="relative rounded-2xl p-6 flex flex-col gap-4 overflow-hidden"
              style={cardStyle}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2, margin: '0px 0px -60px 0px' }}
              custom={i}
              whileHover={{ y: -3, boxShadow: '0 8px 32px rgba(120,60,220,0.2)' }}
            >
              <div
                aria-hidden
                className="absolute top-0 left-0 w-24 h-24 pointer-events-none"
                style={{ background: 'radial-gradient(circle at 0% 0%, rgba(140,60,255,0.12) 0%, transparent 70%)' }}
              />
              <img src={card.icon} alt={card.title} className="w-6 h-6 object-contain" />
              <h3 className="relative text-white font-semibold text-sm leading-snug">{card.title}</h3>
              <p className="relative text-neutral-500 text-xs leading-relaxed">{card.desc}</p>
            </motion.div>
          ))}
        </div>

      </div>
    </section>

  </main>
);

export default HeroSection;