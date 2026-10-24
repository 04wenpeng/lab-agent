<template>
  <div>
    <el-container style="min-height: 100vh">
      <el-header
        style="
          display: flex;
          align-items: center;
          border-bottom: 1px solid #ddd;
          background-color: #fff;
        "
      >
        <el-button v-if="isMobile" class="menu-toggle" text @click="drawerVisible = true">
          <el-icon :size="20"><Expand /></el-icon>
        </el-button>
        <div
          class="app-title"
          style="flex: 1; display: flex; align-items: center; font-size: 24px; font-weight: bold"
        >
          <img style="width: 40px" src="@/assets/imgs/logo.png" alt="" />
          <div class="app-title-text" style="margin-left: 5px">智能实验室预约系统</div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px">
          <el-popover
            ref="notifyPopover"
            placement="bottom-end"
            :width="notifyWidth"
            trigger="click"
            @show="loadNotifications"
          >
            <template #reference>
              <el-badge :value="unread" :hidden="unread === 0" :max="99" style="margin-right: 6px">
                <el-icon :size="19" style="cursor: pointer; color: #606266"><Bell /></el-icon>
              </el-badge>
            </template>
            <div class="notify-head">
              <span style="font-weight: 600">消息通知</span>
              <el-button link type="primary" size="small" @click="readAll">全部已读</el-button>
            </div>
            <div class="notify-list">
              <div
                v-for="item in notifications"
                :key="item.id"
                class="notify-item"
                :class="{ unread: item.is_read === 0 }"
                @click="openNotify(item)"
              >
                <div class="notify-title">{{ item.title }}</div>
                <div class="notify-content">{{ item.content }}</div>
                <div class="notify-time">{{ formatTime(item.create_time) }}</div>
              </div>
              <div v-if="!notifications.length" class="notify-empty">暂无消息</div>
            </div>
            <div class="notify-foot" @click="goNotifyPage">查看全部通知 →</div>
          </el-popover>
          <el-dropdown @command="handleCommand">
            <div style="display: flex; align-items: center; cursor: pointer">
              <img :src="userInfo?.avatar" alt="" style="width: 30px; border-radius: 50%" />
              <div class="user-name-text" style="margin-left: 3px">{{ userInfo?.name }}</div>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button class="logout-btn" text @click="handleLogout">
            <el-icon style="margin-right: 4px"><SwitchButton /></el-icon>
            <span class="logout-text">退出登录</span>
          </el-button>
        </div>
      </el-header>
      <el-container>
        <el-aside v-if="!isMobile" width="220px">
          <el-menu router :default-active="activePath" style="height: 100%">
            <el-menu-item v-for="item in visibleMenus" :key="item.path" :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
              <span v-if="item.count > 0" class="menu-count">
                {{ item.count > 99 ? '99+' : item.count }}
              </span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <!-- 手机端：侧边菜单改成抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      size="230px"
      :with-header="false"
      class="mobile-drawer"
    >
      <el-menu router :default-active="activePath" @select="drawerVisible = false">
        <el-menu-item v-for="item in visibleMenus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
          <span v-if="item.count > 0" class="menu-count">
            {{ item.count > 99 ? '99+' : item.count }}
          </span>
        </el-menu-item>
      </el-menu>
    </el-drawer>
  </div>
</template>

<script setup>
import router from '@/router'
import { logout } from '@/utils/auth'
import { useUser } from '@/utils/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import {
  getUnreadCount,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead
} from '@/api/notification'
import { getAdminApplicationCount } from '@/api/user'
import {
  Menu as IconMenu,
  House,
  Setting,
  User,
  OfficeBuilding,
  Tickets,
  DocumentChecked,
  ChatDotRound,
  ChatLineSquare,
  DataLine,
  Document,
  Key,
  Bell,
  Stamp,
  Box,
  Expand,
  SwitchButton
} from '@element-plus/icons-vue'

const { userInfo } = useUser()

// ===== 手机端适配：宽度小于 768 时侧边栏收进抽屉 =====
const isMobile = ref(window.innerWidth < 768)
const drawerVisible = ref(false)
const notifyWidth = computed(() => (isMobile.value ? Math.min(window.innerWidth - 24, 340) : 360))
const onResize = () => {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) drawerVisible.value = false
}

const activePath = computed(() => router.currentRoute.value.path)

// 主管理员的「管理员申请」菜单角标
const pendingApplyCount = ref(0)

