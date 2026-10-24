<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold; display: flex; align-items: center">
          <span>管理员申请</span>
          <el-tag v-if="total > 0" type="warning" style="margin-left: 10px">
            待审核 {{ total }} 条
          </el-tag>
          <el-button size="small" style="margin-left: auto" @click="load">刷新</el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 14px">
        通过后对方会变成管理员，可用「管理员登录」进入后台；拒绝则保留为学生账号并启用。
        审核结果都会给对方发一条站内通知。
      </el-alert>

      <el-table :data="rows" v-loading="loading" style="width: 100%">
        <el-table-column prop="username" label="账号" width="150" />
        <el-table-column prop="name" label="姓名" width="150" />
        <el-table-column prop="email" label="邮箱" min-width="160">
          <template #default="{ row }">{{ row.email || '-' }}</template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140">
          <template #default="{ row }">{{ row.phone || '-' }}</template>
        </el-table-column>
        <el-table-column label="申请说明" min-width="240">
          <template #default="{ row }">
            <span v-if="row.apply_note">{{ row.apply_note }}</span>
            <span v-else style="color: #c0c4cc">（未填写）</span>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="170">
          <template #default="{ row }">{{ formatTime(row.apply_time || row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="success" text bg @click="handleAudit(row, true)">通过</el-button>
            <el-button type="danger" text bg @click="handleAudit(row, false)">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && rows.length === 0" class="empty">
        目前没有待审核的管理员申请
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { auditAdminApplicationApi, getAdminApplications } from '@/api/user'

const rows = ref([])
const total = ref(0)
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    const res = await getAdminApplications()
    if (res.code === 200) {
      rows.value = res.data?.list || []
      total.value = res.data?.total || 0
    }
  } finally {
    loading.value = false
  }
}

const formatTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`
}

const handleAudit = (row, approve) => {
  const action = approve ? '通过' : '拒绝'
  const tip = approve
    ? `通过「${row.name}」的管理员申请？通过后对方可以用「管理员登录」进入后台。`
    : `拒绝「${row.name}」的申请？账号会保留为普通学生并启用。`
  ElMessageBox.confirm(tip, `${action}申请`, { type: 'warning' })
    .then(async () => {
      const res = await auditAdminApplicationApi(row.id, approve)
      if (res.code === 200) {
        ElMessage.success(approve ? '已通过' : '已拒绝')
        load()
      }
    })
    .catch(() => {})
}

onMounted(load)
</script>

<style scoped>
.empty {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 24px 0;
}
</style>
