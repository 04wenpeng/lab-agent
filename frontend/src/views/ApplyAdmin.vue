<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">申请成为管理员</div>
      </template>

      <template v-if="isAdmin">
        <el-result
          icon="success"
          title="你已经是管理员了"
          sub-title="左侧菜单已经可以使用实验室管理、设备管理、预约审核等功能"
        />
      </template>

      <template v-else-if="pending">
        <el-result
          icon="info"
          title="申请已提交，等待主管理员审核"
          sub-title="审核通过后重新登录，就能用「管理员登录」进入后台"
        />
        <div style="text-align: center; margin-top: 6px">
          <el-button @click="refresh">刷新状态</el-button>
        </div>
      </template>

      <template v-else-if="inCooldown">
        <el-result
          icon="warning"
          title="上次申请未通过"
          :sub-title="`可以在 ${retryDateText} 之后再次申请（还有约 ${remainDays} 天）`"
        />
        <div style="text-align: center; margin-top: 6px">
          <el-button @click="refresh">刷新状态</el-button>
        </div>
      </template>

      <template v-else>
        <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
          提交后由主管理员审核，审核期间你仍然可以正常预约实验室。
        </el-alert>

        <div class="intro">
          <div class="intro-title">管理员可以做什么</div>
          <ul>
            <li>审核学生的预约（通过 / 拒绝 / 改约 / 强制取消）</li>
            <li>管理实验室与设备信息</li>
            <li>查看和管理用户（学生），处理管理员申请</li>
          </ul>
          <div class="intro-tip">
            注意：删除其他管理员、调整用户角色、审核管理员申请这些操作，仍然只有主管理员能做。
          </div>
        </div>

        <div style="margin: 16px 0 6px; font-weight: 600; color: #303133">
          申请说明 <span style="color: #f56c6c">*</span>
        </div>
        <el-input
          v-model="note"
          type="textarea"
          :rows="4"
          maxlength="200"
          show-word-limit
          placeholder="简单说明你为什么需要管理员权限，例如：负责本实验室的排期与审核，需要处理同学的预约申请（至少 5 个字）"
        />

        <div style="text-align: center; margin-top: 20px">
          <el-button
            type="primary"
            size="large"
            :loading="submitting"
            :disabled="note.trim().length < 5"
            @click="apply"
          >
            提交申请
          </el-button>
          <div v-if="note.trim().length > 0 && note.trim().length < 5" class="note-tip">
            申请说明至少 5 个字
          </div>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { applyAdminApi } from '@/api/auth'
import { getUserInfo as getUserMeApi } from '@/api/user'
import { useUser } from '@/utils/user'

const { userInfo, updateUser } = useUser()
const submitting = ref(false)
const note = ref('')

const isAdmin = computed(() => userInfo.value?.role === 'admin')
const pending = computed(() => userInfo.value?.pending_admin === 1)

// 被拒绝后的冷却期：后端返回 apply_retry_at
const retryAt = computed(() => {
  const value = userInfo.value?.apply_retry_at
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
})
const inCooldown = computed(() => !!retryAt.value && retryAt.value.getTime() > Date.now())
const retryDateText = computed(() => {
  if (!retryAt.value) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${retryAt.value.getFullYear()}-${pad(retryAt.value.getMonth() + 1)}-${pad(
    retryAt.value.getDate()
  )}`
})
const remainDays = computed(() => {
  if (!retryAt.value) return 0
  return Math.max(1, Math.ceil((retryAt.value.getTime() - Date.now()) / 86400000))
})

const refresh = async () => {
  const res = await getUserMeApi()
  if (res.code === 200) updateUser(res.data)
}

const apply = () => {
  const text = note.value.trim()
  if (text.length < 5) {
    ElMessage.warning('请填写申请说明（至少 5 个字）')
    return
  }
  ElMessageBox.confirm(
    `提交后由主管理员审核，审核期间你仍然可以正常使用学生功能。\n\n申请说明：${text}`,
    '申请成为管理员',
    { type: 'warning', confirmButtonText: '提交申请', cancelButtonText: '再想想' }
  )
    .then(async () => {
      submitting.value = true
      try {
        const res = await applyAdminApi(text)
        if (res.code === 200) {
          ElMessage.success('申请已提交，等待主管理员审核')
          await refresh()
        }
      } finally {
        submitting.value = false
      }
    })
    .catch(() => {})
}
</script>

<style scoped>
.intro {
  background: #f8f9fb;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px 20px;
  font-size: 13px;
  color: #606266;
  line-height: 1.9;
}
.intro-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}
.intro ul {
  margin: 0;
  padding-left: 20px;
}
.intro-tip {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}
.note-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #e6a23c;
}
</style>
