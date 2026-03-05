import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import authApi from '../service/auth.service';
import pfpIcon from '/pfpIcon.jpg'; 

const PURPLE_BTN = 'rgba(120,50,220,0.3)';

const getUserEmail = () => {
  return localStorage.getItem('user_email') || 'kovalchuk@gmail.com';
};

const UserBadge = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const userEmail = getUserEmail();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    authApi.logout();
    navigate('/');
  };

  const menuItems = [
    { label: 'Мои услуги', icon: '/dropMenuPfp/box.png' },
    { label: 'Профиль', icon: '/dropMenuPfp/user.png' },
    { label: 'Настройка безопасности', icon: '/dropMenuPfp/shield.png' },
    { label: 'Уведомления', icon: '/dropMenuPfp/bell.png' },
    { label: 'Написать в поддержку', icon: '/dropMenuPfp/comment.png' },
  ];

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      {/* Добавляем стили анимации через обычный тег style */}
      <style>{`
        .dropdown-animate {
          transition: all 0.2s ease-out;
          transform-origin: top right;
          opacity: 0;
          transform: translateY(-10px) scale(0.95);
          pointer-events: none;
        }
        .dropdown-animate.show {
          opacity: 1;
          transform: translateY(0) scale(1);
          pointer-events: auto;
        }
      `}</style>

      {/* Кнопка-триггер: Черный див со скругленными краями */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '12px',
          padding: '6px 14px 6px 8px',
          backgroundColor: '#000', // Черный фон
          borderRadius: '20px',    // Скругленные края
          border: `1px solid ${isOpen ? 'rgba(255,255,255,0.2)' : '#222'}`,
          cursor: 'pointer',
          transition: 'border-color 0.2s, background 0.2s'
        }}
        onMouseEnter={e => e.currentTarget.style.background = '#0a0a0a'}
        onMouseLeave={e => e.currentTarget.style.background = '#000'}
      >
        {/* Аватарка */}
        <div style={{
          width: '32px', height: '32px', borderRadius: '50%',
          border: `1px solid ${PURPLE_BTN}`, overflow: 'hidden', flexShrink: 0
        }}>
          <img src={pfpIcon} alt="pfp" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>

        {/* Почта рядом с аватаркой */}
        <span style={{ 
          color: '#cbd5e1', 
          fontSize: '13px', 
          fontWeight: '400',
          maxWidth: '150px',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>
          {userEmail}
        </span>
      </div>

      {/* Выпадающее меню с анимацией */}
      <div className={`dropdown-animate ${isOpen ? 'show' : ''}`} style={{
        position: 'absolute', top: '130%', right: 0, width: '260px',
        backgroundColor: '#000', borderRadius: '16px', border: '1px solid #222',
        padding: '12px 0', zIndex: 1000, boxShadow: '0 10px 30px rgba(0,0,0,0.7)'
      }}>
        {/* Список пунктов */}
        {menuItems.map((item, idx) => (
          <div 
            key={idx}
            style={{
              padding: '10px 20px', color: '#fff', fontSize: '14px',
              display: 'flex', alignItems: 'center', gap: '14px', cursor: 'pointer',
              transition: 'background 0.2s'
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#111'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            <img src={item.icon} alt="" style={{ width: '18px', height: '18px', objectFit: 'contain' }} />
            {item.label}
          </div>
        ))}

        <div style={{ height: '1px', backgroundColor: '#222', margin: '8px 0' }} />

        {/* Выход */}
        <div 
          onClick={handleLogout}
          style={{
            padding: '10px 20px', color: '#fff', fontSize: '14px',
            display: 'flex', alignItems: 'center', gap: '14px', cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onMouseEnter={e => e.currentTarget.style.background = '#111'}
          onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
        >
          <img src="/dropMenuPfp/exit.png" alt="" style={{ width: '18px', height: '18px', objectFit: 'contain' }} />
          Выход
        </div>
      </div>
    </div>
  );
};

export default UserBadge;