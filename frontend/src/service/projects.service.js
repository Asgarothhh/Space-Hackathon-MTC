import apiClient from './api.service';

/**
 * Projects Service — эндпоинты проектов (тенентов) для обычного пользователя
 * Тенент предоставляется администратором, пользователь управляет им сам
 */
const projectsService = {

  /**
   * Создать проект
   * POST /projects
   * @param {{ name: string, cpu_quota?: number, ram_quota?: number, ssd_quota?: number }} payload
   */
  async createProject(payload) {
    const { data } = await apiClient.post('/projects', payload);
    return data;
  },

  /**
   * Получить список своих проектов
   * GET /projects
   */
  async listProjects() {
    const { data } = await apiClient.get('/projects');
    return data;
  },

  /**
   * Запустить проект (активировать тенент)
   * POST /projects/{project_id}/start
   * @param {string} projectId
   */
  async startProject(projectId) {
    const { data } = await apiClient.post(`/projects/${projectId}/start`);
    return data;
  },

  /**
   * Остановить проект
   * POST /projects/{project_id}/stop
   * @param {string} projectId
   */
  async stopProject(projectId) {
    const { data } = await apiClient.post(`/projects/${projectId}/stop`);
    return data;
  },

  /**
   * Обновить проект (переименовать и т.п.)
   * PATCH /projects/{project_id}
   * @param {string} projectId
   * @param {{ name?: string }} payload
   */
  async updateProject(projectId, payload) {
    const { data } = await apiClient.patch(`/projects/${projectId}`, payload);
    return data;
  },

  /**
   * Удалить проект
   * DELETE /projects/{project_id}
   * @param {string} projectId
   */
  async deleteProject(projectId) {
    await apiClient.delete(`/projects/${projectId}`);
  },

  /**
   * Поиск проектов текущего пользователя
   * GET /user/search_projects?q=...
   * @param {string} [query] - поисковая строка
   */
  async searchProjects(query = '') {
    const { data } = await apiClient.get('/user/search_projects', {
      params: query ? { q: query } : {},
    });
    return data;
  },
};

export default projectsService;