<template>
  <div class="log-page">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="page-head">
          <div class="head-text">
            <h2>
              操作日志
              <span class="count-badge">{{ total }}</span>
            </h2>
            <p>记录所有增删改操作：谁、什么时候、做了什么</p>
          </div>
          <div class="head-actions">
            <el-input
              v-model="keywords"
              placeholder="搜索操作人 / 动作 / 路径"
              style="width: 230px"
              clearable
              :prefix-icon="Search"
              @keyup.enter="reload"
              @clear="reload"
            />
            <el-button @click="reload">查询</el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="rows"
        v-loading="loading"
        style="width: 100%"
        :header-cell-style="{ backgroundColor: '#fafbfc', color: '#909399', fontWeight: 500 }"
      >
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            <span class="time">{{ formatTime(row.create_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作人" width="140">
          <template #default="{ row }">
            <span class="who">{{ row.username }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-tag size="small" :type="tagType(row.action)" effect="light">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="请求" min-width="260">
          <template #default="{ row }">
            <span class="method">{{ row.method }}</span>
            <span class="path">{{ row.path }}</span>
          </template>
        </el-table-column>
        <el-table-column label="结果" width="90">
          <template #default="{ row }">
            <span :class="['result', row.status_code < 400 ? 'ok' : 'fail']">
              {{ row.status_code }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="来源 IP" width="130">
          <template #default="{ row }">
            <span class="ip">{{ row.ip || '-' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          background
          layout="total, prev, pager, next"
          @current-change="load"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getLogListApi } from '@/api/log'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keywords = ref('')
const loading = ref(false)

const formatTime = (value) => {
  if (!value) return '-'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const tagType = (action) => {
  if (action.includes('删除')) return 'danger'
  if (action.includes('审核') || action.includes('重置') || action.includes('登录')) return 'warning'
  if (action.includes('新增') || action.includes('发布') || action.includes('注册')) return 'success'
  return 'info'
}

const load = async () => {
  loading.value = true
  try {
    const res = await getLogListApi({
      page: page.value,
      page_size: pageSize.value,
      keywords: keywords.value || undefined
    })
    if (res.code === 200) {
      rows.value = res.data?.list || []
      total.value = res.data?.total || 0
    }
  } finally {
    loading.value = false
  }
}

const reload = () => {
  page.value = 1
  load()
}

onMounted(load)
</script>

<style scoped>
.log-page {
  max-width: 1180px;
  margin: 0 auto;
}
.page-card {
  border-radius: 10px;
}
.page-head {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}
.head-text h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}
.count-badge {
  font-size: 12px;
  font-weight: 500;
  color: var(--el-color-primary);
  background: #ecf5ff;
  border-radius: 10px;
  padding: 1px 9px;
}
.head-text p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #909399;
}
.head-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.time {
  font-size: 12px;
  color: #909399;
}
.who {
  font-size: 13px;
  color: #303133;
}
.method {
  font-size: 11px;
  color: #909399;
  background: #f4f6f8;
  border-radius: 4px;
  padding: 1px 6px;
  margin-right: 8px;
}
.path {
  font-size: 12px;
  color: #606266;
  font-family: Consolas, Monaco, monospace;
}
.result {
  font-size: 12px;
  font-weight: 600;
}
.result.ok {
  color: #67c23a;
}
.result.fail {
  color: #f56c6c;
}
.ip {
  font-size: 12px;
  color: #a8abb2;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
