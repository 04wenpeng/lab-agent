import request from '@/utils/request'

/** 公告列表（所有人可见，返回里带 can_delete / can_edit） */
export function getAnnouncementsApi(limit = 50) {
  return request({ url: '/api/announcement/list', method: 'get', params: { limit } })
}

/** 发布公告（管理员） */
export function createAnnouncementApi(data) {
  return request({ url: '/api/announcement', method: 'post', data })
}

/** 编辑公告：作者本人或主管理员 */
export function updateAnnouncementApi(id, data) {
  return request({ url: `/api/announcement/${id}`, method: 'put', data })
}

/** 删除公告：主管理员可删任意，普通管理员只能删自己的 */
export function deleteAnnouncementApi(id) {
  return request({ url: `/api/announcement/${id}`, method: 'delete' })
}
