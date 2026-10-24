import request from '@/utils/request'

/** 我自己的配置 + 当前生效来源 */
export function getMyAIConfig() {
  return request({ url: '/api/ai/config/me', method: 'get' })
}

/** 新增/覆盖我自己的配置（api_key 不传表示沿用原来的） */
export function saveMyAIConfig(data) {
  return request({ url: '/api/ai/config/me', method: 'put', data })
}

/** 删除我自己的配置 */
export function deleteMyAIConfig() {
  return request({ url: '/api/ai/config/me', method: 'delete' })
}

/** 全部配置（主管理员看全部，其他人只看到自己 + 默认） */
export function getAIConfigList() {
  return request({ url: '/api/ai/config/list', method: 'get' })
}

/** 主管理员：设置系统默认 */
export function saveDefaultAIConfig(data) {
  return request({ url: '/api/ai/config/default', method: 'post', data })
}

/** 主管理员：把某条配置设为默认 */
export function promoteAIConfig(id) {
  return request({ url: `/api/ai/config/${id}/promote`, method: 'post' })
}

/** 主管理员：启用/停用 */
export function setAIConfigStatus(id, status) {
  return request({ url: `/api/ai/config/${id}/status`, method: 'put', params: { status } })
}

/** 主管理员：删除某条配置 */
export function deleteAIConfig(id) {
  return request({ url: `/api/ai/config/${id}`, method: 'delete' })
}
