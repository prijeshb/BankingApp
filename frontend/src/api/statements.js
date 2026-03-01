import client from './client'

export const getStatement = (accountId, start_date, end_date) =>
  client.get(`/accounts/${accountId}/statements/`, {
    params: { start_date, end_date },
  })
