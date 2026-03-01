import request from '@/utils/request'

export function globalSearch(query) {
  return request({
    url: '/api/search/global/',
    method: 'get',
    params: { q: query }
  })
} 