import axios from 'axios';
import { API_CONFIG } from '../config/api.config';

const API_URL = API_CONFIG.BASE_URL;

class AgentService {
  /**
   * Загрузка архива или файла для анализа агентом
   * @param {File} file 
   * @returns {Promise<{project_root: string}>}
   */
  async uploadProject(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_URL}/agent/file_loader`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  /**
   * Отправка вопроса агенту
   * @param {string} message 
   * @param {string|null} projectRoot 
   * @param {string} load 
   */
  async askAgent(message, projectRoot = null, load = 'medium') {
    const formData = new FormData();
    formData.append('user_message', message);
    formData.append('expected_load', load);
    if (projectRoot) {
      formData.append('project_root', projectRoot);
    }

    const response = await axios.post(`${API_URL}/agent/ask`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data; // { response: "текст", specs: {...}, docker_created: bool }
  }
}

export default new AgentService();