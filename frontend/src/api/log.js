import request from '@/utils/request'

/** 操作日志（主管理员） */
export function getLogListApi(params) {
  return request({ url: '/api/log/list', method: 'get', params })
}
