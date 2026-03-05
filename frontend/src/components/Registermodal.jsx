import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Eye, EyeOff } from 'lucide-react';
import authApi from '../service/auth.service';

const PASSWORD_RULES = [
  { label: '10 знаков',                       test: (p) => p.length >= 10 },
  { label: '1 строчная латинская буква (a-z)', test: (p) => /[a-z]/.test(p) },
  { label: '1 спец. символ (!@#$%^)',          test: (p) => /[!@#$%^&*]/.test(p) },
  { label: '1 цифра',                          test: (p) => /\d/.test(p) },
  { label: '1 заглавная латинская буква (A-Z)',test: (p) => /[A-Z]/.test(p) },
];

const InputField = ({ label, placeholder, type = 'text', value, onChange, suffix, disabled }) => (
  <div className="flex flex-col gap-1.5">
    <label className="text-neutral-400 text-xs px-0.5">{label}</label>
    <div
      className="flex items-center rounded-lg overflow-hidden"
      style={{ border: '1px solid rgba(100,80,200,0.4)', background: 'rgba(255,255,255,0.03)' }}
    >
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className="flex-1 bg-transparent text-white text-sm px-4 py-3 outline-none placeholder:text-neutral-600 disabled:opacity-50"
      />
      {suffix && <div className="pr-4 text-neutral-500">{suffix}</div>}
    </div>
  </div>
);

export const RegisterModal = ({ isOpen, onClose, onSwitchToLogin }) => {
  const [email, setEmail]             = useState('');
  const [password, setPassword]       = useState('');
  const [confirm, setConfirm]         = useState('');
  const [showPass, setShowPass]       = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');
  const [success, setSuccess]         = useState(false);

  const allRulesPassed = PASSWORD_RULES.every(({ test }) => test(password));
  const passwordsMatch = password === confirm && confirm.length > 0;
  const canSubmit = email && allRulesPassed && passwordsMatch && !loading;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setError('');
    setLoading(true);
    try {
      await authApi.register(email, password);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onSwitchToLogin();
      }, 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const eyeBtn = (show, toggle) => (
    <button type="button" onClick={toggle} className="hover:text-neutral-300 transition-colors">
      {show ? <Eye size={17} /> : <EyeOff size={17} />}
    </button>
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            className="absolute inset-0 bg-black/75 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          <motion.div
            className="relative w-full max-w-2xl rounded-2xl overflow-hidden"
            style={{
              background: '#0d0d18',
              border: '1px solid rgba(100,80,200,0.35)',
              boxShadow: '0 0 0 1px rgba(80,60,180,0.15), 0 24px 80px rgba(20,10,60,0.8)',
            }}
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-neutral-500 hover:text-white transition-colors z-10"
            >
              <X size={16} />
            </button>

            <div className="flex min-h-[460px]">
              {/* Sidebar */}
              <div
                className="w-56 flex-shrink-0 flex flex-col justify-between p-7 rounded-l-2xl"
                style={{
                  background: 'linear-gradient(160deg, #1a1035 0%, #0d0a20 100%)',
                  borderRight: '1px solid rgba(100,80,200,0.2)',
                }}
              >
                <div>
                  <h2 className="text-white text-2xl font-semibold mb-4 leading-tight">Регистрация</h2>
                  <p className="text-neutral-500 text-xs mb-5">Уже есть аккаунт?</p>
                  <button
                    onClick={onSwitchToLogin}
                    className="px-5 py-1.5 rounded-full text-white text-xs font-medium transition-colors hover:bg-white/10"
                    style={{
                      background: 'rgba(255,255,255,0.08)',
                      border: '1px solid rgba(255,255,255,0.12)',
                    }}
                  >
                    Войти
                  </button>
                </div>
                <a href="#" className="text-purple-400 hover:text-purple-300 text-xs transition-colors">
                  Нужна помощь?
                </a>
              </div>

              {/* Form */}
              <div className="flex-1 p-8 flex flex-col">
                <h3 className="text-white text-lg font-semibold mb-6">Данные профиля</h3>

                <div className="flex flex-col gap-4 flex-1">
                  <InputField
                    label="Email"
                    placeholder="Введите ваш email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={loading}
                  />

                  <InputField
                    label="Пароль"
                    placeholder="Придумайте надёжный пароль"
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    suffix={eyeBtn(showPass, () => setShowPass((v) => !v))}
                    disabled={loading}
                  />

                  {/* Password rules */}
                  <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 px-1">
                    {PASSWORD_RULES.map(({ label, test }) => (
                      <div key={label} className="flex items-center gap-2">
                        <span
                          className="w-1.5 h-1.5 rounded-full flex-shrink-0 transition-colors duration-300"
                          style={{ background: test(password) ? '#a855f7' : 'rgba(255,255,255,0.15)' }}
                        />
                        <span
                          className="text-[11px] transition-colors duration-300"
                          style={{ color: test(password) ? '#c084fc' : '#525252' }}
                        >
                          {label}
                        </span>
                      </div>
                    ))}
                  </div>

                  <InputField
                    label="Подтверждение пароля"
                    placeholder="Подтвердите пароль"
                    type={showConfirm ? 'text' : 'password'}
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    suffix={eyeBtn(showConfirm, () => setShowConfirm((v) => !v))}
                    disabled={loading}
                  />

                  {/* Ошибка или успех */}
                  {error && (
                    <p className="text-red-400 text-xs px-1">{error}</p>
                  )}
                  {confirm.length > 0 && !passwordsMatch && (
                    <p className="text-red-400 text-xs px-1">Пароли не совпадают</p>
                  )}
                </div>

                <div
                  className="mt-6 pt-5 flex justify-end"
                  style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
                >
                  <motion.button
                    onClick={handleSubmit}
                    disabled={!canSubmit}
                    className="px-8 py-2.5 rounded-xl text-white text-sm font-semibold tracking-wide transition-opacity"
                    style={{
                      background: success
                        ? 'linear-gradient(90deg, #1a6e3d 0%, #0f4526 100%)'
                        : 'linear-gradient(90deg, #3d1f6e 0%, #251045 100%)',
                      border: '1px solid rgba(140,70,255,0.25)',
                      boxShadow: '0 4px 20px rgba(80,30,180,0.25)',
                      opacity: canSubmit ? 1 : 0.45,
                    }}
                    whileHover={canSubmit ? { scale: 1.02 } : {}}
                    whileTap={canSubmit ? { scale: 0.97 } : {}}
                  >
                    {success ? '✓ Готово!' : loading ? 'Регистрация...' : 'Зарегистрироваться'}
                  </motion.button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};