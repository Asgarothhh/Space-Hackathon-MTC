import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Eye, EyeOff } from 'lucide-react';

const FloatingInput = ({ label, type, value, onChange, suffix }) => {
  const [focused, setFocused] = useState(false);
  const active = focused || value.length > 0;

  return (
    <div className="relative">
      <label
        className="absolute left-4 transition-all duration-200 pointer-events-none text-neutral-500 z-10"
        style={{
          top: active ? '-9px' : '50%',
          transform: active ? 'none' : 'translateY(-50%)',
          fontSize: active ? '11px' : '14px',
        }}
      >
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className="w-full bg-transparent text-white text-sm outline-none pr-10 pl-4 py-4 rounded-xl"
        style={{
          border: `1px solid ${focused ? 'rgba(140,70,255,0.6)' : 'rgba(255,255,255,0.15)'}`,
          boxShadow: focused ? '0 0 0 3px rgba(120,50,220,0.12)' : 'none',
          transition: 'border-color 0.2s, box-shadow 0.2s',
        }}
      />
      {suffix && (
        <div className="absolute right-4 top-1/2 -translate-y-1/2">{suffix}</div>
      )}
    </div>
  );
};

export const LoginModal = ({ isOpen, onClose, onSwitchToRegister }) => {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail]               = useState('');
  const [password, setPassword]         = useState('');

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          <motion.div
            className="relative w-full max-w-md rounded-2xl overflow-hidden"
            style={{
              background: 'linear-gradient(160deg, #371C60 0%, #1c0e38 40%, #000000 100%)',
              border: '1px solid rgba(140,70,255,0.2)',
              boxShadow: '0 24px 80px rgba(55,28,96,0.6), 0 0 0 1px rgba(255,255,255,0.04)',
            }}
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            <button
              onClick={onClose}
              className="absolute top-5 right-5 text-neutral-400 hover:text-white transition-colors z-10"
            >
              <X size={18} />
            </button>

            <div className="px-10 pt-12 pb-10">
              <h2 className="text-white text-2xl font-semibold mb-10 tracking-tight">Авторизация</h2>

              <div className="flex flex-col gap-5">
                <FloatingInput
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <FloatingInput
                  label="Пароль"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  suffix={
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="text-neutral-500 hover:text-neutral-300 transition-colors"
                    >
                      {showPassword ? <Eye size={18} /> : <EyeOff size={18} />}
                    </button>
                  }
                />
              </div>

              <div className="flex justify-end mt-3">
                <a href="#" className="text-[#7C4FBF] hover:text-purple-400 text-sm transition-colors">
                  Забыли пароль?
                </a>
              </div>

              <motion.button
                className="w-full mt-6 py-3.5 rounded-xl text-white text-sm font-semibold tracking-wide"
                style={{
                  background: 'linear-gradient(90deg, #4a1f80 0%, #2d1050 100%)',
                  border: '1px solid rgba(140,70,255,0.3)',
                  boxShadow: '0 4px 20px rgba(100,40,200,0.3)',
                }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Войти
              </motion.button>

              <p className="mt-6 text-neutral-500 text-sm">
                Нет аккаунта?{' '}
                <button
                  onClick={onSwitchToRegister}
                  className="text-[#7C4FBF] hover:text-purple-400 transition-colors"
                >
                  Зарегистрируйтесь
                </button>
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};