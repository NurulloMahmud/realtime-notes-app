import client from './client'
import axios from 'axios'

export async function register(email, username, password) {
  const { data } = await axios.post('/api/auth/register', { email, username, password })
  return data
}

export async function login(email, password) {
  const { data } = await axios.post('/api/auth/login', { email, password })
  return data
}

export async function getMe() {
  const { data } = await client.get('/auth/me')
  return data
}
