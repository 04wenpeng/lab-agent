import request from '@/utils/request'

/** 统计报表（管理员）*/
export function getStatsApi(days = 30) {
  return request({ url: '/api/stats/overview', method: 'get', params: { days } })
}
