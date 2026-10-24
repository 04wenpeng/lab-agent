import request from '@/utils/request'

/** 设备库列表（登录后都能看） */
export function getCatalogList(params) {
  return request({ url: '/api/equipment-catalog/list', method: 'get', params })
}

/** 新增设备库条目 */
export function createCatalogApi(data) {
  return request({ url: '/api/equipment-catalog', method: 'post', data })
}

/** 修改设备库条目 */
export function updateCatalogApi(id, data) {
  return request({ url: `/api/equipment-catalog/${id}`, method: 'put', data })
}

/** 删除设备库条目 */
export function deleteCatalogApi(id) {
  return request({ url: `/api/equipment-catalog/${id}`, method: 'delete' })
}
