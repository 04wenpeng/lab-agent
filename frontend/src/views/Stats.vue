<template>
  <div v-loading="loading">
    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header>
        <div style="display: flex; align-items: center">
          <span style="font-size: 16px; font-weight: bold">统计报表</span>
          <el-radio-group v-model="days" size="small" style="margin-left: auto" @change="load">
            <el-radio-button :value="7">近 7 天</el-radio-button>
            <el-radio-button :value="30">近 30 天</el-radio-button>
            <el-radio-button :value="90">近 90 天</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-row :gutter="12">
        <el-col :xs="12" :sm="8" :md="4" v-for="item in summaryCards" :key="item.label">
          <div class="stat">
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header><span>实验室使用率（按占用时长）</span></template>
          <div v-if="!labs.length" class="empty">暂无数据</div>
          <div v-for="row in labs" :key="row.lab_id" class="bar-row">
            <span class="bar-name">{{ row.lab_name }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: Math.min(row.rate, 100) + '%' }"></div>
            </div>
            <span class="bar-value">{{ row.hours }} 小时 · {{ row.rate }}%</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header><span>热门时段（按开始时间）</span></template>
          <div class="hour-chart">
            <div v-for="row in hours" :key="row.hour" class="hour-col">
              <div class="hour-bar-wrap">
                <div class="hour-bar" :style="{ height: hourHeight(row.count) }"></div>
              </div>
              <div class="hour-count">{{ row.count || '' }}</div>
              <div class="hour-label">{{ row.hour.slice(0, 2) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header><span>违约情况</span></template>
      <el-row :gutter="12" style="margin-bottom: 12px">
        <el-col :xs="24" :sm="8">
          <div class="stat">
            <div class="stat-label">未签到（违约）</div>
            <div class="stat-value" style="color: #f56c6c">{{ summary.no_show }} 次</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="stat">
            <div class="stat-label">已签到</div>
            <div class="stat-value" style="color: #67c23a">{{ summary.checked_in }} 次</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="stat">
            <div class="stat-label">签到率</div>
            <div class="stat-value" style="color: #409eff">{{ summary.check_in_rate }}%</div>
          </div>
        </el-col>
      </el-row>
      <el-tabs v-model="noShowTab" style="margin-top: 4px">
        <el-tab-pane :label="`违约明细（${noShowList.length}）`" name="detail">
          <el-table
            :data="noShowList"
            size="small"
            style="width: 100%"
            row-style="cursor: pointer"
            @row-click="openDetail"
          >
            <el-table-column prop="user_name" label="用户" width="110" />
            <el-table-column prop="lab_name" label="实验室" />
            <el-table-column label="设备" width="110">
              <template #default="{ row }">{{ row.equipment_name || '整间' }}</template>
            </el-table-column>
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column label="时段" width="140">
              <template #default="{ row }">{{ row.start_time }} - {{ row.end_time }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default>
                <el-tag type="danger" size="small">未签到</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button type="primary" text size="small" @click.stop="openDetail(row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!noShowList.length" class="empty" style="padding: 10px 0">
            时间范围内没有违约记录 👍
          </div>
        </el-tab-pane>

        <el-tab-pane label="按用户汇总" name="user">
          <el-table :data="noShowUsers" size="small" style="width: 100%">
            <el-table-column prop="user_name" label="用户" />
            <el-table-column prop="count" label="违约次数" width="140" />
            <el-table-column label="处理" width="200">
              <template #default="{ row }">
                <el-tag v-if="row.count >= noShowLimit" type="danger" size="small">已自动禁用</el-tag>
                <span v-else style="color: #909399; font-size: 12px">
                  再 {{ noShowLimit - row.count }} 次将被禁用
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!noShowUsers.length" class="empty" style="padding: 10px 0">暂无</div>
        </el-tab-pane>
      </el-tabs>
      <div class="tip">
        规则：预约通过后，在开始前 30 分钟到结束之间可以签到；过期未签到记一次违约，累计
        {{ noShowLimit }} 次自动禁用账号（可在「系统设置」里改）。
      </div>
    </el-card>

    <!-- 违约预约详情 -->
    <el-dialog v-model="detailVisible" title="预约详情" width="560">
      <el-descriptions v-if="detail" :column="1" border size="small">
        <el-descriptions-item label="预约人">{{ detail.user_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="实验室">{{ detail.lab_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备">
          {{ detail.equipment_name || '整间实验室' }}
        </el-descriptions-item>
        <el-descriptions-item label="日期">{{ detail.date }}</el-descriptions-item>
        <el-descriptions-item label="时段">
          {{ detail.start_time }} - {{ detail.end_time }}
        </el-descriptions-item>
        <el-descriptions-item label="使用人数">{{ detail.people || 1 }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detail.remark || '（无）' }}</el-descriptions-item>
        <el-descriptions-item label="预约状态">
          <el-tag :type="statusType(detail.status)" size="small">
            {{ statusText(detail.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="签到情况">
          <el-tag v-if="detail.checked_in === 1" type="success" size="small">已签到</el-tag>
          <el-tag v-else-if="detail.no_show === 1" type="danger" size="small">未签到（违约）</el-tag>
          <span v-else style="color: #909399">未签到</span>
        </el-descriptions-item>
        <el-descriptions-item label="审核来源">
          {{ detail.audit_source === 'ai' ? 'AI 自动审核' : '管理员审核' }}
        </el-descriptions-item>
        <el-descriptions-item label="审核人">{{ detail.audit_by_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">
          {{ formatTime(detail.audit_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="提交时间">
          {{ formatTime(detail.create_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="修改次数">{{ detail.modify_count || 0 }} 次</el-descriptions-item>
        <el-descriptions-item v-if="detail.cancel_reason" label="取消/调整原因">
          {{ detail.cancel_reason }}
        </el-descriptions-item>
      </el-descriptions>
      <div v-else style="color: #909399; font-size: 13px">加载中…</div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { getStatsApi } from '@/api/stats'
import { getReservationRulesApi } from '@/api/setting'
import { getReservationDetailApi } from '@/api/reservation'

const loading = ref(false)
const days = ref(30)
const summary = ref({})
const labs = ref([])
const hours = ref([])
const noShowUsers = ref([])
const noShowList = ref([])
const noShowTab = ref('detail')
const noShowLimit = ref(3)
// 违约预约详情
const detailVisible = ref(false)
const detail = ref(null)

const statusText = (status) =>
  ({ 0: '待审核', 1: '已通过', 2: '已拒绝', 3: '已取消' })[status] || '-'
const statusType = (status) =>
  ({ 0: 'warning', 1: 'success', 2: 'danger', 3: 'info' })[status] || ''
const formatTime = (value) => {
  if (!value) return '-'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const openDetail = async (row) => {
  detail.value = null
  detailVisible.value = true
  try {
    const res = await getReservationDetailApi(row.id)
    if (res.code === 200) detail.value = res.data
  } catch {
    detail.value = null
  }
}

const summaryCards = computed(() => [
  { label: '预约总数', value: summary.value.total ?? 0, color: '#303133' },
  { label: '已通过', value: summary.value.approved ?? 0, color: '#67c23a' },
  { label: '待审核', value: summary.value.pending ?? 0, color: '#e6a23c' },
  { label: '已拒绝', value: summary.value.rejected ?? 0, color: '#f56c6c' },
  { label: '已取消', value: summary.value.cancelled ?? 0, color: '#909399' },
  { label: '今日预约', value: summary.value.today ?? 0, color: '#409eff' }
])

const maxCount = computed(() => Math.max(...hours.value.map((h) => h.count), 1))
const hourHeight = (count) => (count ? `${Math.max(6, (count / maxCount.value) * 100)}%` : '0%')

const load = async () => {
  loading.value = true
  try {
    const [res, rules] = await Promise.all([getStatsApi(days.value), getReservationRulesApi()])
    if (res.code === 200) {
      summary.value = res.data.summary || {}
      labs.value = res.data.labs || []
      hours.value = res.data.hours || []
      noShowUsers.value = res.data.no_show_users || []
      noShowList.value = res.data.no_show_list || []
    }
    if (rules.code === 200) noShowLimit.value = rules.data?.no_show_limit || 3
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.stat {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fafbfc;
}
.stat-label {
  font-size: 12px;
  color: #909399;
}
.stat-value {
  font-size: 20px;
  font-weight: 600;
  margin-top: 4px;
}
.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 13px;
}
.bar-name {
  width: 130px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bar-track {
  flex: 1;
  height: 14px;
  background: #f0f2f5;
  border-radius: 7px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #79bbff, #409eff);
  border-radius: 7px;
  transition: width 0.3s;
}
.bar-value {
  width: 130px;
  text-align: right;
  color: #909399;
  font-size: 12px;
}
.hour-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 160px;
}
.hour-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}
.hour-bar-wrap {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
}
.hour-bar {
  width: 100%;
  background: linear-gradient(180deg, #a0cfff, #409eff);
  border-radius: 3px 3px 0 0;
  transition: height 0.3s;
}
.hour-count {
  font-size: 10px;
  color: #909399;
  height: 14px;
}
.hour-label {
  font-size: 10px;
  color: #c0c4cc;
}
.empty {
  color: #c0c4cc;
  font-size: 13px;
}
.tip {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
  line-height: 1.8;
}
</style>
