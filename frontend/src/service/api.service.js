import axios from 'axios';
import { API_CONFIG } from '../config/api.config';

const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем токен из localStorage к каждому запросу
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token'); // ключ совпадает с auth.service.js
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Перехватчик ответа — обрабатываем 401 глобально
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_email');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default apiClient;