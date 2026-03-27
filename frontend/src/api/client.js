import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = null

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true

      if (!refreshing) {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          localStorage.clear()
          window.location.href = '/login'
          return Promise.reject(error)
        }
        refreshing = axios
          .post('/api/auth/refresh', { refresh_token: refreshToken })
          .then(({ data }) => {
            localStorage.setItem('access_token', data.access_token)
            localStorage.setItem('refresh_token', data.refresh_token)
            return data.access_token
          })
          .catch(() => {
            localStorage.clear()
            window.location.href = '/login'
            return Promise.reject(error)
          })
          .finally(() => {
            refreshing = null
          })
      }

      const newToken = await refreshing
      original.headers.Authorization = `Bearer ${newToken}`
      return client(original)
    }
    return Promise.reject(error)
  }
)

export default client
