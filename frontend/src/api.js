import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
})

export const getOverview = () => api.get('/overview').then((r) => r.data)
export const getCases = () => api.get('/cases').then((r) => r.data)
export const getTransactions = (caseId) =>
  api
    .get('/transactions', { params: caseId ? { case_id: caseId } : {} })
    .then((r) => r.data)
export const getGraph = (caseIds) =>
  api
    .get('/graph', {
      params: { cases: Array.isArray(caseIds) ? caseIds.join(',') : caseIds },
    })
    .then((r) => r.data)
export const discoverConnections = () =>
  api.post('/discover-connections').then((r) => r.data)
export const comparePatterns = () =>
  api.post('/compare-patterns').then((r) => r.data)
export const getMoneyTrail = (caseId) =>
  api.get(`/money-trail/${caseId}`).then((r) => r.data)
export const simulateRisk = (txs) =>
  api.post('/simulate-risk', txs).then((r) => r.data)
export const uploadTransactions = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api
    .post('/upload-transactions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}

export default api
