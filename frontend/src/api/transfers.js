import client from './client'

export const createTransfer = (payload) => client.post('/transfers', payload)
export const getTransfer    = (id)      => client.get(`/transfers/${id}`)
