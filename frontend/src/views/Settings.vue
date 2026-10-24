<template>
  <div class="settings-page" v-loading="loading">
    <div class="page-head">
      <div class="head-text">
        <h2>系统设置</h2>
        <p>这里的规则对所有人生效（管理员也一样），提交预约、修改、取消时都会按规则校验</p>
      </div>
      <div class="head-actions">
        <el-button @click="load">重置</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
      </div>
    </div>

    <el-form :model="form" label-width="0" class="settings-form">
      <el-card
        v-for="group in groups"
        :key="group.key"
        shadow="never"
        class="section-card"
      >
        <template #header>
          <div class="section-head">
            <el-icon class="section-icon"><component :is="group.icon" /></el-icon>
            <div>
              <div class="section-title">{{ group.title }}</div>
              <div class="section-desc">{{ group.desc }}</div>
            </div>
          </div>
        </template>

        <div v-for="item in group.items" :key="item.key" class="row">
          <div class="row-text">
            <div class="row-title">{{ item.label }}</div>
            <div class="row-hint">{{ item.hint }}</div>
          </div>
          <div class="row-control">
            <el-input-number
              v-model="form[item.key]"
              :min="item.min"
              :max="item.max"
              controls-position="right"
            />
            <span class="unit">{{ item.unit }}</span>
          </div>
        </div>
      </el-card>
    </el-form>

    <el-card shadow="never" class="preview-card">
      <template #header>
        <div class="section-head">
          <el-icon class="section-icon"><InfoFilled /></el-icon>
          <div>
            <div class="section-title">当前规则效果</div>
            <div class="section-desc">保存后立即按下面的方式生效</div>
          </div>
        </div>
      </template>
      <div class="chips">
        <span v-for="chip in previewChips" :key="chip" class="chip">{{ chip }}</span>
      </div>
      <div class="preview-line">
        签到：预约通过后，开始前 30 分钟到结束之间可签到；过期未签到记一次违约。
        「0」表示不限制。
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled, Tickets, EditPen } from '@element-plus/icons-vue'
import { getReservationRulesApi, updateReservationRulesApi } from '@/api/setting'

const loading = ref(false)
const saving = ref(false)
const form = reactive({
  advance_days: 30,
  max_hours: 4,
  daily_limit: 2,
  no_show_limit: 3,
  modify_limit: 2,
  modify_window_days: 0,
  modify_before_days: 0,
  cancel_before_days: 0
})

const groups = [
  {
    key: 'booking',
    title: '预约规则',
    desc: '提交预约时校验：能约多远的日期、单次占多久、一天能约几次、违约怎么处理',
    icon: Tickets,
    items: [
      {
        key: 'advance_days',
        label: '最多提前几天预约',
        hint: '超过这个天数的日期不能提交预约',
        unit: '天',
        min: 1,
        max: 365
      },
      {
        key: 'max_hours',
        label: '单次最长时长',
        hint: '一次预约最多能占用几个小时',
        unit: '小时',
        min: 1,
        max: 24
      },
      {
        key: 'daily_limit',
        label: '每人每天最多预约',
        hint: '同一个人同一天最多能有几条有效预约',
        unit: '次',
        min: 1,
        max: 20
      },
      {
        key: 'no_show_limit',
        label: '违约几次后禁用账号',
        hint: '预约通过了却没签到记一次违约，累计到这个次数自动禁用账号',
        unit: '次',
        min: 1,
        max: 10
      }
    ]
  },
  {
    key: 'self-service',
    title: '学生自助：改预约与取消',
    desc: '只对「还没开始」的预约生效，超出限制就只能找管理员处理',
    icon: EditPen,
    items: [
      {
        key: 'modify_limit',
        label: '最多能改几次',
        hint: '每条预约的修改次数上限，0 = 不允许自己改',
        unit: '次',
        min: 0,
        max: 10
      },
      {
        key: 'modify_window_days',
        label: '提交后多少天内可改',
        hint: '从提交那一刻算起，超过就不能自己改了，0 = 不限制',
        unit: '天',
        min: 0,
        max: 30
      },
      {
        key: 'modify_before_days',
        label: '开始前多少天内不能再改',
        hint: '离进场太近就不让改，避免临场变动，0 = 不限制',
        unit: '天',
        min: 0,
        max: 30
      },
      {
        key: 'cancel_before_days',
        label: '开始前多少天内不能取消',
        hint: '离进场不足这个天数就不能自己取消，0 = 随时能取消',
        unit: '天',
        min: 0,
        max: 30
      }
    ]
  }
]

const previewChips = computed(() => [
  `最多提前 ${form.advance_days} 天预约`,
  `单次最长 ${form.max_hours} 小时`,
  `每人每天最多 ${form.daily_limit} 次`,
  `违约 ${form.no_show_limit} 次禁用账号`,
  form.modify_limit > 0 ? `每条最多改 ${form.modify_limit} 次` : '不允许自己改预约',
  form.modify_window_days > 0
    ? `提交后 ${form.modify_window_days} 天内可改`
    : '提交后随时可改（受次数限制）',
  form.modify_before_days > 0
    ? `开始前 ${form.modify_before_days} 天内不能改`
    : '离开场多近都能改',
  form.cancel_before_days > 0
    ? `开始前 ${form.cancel_before_days} 天内不能取消`
    : '随时可以取消（开始后除外）'
])

const load = async () => {
  loading.value = true
  try {
    const res = await getReservationRulesApi()
    if (res.code === 200 && res.data) Object.assign(form, res.data)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const res = await updateReservationRulesApi({
      advance_days: form.advance_days,
      max_hours: form.max_hours,
      daily_limit: form.daily_limit,
      no_show_limit: form.no_show_limit,
      modify_limit: form.modify_limit,
      modify_window_days: form.modify_window_days,
      modify_before_days: form.modify_before_days,
      cancel_before_days: form.cancel_before_days
    })
    if (res.code === 200) {
      Object.assign(form, res.data)
      ElMessage.success('规则已保存，立即生效')
    }
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.settings-page {
  max-width: 920px;
  margin: 0 auto;
}

.page-head {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}
.head-text h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
.head-text p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}
.head-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.section-card {
  margin-bottom: 16px;
  border-radius: 10px;
}
.section-head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.section-icon {
  font-size: 17px;
  color: #409eff;
  background: #eef6ff;
  border-radius: 8px;
  padding: 7px;
  box-sizing: content-box;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.section-desc {
  margin-top: 2px;
  font-size: 12px;
  color: #909399;
}

.row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 6px;
  border-bottom: 1px dashed #f0f2f5;
  border-radius: 6px;
  transition: background 0.15s;
}
.row:last-child {
  border-bottom: none;
}
.row:hover {
  background: #fafbfc;
}
.row-text {
  min-width: 0;
}
.row-title {
  font-size: 14px;
  color: #303133;
}
.row-hint {
  margin-top: 3px;
  font-size: 12px;
  color: #a8abb2;
  line-height: 1.5;
}
.row-control {
  margin-left: auto;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.row-control :deep(.el-input-number) {
  width: 130px;
}
.unit {
  margin-left: 10px;
  min-width: 28px;
  white-space: nowrap;
  font-size: 13px;
  color: #909399;
}

.preview-card {
  border-radius: 10px;
  background: #fcfdff;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  font-size: 12px;
  color: #606266;
  background: #f4f6f8;
  border-radius: 14px;
  padding: 5px 12px;
}
.chip b {
  color: var(--el-color-primary);
  font-weight: 600;
}
.preview-line {
  margin-top: 12px;
  font-size: 12px;
  color: #a8abb2;
  line-height: 1.8;
}
</style>
