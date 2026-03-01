import client from './client'

export const register = (email, password, full_name) =>
  client.post('/auth/register', { email, password, full_name })

export const login = (email, password) =>
  client.post('/auth/login', { email, password })

export const refresh = (refresh_token) =>
  client.post('/auth/refresh', { refresh_token })

export const logout = (refresh_token) =>
  client.post('/auth/logout', { refresh_token })

export const getMe = () => client.get('/users/me')

export const updateMe = (payload) => client.put('/users/me', payload)
