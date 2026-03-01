import client from './client'

export const listAccounts  = ()          => client.get('/accounts/')
export const getAccount    = (id)        => client.get(`/accounts/${id}`)
export const createAccount = (account_type, currency) =>
  client.post('/accounts/', { account_type, currency })
export const deleteAccount = (id)        => client.delete(`/accounts/${id}`)
export const deposit       = (id, amount, description) =>
  client.post(`/accounts/${id}/deposit`, { amount, description })
export const withdraw      = (id, amount, description) =>
  client.post(`/accounts/${id}/withdraw`, { amount, description })
