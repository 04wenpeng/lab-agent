import request from '@/utils/request'

/**
 * 创建预约
 */
export function createReservationApi(data) {
  return request({
    url: '/api/reservation',
    method: 'post',
    data
  })
}

/**
 * 查询预约记录
 */
export function getReservationPageList(params) {
  return request({
    url: '/api/reservation/list',
    method: 'get',
    params
  })
}

/**
 * 取消预约
 */
export function cancelReservationApi(id) {
  return request({
    url: `/api/reservation/${id}/cancel`,
    method: 'put'
  })
}

/**
 * 单条预约详情（本人或管理员）
 */
export function getReservationDetailApi(id) {
  return request({
    url: `/api/reservation/${id}/detail`,
    method: 'get'
  })
}

/**
 * 学生自己改预约（只能改还没开始的，有次数上限）
 */
export function modifyReservationApi(id, data) {
  return request({
    url: `/api/reservation/${id}/modify`,
    method: 'put',
    data
  })
}

/**
 * 签到（已通过的预约，开始前 30 分钟到结束之间）
 */
export function checkInReservationApi(id) {
  return request({
    url: `/api/reservation/${id}/check-in`,
    method: 'put'
  })
}

/**
 * 审核预约
 */
export function auditReservationApi(id, status) {
  return request({
    url: `/api/reservation/${id}/audit`,
    method: 'put',
    data: { status }
  })
}

/**
 * 管理员强制取消（待审核 / 已通过都可以）
 */
export function adminCancelReservationApi(id, reason) {
  return request({
    url: `/api/reservation/${id}/admin-cancel`,
    method: 'put',
    data: { reason }
  })
}

/**
 * 管理员调整预约时间
 */
export function adminRescheduleReservationApi(id, data) {
  return request({
    url: `/api/reservation/${id}/admin-reschedule`,
    method: 'put',
    data
  })
}
