<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px">
      <div style="display: flex; justify-content: space-between; align-items: center; gap: 16px">
        <div>
          <div style="font-size: 18px; color: #333">欢迎您：{{ userInfo?.name || '同学' }}</div>
          <div style="font-size: 14px; color: #999; margin-top: 8px">
            欢迎使用实验室预约系统，当前身份：{{ userInfo.role === 'student' ? '学生' : '管理员' }}
          </div>
        </div>

        <el-button type="primary" @click="router.push('/manager/ai-chat')">打开AI助手</el-button>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <div style="display: flex; align-items: center; gap: 50px">
        <div>
          开放的实验室 <b style="margin-left: 5px; font-size: 18px">{{ openLabCount }}</b>
        </div>
        <div>
          与我相关的预约 <b style="margin-left: 5px; font-size: 18px">{{ reservationCount }}</b>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header>
        <div style="font-size: 16px">
          <span>快捷入口</span>
        </div>
      </template>
      <div style="display: flex; flex-wrap: wrap; gap: 32px">
        <router-link
          v-for="(item, index) in shortcuts"
          :key="index"
          style="color: #409eff"
          :to="item.path"
          >{{ item.label }}</router-link
        >
      </div>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header>
        <div style="font-size: 16px; display: flex; align-items: center">
          <span>最新公告</span>
          <router-link to="/manager/announcements" style="margin-left: auto; font-size: 13px">
            查看全部 →
          </router-link>
        </div>
      </template>
      <div v-if="!announcements.length" style="color: #c0c4cc; font-size: 13px">暂无公告</div>
      <div v-for="item in announcements" :key="item.id" class="notice-item">
        <span class="notice-title">{{ item.title }}</span>
        <span class="notice-meta">
          <template v-if="userInfo?.role === 'admin'">{{ item.author_name || '管理员' }} · </template>
          {{ (item.create_time || '').slice(0, 10) }}
        </span>
      </div>
    </el-card>

    <div style="margin-bottom: 16px">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" v-for="(item, index) in features" :key="index">
          <el-card shadow="hover" class="feature-card" @click="openFeature(item)">
            <div style="padding: 10px; display: flex; flex-direction: column; height: 100%">
              <div style="font-size: 16px; font-weight: 600; color: #333">{{ item.title }}</div>
              <div
                style="
                  margin-top: 8px;
                  color: #666;
                  font-size: 13px;
                  line-height: 1.6;
                  min-height: 40px;
                "
              >
                {{ item.desc }}
              </div>
              <div class="feature-go">{{ item.action }} →</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { getLabPageList } from '@/api/lab'
import { getReservationPageList } from '@/api/reservation'
import { getAnnouncementsApi } from '@/api/announcement'
import router from '@/router'
import { useUser } from '@/utils/user'
import { onMounted } from 'vue'

const { userInfo } = useUser()
const openLabCount = ref(0)
const reservationCount = ref(0)
const announcements = ref([])

const features = computed(() => {
  const isStudent = userInfo.value?.role === 'student'
  return [
    {
      title: '业务预约',
      desc: '实验室 / 设备浏览、提交预约、我的预约和管理员审核',
      action: isStudent ? '去预约' : '去审核',
      path: isStudent ? '/manager/lablist' : '/manager/audit-reservation'
    },
    {
      title: '知识库问答',
      desc: 'RAG 检索规则和开放时间等文档，回答有依据',
      action: '去提问',
      path: '/manager/ai-chat',
      query: { q: '实验室的预约规则、开放时间和安全规范分别是什么？' }
    },
    {
      title: '智能 Agent',
      desc: '根据用户输入的自然语言主动进行 Tool Call 和节点编排循环调用，可以查库，流式对话，确认表单提交',
      action: '去试试',
      path: '/manager/ai-chat',
      query: { q: '帮我查一下现在有哪些开放的实验室' }
    }
  ]
})

const openFeature = (item) => {
  if (item.query) {
    router.push({ path: item.path, query: item.query })
  } else {
    router.push(item.path)
  }
}

const shortcuts = computed(() => {
  if (userInfo.value.role === 'student') {
    return [
      { label: 'AI 智能助手', path: '/manager/ai-chat' },
      { label: '实验室列表', path: '/manager/lablist' },
      { label: '我的预约', path: '/manager/my-reservation' }
    ]
  }
  return [
    { label: '实验室列表', path: '/manager/lablist' },
    { label: '我的预约', path: '/manager/my-reservation' },
    { label: '预约审核', path: '/manager/audit-reservation' },
    { label: '实验室管理', path: '/manager/lab' },
    { label: '设备管理', path: '/manager/equipment' },
    { label: '用户管理', path: '/manager/user' }
  ]
})

onMounted(async () => {
  try {
    const res = await getLabPageList({ page: 1, page_size: 1, status: 1 })
    if (res.code === 200) openLabCount.value = res.data?.total || 0
  } catch {
    openLabCount.value = 0
  }
  try {
    const res = await getReservationPageList({ page: 1, page_size: 1 })
    if (res.code === 200) reservationCount.value = res.data?.total || 0
  } catch {
    reservationCount.value = 0
  }
  try {
    const res = await getAnnouncementsApi(3)
    if (res.code === 200) announcements.value = res.data || []
  } catch {
    announcements.value = []
  }
})
</script>

<style scoped>
.notice-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: 13px;
}
.notice-title {
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notice-meta {
  margin-left: auto;
  color: #909399;
  font-size: 12px;
  flex-shrink: 0;
}
.feature-card {
  cursor: pointer;
  transition: transform 0.15s ease;
}
.feature-card:hover {
  transform: translateY(-2px);
}
.feature-go {
  margin-top: 12px;
  font-size: 12.5px;
  color: var(--el-color-primary);
  text-align: right;
}
</style>
