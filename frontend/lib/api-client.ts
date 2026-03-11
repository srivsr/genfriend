import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'

let clerkToken: string | null = null

export function setClerkToken(token: string | null) {
  clerkToken = token
}

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Add Clerk token to all requests
api.interceptors.request.use((config) => {
  if (clerkToken) {
    config.headers.Authorization = `Bearer ${clerkToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to sign-in if unauthorized
      if (typeof window !== 'undefined') {
        window.location.href = '/sign-in'
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  signup: (data: { email: string; password: string; name?: string }) => api.post('/auth/signup', data),
  login: (data: { email: string; password: string }) => api.post('/auth/login', data),
}

export const identityApi = {
  get: () => api.get('/identity'),
  create: (initial_input: string) => api.post('/identity', { initial_input }),
  refine: (additional_input: string) => api.post('/identity/refine', { additional_input }),
}

export const goalsApi = {
  list: (status?: string) => api.get('/goals', { params: { status } }),
  listArchived: () => api.get('/goals/archived'),
  create: (initial_input: string) => api.post('/goals', { initial_input }),
  get: (id: string) => api.get(`/goals/${id}`),
  update: (id: string, data: any) => api.patch(`/goals/${id}`, data),
  delete: (id: string) => api.delete(`/goals/${id}`),
  addKeyResult: (id: string, data: any) => api.post(`/goals/${id}/key-results`, data),
  updateProgress: (id: string, progress_percent: number) => api.patch(`/goals/${id}/progress`, { progress_percent }),
  analyze: (id: string) => api.get(`/goals/${id}/analysis`),
  pause: (id: string, data: { reason?: string; expected_resume_date?: string }) => api.post(`/goals/${id}/pause`, data),
  resume: (id: string, data: { adjust_timeline?: boolean }) => api.post(`/goals/${id}/resume`, data),
  complete: (id: string, data: { proud_of?: string; learned?: string; next_goal?: string }) => api.post(`/goals/${id}/complete`, data),
  archive: (id: string, data: { reason: string; learning?: string }) => api.post(`/goals/${id}/archive`, data),
  restore: (id: string, new_target_date?: string) => api.post(`/goals/${id}/restore`, { new_target_date }),
  deletePermanent: (id: string) => api.delete(`/goals/${id}/permanent`, { data: { confirmation: 'DELETE_PERMANENTLY' } }),
}

export const tasksApi = {
  list: (params?: { scheduled_date?: string; goal_id?: string; status?: string }) => api.get('/tasks', { params }),
  create: (data: { title: string; goal_id?: string; scheduled_date?: string }) => api.post('/tasks', data),
  update: (id: string, data: any) => api.patch(`/tasks/${id}`, data),
  complete: (id: string, data?: { outcome_notes?: string; contribution_to_goal?: string }) => api.post(`/tasks/${id}/complete`, data || {}),
  delete: (id: string) => api.delete(`/tasks/${id}`),
}

export const chatApi = {
  send: (message: string, conversation_id?: string) => api.post('/chat', { message, conversation_id }),
  getHistory: (conversation_id?: string) => api.get('/chat/history', { params: { conversation_id } }),
}

export const journalApi = {
  list: (entry_type?: string) => api.get('/journal', { params: { entry_type } }),
  create: (data: { entry_type: string; content: string; related_goal_id?: string; mood?: string }) => api.post('/journal', data),
  getWins: () => api.get('/journal/wins'),
  recall: (context: string) => api.post('/journal/recall', { context }),
}

export const progressApi = {
  overview: () => api.get('/progress/overview'),
  patterns: () => api.get('/progress/patterns'),
  detectPatterns: () => api.post('/progress/detect-patterns'),
  journey: () => api.get('/progress/journey'),
}

export const preferencesApi = {
  get: () => api.get('/preferences'),
  update: (data: any) => api.patch('/preferences', data),
}

export const academyApi = {
  topics: () => api.get('/academy/topics'),
  get: (slug: string) => api.get(`/academy/topics/${slug}`),
  ask: (question: string) => api.post('/academy/ask', { question }),
}

export const entriesApi = {
  list: (params?: { entry_type?: string; start_date?: string; end_date?: string }) => api.get('/entries', { params }),
  create: (data: { content: string; entry_type?: string; mood?: string; tags?: string[] }) => api.post('/entries', data),
  get: (id: string) => api.get(`/entries/${id}`),
  update: (id: string, data: any) => api.patch(`/entries/${id}`, data),
  delete: (id: string) => api.delete(`/entries/${id}`),
}

export const planningApi = {
  getToday: () => api.get('/planning/today'),
  generate: () => api.post('/planning/today'),
  generateToday: () => api.post('/planning/today'),
  weeklyReview: () => api.get('/planning/weekly-review'),
}

export const usersApi = {
  me: () => api.get('/users/me'),
  deleteAccount: (confirmation: string) => api.delete('/users/me', { params: { confirmation } }),
  exportData: () => api.get('/users/me/export'),
}

export const adminApi = {
  listUsers: (params?: { skip?: number; limit?: number; search?: string }, adminKey?: string) =>
    api.get('/admin/users', { params: { ...params, admin_key: adminKey } }),
  getUser: (userId: string, adminKey: string) =>
    api.get(`/admin/users/${userId}`, { params: { admin_key: adminKey } }),
  deleteUser: (userId: string, adminKey: string) =>
    api.delete(`/admin/users/${userId}`, { params: { admin_key: adminKey } }),
  resetUser: (userId: string, resetType: string, adminKey: string) =>
    api.post(`/admin/users/${userId}/reset`, null, { params: { reset_type: resetType, admin_key: adminKey } }),
  stats: (adminKey: string) =>
    api.get('/admin/stats', { params: { admin_key: adminKey } }),
}

export const ifThenApi = {
  getPlans: (goalId: string) => api.get(`/if-then/goals/${goalId}/plans`),
  createPlan: (goalId: string, data: { when_trigger: string; then_action: string; obstacle_type?: string; is_primary?: boolean }) =>
    api.post(`/if-then/goals/${goalId}/plans`, data),
  updatePlan: (planId: string, data: { when_trigger?: string; then_action?: string; is_active?: boolean }) =>
    api.patch(`/if-then/plans/${planId}`, data),
  deletePlan: (planId: string) => api.delete(`/if-then/plans/${planId}`),
  logUse: (planId: string, data: { was_triggered?: boolean; was_used?: boolean; was_effective?: boolean; context?: string; notes?: string }) =>
    api.post(`/if-then/plans/${planId}/log`, data),
  getEffectiveness: (planId: string) => api.get(`/if-then/plans/${planId}/effectiveness`),
  getUserSummary: () => api.get('/if-then/user/summary'),
}

export const reflectionApi = {
  getWeekly: () => api.get('/planning/weekly-review'),
}

export const notificationsApi = {
  getNudges: () => api.get('/snapshots/nudges'),
}

export default api
