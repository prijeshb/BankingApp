import client from './client'

export const listCards        = (accountId)        => client.get(`/accounts/${accountId}/cards`)
export const getCard          = (cardId)            => client.get(`/cards/${cardId}`)
export const issueCard        = (accountId, card_type) =>
  client.post(`/accounts/${accountId}/cards`, { card_type })
export const updateCardStatus = (cardId, status)   =>
  client.patch(`/cards/${cardId}/status`, { status })
export const deleteCard       = (cardId)            => client.delete(`/cards/${cardId}`)
export const revealCard       = (cardId, password)  => client.post(`/cards/${cardId}/reveal`, { password })
