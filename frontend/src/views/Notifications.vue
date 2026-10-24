<template>
  <div class="notify-page">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="page-head">
          <div class="head-text">
            <h2>消息通知</h2>
            <p>预约审核结果、管理员申请、违约提醒都会在这里留档</p>
          </div>
          <div class="head-actions">
            <el-radio-group v-model="filter" size="small" @change="reload">
              <el-radio-button value="all">全部</el-radio-button>
              <el-radio-button value="unread">未读</el-radio-button>
            </el-radio-group>
            <el-button size="small" :disabled="!unread" @click="readAll">全部已读</el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading">
        <el-empty v-if="!loading && !rows.length" description="还没有通知" />
        <div
          v-for="item in rows"
          :key="item.id"
          class="notify-item"
          :class="{ unread: item.is_read === 0 }"
          @click="openItem(item)"
        >
          <span class="dot" v-if="item.is_read === 0"></span>
          <div class="body">
            <div class="line">
              <span class="title">{{ item.title }}</span>
              <span class="time">{{ formatTime(item.create_time) }}</span>
            </div>
            <div class="content">{{ item.content }}</div>
          </div>
        </div>
      </div>

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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead
} from '@/api/notification'

const router = useRouter()
const rows = ref([])
const total = ref(0)
const unread = ref(0)
const page = ref(1)
const pageSize = ref(10)
const filter = ref('all')
const loading = ref(false)

const formatTime = (value) => {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const load = async () => {
  loading.value = true
  try {
    const res = await getNotifications({
      page: page.value,
      page_size: pageSize.value,
      unread_only: filter.value === 'unread'
    })
    if (res.code === 200) {
      rows.value = res.data?.list || []
      total.value = res.data?.total || 0
      unread.value = res.data?.unread || 0
    }
  } finally {
    loading.value = false
  }
}

const reload = () => {
  page.value = 1
  load()
}

const readAll = async () => {
  await markAllNotificationsRead()
  ElMessage.success('已全部标记为已读')
  load()
}

const openItem = async (item) => {
  if (item.is_read === 0) {
    try {
      await markNotificationRead(item.id)
      item.is_read = 1
      unread.value = Math.max(0, unread.value - 1)
    } catch {}
  }
  const target = item.link || (item.reservation_id ? '/manager/my-reservation' : '')
  if (target) router.push(target)
}

onMounted(load)
</script>

<style scoped>
.notify-page {
  max-width: 920px;
  margin: 0 auto;
}
.page-card {
  border-radius: 10px;
}
.page-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.head-text h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
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
  align-items: center;
}

.notify-item {
  display: flex;
  gap: 10px;
  padding: 14px 6px;
  border-bottom: 1px solid #f5f7fa;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}
.notify-item:last-child {
  border-bottom: none;
}
.notify-item:hover {
  background: #fafbfc;
}
.notify-item.unread {
  background: #f6faff;
}
.notify-item.unread:hover {
  background: #eef6ff;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f56c6c;
  margin-top: 8px;
  flex-shrink: 0;
}
.body {
  flex: 1;
  min-width: 0;
}
.line {
  display: flex;
  gap: 10px;
}
.title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.time {
  margin-left: auto;
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.content {
  margin-top: 4px;
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
