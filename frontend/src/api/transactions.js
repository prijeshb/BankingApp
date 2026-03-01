import client from './client'

export const listTransactions = (
  accountId,
  { page = 1, limit = 20, start_date, end_date } = {}
) => {
  const params = { page, limit }
  if (start_date) params.start_date = start_date
  if (end_date)   params.end_date   = end_date
  return client.get(`/accounts/${accountId}/transactions/`, { params })
}

export const getTransaction = (accountId, transactionId) =>
  client.get(`/accounts/${accountId}/transactions/${transactionId}`)
