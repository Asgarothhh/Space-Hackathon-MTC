import { API_CONFIG } from '../config/api.config';

const BASE_URL = API_CONFIG.BASE_URL;

const authApi = {
  async register(email, password) {
    const res = await fetch(`${BASE_URL}/user/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Ошибка регистрации');
    return data;
  },

  async login(email, password) {
    const res = await fetch(`${BASE_URL}/user/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Неверный email или пароль');

    // Бэкенд теперь возвращает { access_token, role }
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user_email', email);
    localStorage.setItem('user_role', data.role); // 'admin' | 'user'

    return data; // { access_token, role }
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_role');
  },

  getToken() {
    return localStorage.getItem('access_token');
  },

  getRole() {
    return localStorage.getItem('user_role') || 'user';
  },

  isAdmin() {
    return this.getRole() === 'admin';
  },

  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  },
};

export default authApi;

// Отдельный экспорт для использования в admin.service.js
export const isAdmin = () => authApi.isAdmin();