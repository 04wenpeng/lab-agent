import request from '@/utils/request'

/**
 * 分页模糊查询列表
 */
export function getLabPageList(params) {
  return request({
    url: '/api/lab/list',
    method: 'get',
    params
  })
}

/**
 * 根据ID查询实验室详情
 * @param {Number} lab_id
 * @returns
 */
export function getLab(lab_id) {
  return request({
    url: `/api/lab/${lab_id}`,
    method: 'get'
  })
}

/**
 * 新增
 */
export function createLabApi(data) {
  return request({
    url: '/api/lab',
    method: 'post',
    data
  })
}

/**
 * 修改
 */
export function updateLabApi(labId, data) {
  return request({
    url: `/api/lab/${labId}`,
    method: 'put',
    data
  })
}

/**
 * 删除
 */
export function deleteLabApi(labId) {
  return request({
    url: `/api/lab/${labId}`,
    method: 'delete'
  })
}

/**
 * 保存某个实验室的设备清单（整份列表提交，后端按 id 增/改/删）
 */
export function saveLabEquipmentsApi(labId, equipments) {
  return request({
    url: `/api/lab/${labId}/equipments`,
    method: 'put',
    data: { equipments }
  })
}
