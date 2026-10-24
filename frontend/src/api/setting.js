import request from '@/utils/request'

/** 读取预约规则（所有人可读） */
export function getReservationRulesApi() {
  return request({ url: '/api/setting/reservation-rules', method: 'get' })
}

/** 修改预约规则（管理员） */
export function updateReservationRulesApi(data) {
  return request({ url: '/api/setting/reservation-rules', method: 'put', data })
}