// 菜单配置：桌面侧栏和手机抽屉共用一份
const visibleMenus = computed(() => {
  const role = userInfo.value?.role
  const primary = userInfo.value?.is_primary === true
  const menus = [
    { path: '/manager/home', label: '系统首页', icon: IconMenu, show: true },
    { path: '/manager/announcements', label: '公告', icon: ChatLineSquare, show: true },
    { path: '/manager/ai-chat', label: 'AI智能助手', icon: ChatDotRound, show: true },
    { path: '/manager/lablist', label: '实验室列表', icon: OfficeBuilding, show: true },
    { path: '/manager/my-reservation', label: '我的预约', icon: Tickets, show: true },
    { path: '/manager/lab', label: '实验室管理', icon: House, show: role === 'admin' },
    { path: '/manager/equipment', label: '设备列表管理', icon: Setting, show: role === 'admin' },
    { path: '/manager/equipment-catalog', label: '设备库', icon: Box, show: role === 'admin' },
    {
      path: '/manager/audit-reservation',
      label: '预约审核',
      icon: DocumentChecked,
      show: role === 'admin'
    },
    { path: '/manager/user', label: '用户管理', icon: User, show: role === 'admin' },
    {
      path: '/manager/admin-apply',
      label: '管理员申请',
      icon: Stamp,
      show: primary,
      count: pendingApplyCount.value
    },
    { path: '/manager/ai-config', label: 'AI 模型配置', icon: Key, show: primary },
    { path: '/manager/settings', label: '系统设置', icon: Setting, show: role === 'admin' },
    { path: '/manager/stats', label: '统计报表', icon: DataLine, show: role === 'admin' },
    { path: '/manager/logs', label: '操作日志', icon: Document, show: primary }
  ]
  return menus.filter((m) => m.show)
})

const loadPendingApply = async () => {
  if (userInfo.value?.is_primary !== true) return
  try {
    const res = await getAdminApplicationCount()
    if (res.code === 200) pendingApplyCount.value = res.data || 0
  } catch {
    /* ignore */
  }
}

// ===== 站内通知 =====
const unread = ref(0)
const notifications = ref([])
const notifyPopover = ref(null)
let notifyTimer = null

const loadUnread = async () => {
  try {
    const res = await getUnreadCount()
    if (res.code === 200) unread.value = res.data || 0
  } catch {
    /* 通知失败不影响主流程 */
  }
}

const loadNotifications = async () => {
  try {
    const res = await getNotifications({ page: 1, page_size: 8 })
    if (res.code === 200) {
      notifications.value = res.data?.list || []
      unread.value = res.data?.unread || 0
    }
  } catch {
    /* ignore */
  }
}

const goNotifyPage = () => {
  notifyPopover.value?.hide()
  router.push('/manager/notifications')
}

const openNotify = async (item) => {
  if (item.is_read === 0) {
    try {
      await markNotificationRead(item.id)
      item.is_read = 1
      unread.value = Math.max(0, unread.value - 1)
    } catch {
      /* ignore */
    }
  }
  notifyPopover.value?.hide()
  // 后端给了跳转路由就跳过去（预约相关 → 我的预约，管理员申请 → 申请页）
  const target = item.link || (item.reservation_id ? '/manager/my-reservation' : '')
  if (target) router.push(target)
}

const readAll = async () => {
  const res = await markAllNotificationsRead()
  if (res.code === 200) {
    notifications.value = notifications.value.map((n) => ({ ...n, is_read: 1 }))
    unread.value = 0
    ElMessage.success('已全部标记为已读')
  }
}

const formatTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getMonth() + 1}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(
    date.getMinutes()
  )}`
}

onMounted(() => {
  loadUnread()
  loadPendingApply()
  window.addEventListener('resize', onResize)
  notifyTimer = setInterval(() => {
    loadUnread()
    loadPendingApply()
  }, 30000)
})

onBeforeUnmount(() => {
  if (notifyTimer) clearInterval(notifyTimer)
  window.removeEventListener('resize', onResize)
})

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/manager/profile')
  } else if (command === 'password') {
    router.push('/manager/password')
  }
}

// 顶栏直接退出登录（不再藏在下拉菜单里）
const handleLogout = () => {
  ElMessageBox.confirm('确认退出登录？', '提示', {
    type: 'warning',
    confirmButtonText: '退出',
    cancelButtonText: '取消'
  })
    .then(() => {
      logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    })
    .catch(() => {})
}
</script>

<style scoped>
.logout-btn {
  color: #606266;
}
.logout-btn:hover {
  color: var(--el-color-danger);
  background-color: transparent;
}

.notify-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.notify-list {
  max-height: 320px;
  overflow-y: auto;
}
.notify-item {
  padding: 8px 8px;
  border-bottom: 1px solid #f2f3f5;
  cursor: pointer;
  border-radius: 4px;
}
.notify-item:hover {
  background: #f7f9ff;
}
.notify-item.unread {
  background: #f0f6ff;
}
.notify-item.unread .notify-title {
  font-weight: 600;
}
.notify-title {
  font-size: 13px;
  color: #333;
}
.notify-content {
  font-size: 12px;
  color: #666;
  margin-top: 3px;
  line-height: 1.5;
}
.notify-time {
  font-size: 11px;
  color: #aaa;
  margin-top: 4px;
}
.notify-empty {
  text-align: center;
  color: #aaa;
  font-size: 12px;
  padding: 18px 0;
}
.notify-foot {
  margin-top: 6px;
  text-align: center;
  font-size: 12px;
  color: var(--el-color-primary);
  cursor: pointer;
  padding-top: 8px;
  border-top: 1px solid #f2f3f5;
}
.notify-foot:hover {
  text-decoration: underline;
}

/* 菜单右侧的小红点数字（用 span 而不是 el-badge，badge 会换行掉到文字下面） */
.menu-count {
  margin-left: auto;
  background: #f56c6c;
  color: #fff;
  font-size: 11px;
  line-height: 16px;
  height: 16px;
  min-width: 16px;
  padding: 0 5px;
  border-radius: 8px;
  text-align: center;
  font-weight: 500;
}
</style>
