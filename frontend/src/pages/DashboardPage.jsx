import React, { useState } from 'react';
import UserBadge from '../components/UserBadge';
import CreateServerModal from '../components/CreateServerModal';
import AiChat from '../components/AiChat';

const CARDS = [
  { title: 'Проекты', desc: 'Управление окружениями', btn: 'Просмотреть', action: null },
  { title: 'Облачные решения', desc: 'Готовые конфигурации', btn: 'Создать сервер', action: 'createServer' },
  { title: 'SSL сертификат', desc: 'Выпуск и продление SSL', btn: 'Получить', action: null },
  { title: 'DNS хостинг', desc: 'DNS-конфигурация', btn: 'Запустить', action: null },
  { title: 'Домены', desc: 'Регистрация и продление', btn: 'Получить', action: null },
  { title: 'Статистика', desc: 'Аналитика инфраструктуры', btn: 'Просмотреть', action: null, highlight: true },
];

const DashboardPage = () => {
  const [isCreateServerOpen, setCreateServerOpen] = useState(false);

  const handleCardAction = (action) => {
    if (action === 'createServer') setCreateServerOpen(true);
  };

  return (
    <>
      <div
        className="w-full min-h-screen text-white"
        style={{ 
          background: 'linear-gradient(160deg, #05030a 0%, #000000 100%)', 
          position: 'relative', 
          overflow: 'hidden' 
        }}
      >
        <style>{`
          /* 1. Анимация фонового шара (Orb) */
          @keyframes spin-gradient {
            0%   { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(360deg); }
          }
          .rotating-gradient { 
            animation: spin-gradient 20s linear infinite; 
            opacity: 0.5;
          }

          /* 2. Анимация внутреннего свечения карточек */
          @keyframes move-bg {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
          }

          /* 3. Базовое состояние КАРТОЧКИ (Серое/Пустое) */
          .glass-card {
            position: relative;
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 24px;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid rgba(255, 255, 255, 0.05);
            overflow: hidden;
            z-index: 2;
            transition: all 0.5s cubic-bezier(0.2, 1, 0.3, 1);
            cursor: pointer;
          }

          /* 4. Единый HOVER для всей карточки */
          .glass-card:hover {
            background: rgba(13, 10, 29, 0.9);
            border-color: rgba(140, 70, 255, 0.3);
            transform: translateY(-4px);
            /* Сетка квадратов проявляется при ховере */
            background-image: 
              linear-gradient(rgba(110, 40, 200, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(110, 40, 200, 0.1) 1px, transparent 1px);
            background-size: 20px 20px;
          }

          /* Плавное появление свечения при ховере */
          .glass-card::after {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 50% 120%, rgba(110, 40, 200, 0.4) 0%, transparent 75%);
            opacity: 0;
            transition: opacity 0.5s ease;
            z-index: -1;
            pointer-events: none;
          }
          .glass-card:hover::after {
            opacity: 1;
            animation: move-bg 6s ease infinite;
          }

          /* 5. Кнопка внутри карточки (Управляется ховером родителя) */
          .action-btn {
            margin-top: auto;
            padding: 10px 20px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #475569;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.5s ease;
            pointer-events: none; /* Чтобы не мешать ховеру карточки */
            text-align: center;
          }

          .glass-card:hover .action-btn {
            background: linear-gradient(135deg, #6e28c8 0%, #4a148c 100%);
            border-color: rgba(255, 255, 255, 0.2);
            color: #ffffff;
            box-shadow: 0 4px 20px rgba(110, 40, 200, 0.5);
          }

          /* 6. Кнопка Ask AI */
          .ask-ai-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(110, 40, 220, 0.12);
            border: 1px solid rgba(140, 70, 255, 0.25);
            border-radius: 20px;
            color: #c084fc;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
          }
          .ask-ai-btn:hover {
            background: rgba(110, 40, 220, 0.2);
            border-color: rgba(140, 70, 255, 0.5);
            transform: scale(1.03);
          }

          .my-services-btn {
            margin-top: 40px;
            padding: 12px 60px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.95);
            color: #000;
            font-weight: 700;
            transition: all 0.3s;
          }
          .my-services-btn:hover { transform: scale(1.05); background: #fff; }
        `}</style>

        {/* Анимированный фон (Orb) */}
        <div style={{ position: 'absolute', top: '50%', left: '50%', width: 0, height: 0, pointerEvents: 'none', zIndex: 0 }}>
          <div className="rotating-gradient" style={{
              position: 'absolute',
              width: '750px',
              height: '750px',
              borderRadius: '50%',
              background: `conic-gradient(from 0deg, rgba(110,40,200,0) 0%, rgba(110,40,200,0.4) 25%, rgba(60,10,140,0.1) 50%, rgba(140,60,240,0.3) 75%, rgba(110,40,200,0) 100%)`,
              filter: 'blur(100px)',
            }}
          />
        </div>

        {/* Контент страницы */}
        <div style={{ position: 'relative', zIndex: 1 }} className="w-full min-h-screen flex flex-col">
          
          <div className="flex-1 flex flex-col items-center px-8 py-10">
            
            {/* Header (Ask AI | Title | UserBadge) */}
            <div className="w-full max-w-[1100px] flex items-center justify-between mb-12">
              
              <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-start' }}>
              </div>

              <h1 style={{ 
                color: '#ffffff', 
                fontSize: '34px', 
                fontWeight: 300, // Тонкий шрифт
                letterSpacing: '0.01em',
                textAlign: 'center',
                margin: 0
              }}>
                Личный кабинет
              </h1>

              <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
                <UserBadge />
              </div>
            </div>

            {/* Subtitle */}
            <p style={{ color: '#475569', fontSize: '15px', textAlign: 'center', marginBottom: '50px', lineHeight: 1.6 }}>
              Автоматизация инфраструктуры<br />начинается здесь
            </p>

            {/* Grid с карточками */}
            <div style={{
              width: '100%',
              maxWidth: '960px',
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '16px',
            }}>
              {CARDS.map((card, i) => (
                <div 
                  key={i} 
                  className="glass-card" 
                  onClick={() => handleCardAction(card.action)}
                >
                  <h3 style={{ 
                    color: '#f1f5f9', 
                    fontWeight: 500, 
                    fontSize: '17px',
                    transition: 'color 0.4s' 
                  }}>
                    {card.title}
                  </h3>
                  <p style={{ color: '#475569', fontSize: '13px', flex: 1 }}>
                    {card.desc}
                  </p>
                  <button className="action-btn">
                    {card.btn}
                  </button>
                </div>
              ))}
            </div>

            {/* Большая кнопка внизу */}
            <button className="my-services-btn shadow-lg shadow-purple-900/20">
              Мои услуги
            </button>

          </div>
        </div>

        <AiChat />
      </div>

      {/* Модальное окно */}
      <CreateServerModal
        isOpen={isCreateServerOpen}
        onClose={() => setCreateServerOpen(false)}
      />
    </>
  );
};

export default DashboardPage;