import apiClient from './api.service';
import { API_CONFIG } from '../config/api.config';

export const authService = {
  async login(email, password) {
    try {
      const response = await apiClient.post(API_CONFIG.ENDPOINTS.LOGIN, {
        email,
        password,
      });
      
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data?.message || 'Ошибка входа';
    }
  },

  logout() {
    localStorage.removeItem('token');
    window.location.reload();
  }
};