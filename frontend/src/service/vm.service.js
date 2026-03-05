import apiClient from './api.service';

/**
 * VM Service — эндпоинты для обычного пользователя
 * Бэкенд сам определяет owner_id из JWT токена через get_current_user
 */
const vmService = {

  /**
   * Создать VM внутри тенента
   * POST /vm/
   * @param {{ name: string, cpu: number, ram: number, ssd: number, network_speed?: number }} payload
   */
  async createVm(payload) {
    const { data } = await apiClient.post('/vm/', payload);
    return data;
  },

  /**
   * Получить информацию о VM
   * GET /vm/{server_id}
   * @param {string} serverId - UUID сервера
   */
  async getVm(serverId) {
    const { data } = await apiClient.get(`/vm/${serverId}`);
    return data;
  },

  /**
   * Обновить параметры VM (cpu, ram, ssd, network_speed)
   * PATCH /vm/{server_id}
   * @param {string} serverId
   * @param {{ cpu?: number, ram?: number, ssd?: number, network_speed?: number }} payload
   */
  async updateVm(serverId, payload) {
    const { data } = await apiClient.patch(`/vm/${serverId}`, payload);
    return data;
  },

  /**
   * Удалить VM
   * DELETE /vm/{server_id}
   * @param {string} serverId
   */
  async deleteVm(serverId) {
    await apiClient.delete(`/vm/${serverId}`);
  },

  /**
   * Создать SSH ссылку для VM (ставится в очередь)
   * POST /vm/{server_id}/ssh
   * @param {string} serverId
   * @returns {{ job_id: string, message: string }}
   */
  async createSsh(serverId) {
    const { data } = await apiClient.post(`/vm/${serverId}/ssh`);
    return data;
  },

  /**
   * Запустить VM
   * POST /vm/{server_id}/start
   * @param {string} serverId
   */
  async startVm(serverId) {
    const { data } = await apiClient.post(`/vm/${serverId}/start`);
    return data;
  },

  /**
   * Остановить VM
   * POST /vm/{server_id}/stop
   * @param {string} serverId
   */
  async stopVm(serverId) {
    const { data } = await apiClient.post(`/vm/${serverId}/stop`);
    return data;
  },
};

export default vmService;