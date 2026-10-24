import request from '@/utils/request'

export function getNotifications(params) {
  return request({ url: '/api/notification/list', method: 'get', params })
}

export function getUnreadCount() {
  return request({ url: '/api/notification/unread-count', method: 'get' })
}

export function markNotificationRead(id) {
  return request({ url: `/api/notification/${id}/read`, method: 'put' })
}

export function markAllNotificationsRead() {
  return request({ url: '/api/notification/read-all', method: 'put' })
}
