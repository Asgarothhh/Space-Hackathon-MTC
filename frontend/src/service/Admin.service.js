import apiClient from './api.service';
import authApi from './auth.service';

// isAdmin читает user_role из localStorage — выставляется при логине
const requireAdmin = () => {
  if (!authApi.isAdmin()) {
    throw new Error('Доступ запрещён: требуются права администратора');
  }
};

const adminService = {

  // ── Проекты ──────────────────────────────────────────────────────

  async addProject(userId, payload) {
    requireAdmin();
    const { data } = await apiClient.post(`/project/admin/add/${userId}`, payload);
    return data;
  },

  async disableProject(projectId) {
    requireAdmin();
    const { data } = await apiClient.post(`/project/admin/disable/${projectId}`);
    return data;
  },

  async activateProject(projectId) {
    requireAdmin();
    const { data } = await apiClient.post(`/project/admin/active/${projectId}`);
    return data;
  },

  async deleteProject(projectId) {
    requireAdmin();
    await apiClient.delete(`/project/admin/delete/${projectId}`);
  },

  async getProject(projectId) {
    requireAdmin();
    const { data } = await apiClient.get(`/project/admin/info/${projectId}`);
    return data;
  },

  async getProjectsByUser(userId) {
    requireAdmin();
    const { data } = await apiClient.get(`/projects/admin/info/${userId}`);
    return data.projects ?? [];
  },

  async getDisabledProjects() {
    requireAdmin();
    const { data } = await apiClient.get('/projects/admin/disabled');
    return data.projects ?? [];
  },

  // ── Серверы ───────────────────────────────────────────────────────

  async addServer(userId, payload) {
    requireAdmin();
    const { data } = await apiClient.post(`/server/admin/add/${userId}`, payload);
    return data;
  },

  async disableServer(serverId) {
    requireAdmin();
    const { data } = await apiClient.post(`/server/admin/disable/${serverId}`);
    return data;
  },

  async activateServer(serverId) {
    requireAdmin();
    const { data } = await apiClient.post(`/server/admin/active/${serverId}`);
    return data;
  },

  async deleteServer(serverId) {
    requireAdmin();
    await apiClient.delete(`/server/admin/delete/${serverId}`);
  },

  async getServer(serverId) {
    requireAdmin();
    const { data } = await apiClient.get(`/server/admin/info/${serverId}`);
    return data;
  },

  async getDisabledServers() {
    requireAdmin();
    const { data } = await apiClient.get('/servers/admin/disabled');
    return data.servers ?? [];
  },

  async getServersByUser(userId) {
    requireAdmin();
    const { data } = await apiClient.get(`/servers/admin/info/user/${userId}`);
    return data.servers ?? [];
  },

  async getServersByProject(projectId) {
    requireAdmin();
    const { data } = await apiClient.get(`/servers/admin/info/project/${projectId}`);
    return data.servers ?? [];
  },

  // ── Пользователи ─────────────────────────────────────────────────

  async disableUser(userId) {
    requireAdmin();
    const { data } = await apiClient.post(`/user/admin/disable/${userId}`);
    return data;
  },

  async activateUser(userId) {
    requireAdmin();
    const { data } = await apiClient.post(`/user/admin/active/${userId}`);
    return data;
  },

  async deleteUser(userId) {
    requireAdmin();
    await apiClient.delete(`/user/admin/delete/${userId}`);
  },
};

export default adminService;