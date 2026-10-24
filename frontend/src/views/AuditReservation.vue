<template>
  <div class="page">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="page-head">
          <div class="head-text">
            <h2>
              预约审核
              <span class="count-badge">{{ total }}</span>
            </h2>
            <p>AI 会自动审核大部分预约；这里可以人工复核、改约或强制取消</p>
          </div>
          <div class="head-actions">
            <el-select
              placeholder="请选择状态"
              v-model="params.status"
              style="width: 170px"
              clearable
              @change="handleSearch"
              @clear="handleSearch"
            >
              <el-option :value="0" label="待审核" />
              <el-option :value="1" label="已通过" />
              <el-option :value="2" label="已拒绝" />
              <el-option :value="3" label="已取消" />
            </el-select>
            <el-button @click="handleSearch">查询</el-button>
          </div>
        </div>
      </template>
      <el-table
        :header-cell-style="{ backgroundColor: '#fafbfc', color: '#909399', fontWeight: 500 }"
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="lab_name" label="实验室" />
        <el-table-column label="预约类型">
          <template #default="{ row }">
            <el-tag :type="row.type === '实验室' ? 'success' : 'primary'">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="设备">
          <template #default="{ row }">
            {{ row.equipment_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" />
        <el-table-column label="预约时段">
          <template #default="{ row }"> {{ row.start_time }} - {{ row.end_time }} </template>
        </el-table-column>
        <el-table-column prop="people" label="人数" width="70" />
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="user_name" label="预约人" width="100" />
        <el-table-column label="签到" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.checked_in === 1" type="success" size="small">已签到</el-tag>
            <el-tag v-else-if="row.no_show === 1" type="danger" size="small">违约</el-tag>
            <span v-else-if="row.status === 1" style="color: #e6a23c; font-size: 12px">未签到</span>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="预约状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核人" width="110">
          <template #default="{ row }">{{ row.audit_by_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="审核时间" width="170">
          <template #default="{ row }">{{ formatTime(row.audit_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="230">
          <template #default="{ row }">
            <template v-if="row.status === 0">
              <el-button type="success" text bg size="small" @click="handleAudit(row, 1)"
                >通过</el-button
              >
              <el-button type="danger" text bg size="small" @click="handleAudit(row, 2)"
                >拒绝</el-button
              >
            </template>
            <el-dropdown
              v-if="row.status === 0 || row.status === 1"
              trigger="click"
              @command="(cmd) => handleMore(cmd, row)"
            >
              <el-button text bg size="small" style="margin-left: 4px">
                更多<el-icon style="margin-left: 2px"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="reschedule">改约时间</el-dropdown-item>
                  <el-dropdown-item command="cancel" divided>强制取消</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="rescheduleVisible" title="调整预约时间" width="460">
        <el-form label-width="80px">
          <el-form-item label="预约人">
            <span>{{ currentRow?.user_name }} · {{ currentRow?.lab_name }}</span>
          </el-form-item>
          <el-form-item label="日期">
            <el-date-picker
              v-model="rescheduleForm.date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="开始时间">
            <el-time-select
              v-model="rescheduleForm.start_time"
              start="07:00"
              step="00:30"
              end="22:00"
              placeholder="开始"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="结束时间">
            <el-time-select
              v-model="rescheduleForm.end_time"
              start="07:00"
              step="00:30"
              end="22:00"
              placeholder="结束"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="原因">
            <el-input v-model="rescheduleForm.reason" placeholder="会通知给预约人" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="rescheduleVisible = false">取消</el-button>
          <el-button type="primary" :loading="rescheduleSaving" @click="saveReschedule"
            >确定改约</el-button
          >
        </template>
      </el-dialog>

      <div class="pager">
        <el-pagination
          v-model:current-page="params.page"
          v-model:page-size="params.page_size"
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
import {
  adminCancelReservationApi,
  adminRescheduleReservationApi,
  auditReservationApi,
  getReservationPageList
} from '@/api/reservation'
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
const statusType = (status) => {
  return { 0: 'warning', 1: 'success', 2: 'danger', 3: 'info' }[status] || '-'
}
const statusText = (status) => {
  return { 0: '待审核', 1: '已通过', 2: '已拒绝', 3: '已取消' }[status] || '-'
}
// 后端返回的 ISO 时间，转成「2026-10-23 13:30」
const formatTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`
}
const loading = ref(false)
const tableData = ref([])
const params = reactive({
  page: 1,
  page_size: 10,
  status: 0
})
const total = ref(0)

const load = async () => {
  loading.value = true
  try {
    const res = await getReservationPageList(params)
    if (res.code === 200) {
      tableData.value = res.data?.list
      total.value = res.data?.total
    }
  } finally {
    loading.value = false
  }
}

const handleAudit = (row, status) => {
  const action = status === 1 ? '通过' : '拒绝'
  ElMessageBox.confirm(`${action} [${row.user_name}] 的预约？`, '审核', { type: 'warning' }).then(
    async () => {
      const res = await auditReservationApi(row.id, status)
      if (res.code === 200) {
        ElMessage.success(`审核${action}`)
        load()
      }
    }
  )
}

const handleSearch = () => {
  params.page = 1
  load()
}

// ===== 更多操作：改约 / 强制取消 =====
const handleMore = (command, row) => {
  if (command === 'reschedule') {
    openReschedule(row)
  } else if (command === 'cancel') {
    handleAdminCancel(row)
  }
}

// ===== 管理员强制取消 =====
const handleAdminCancel = (row) => {
  ElMessageBox.prompt(
    `取消 [${row.user_name}] 的预约「${row.lab_name} ${row.date} ${row.start_time}-${row.end_time}」`,
    '强制取消预约',
    {
      type: 'warning',
      inputPlaceholder: '取消原因（会通知给预约人）',
      confirmButtonText: '确定取消',
      cancelButtonText: '返回'
    }
  )
    .then(async ({ value }) => {
      const res = await adminCancelReservationApi(row.id, value || '')
      if (res.code === 200) {
        ElMessage.success('已取消，并通知了预约人')
        load()
      }
    })
    .catch(() => {})
}

// ===== 管理员改约 =====
const rescheduleVisible = ref(false)
const rescheduleSaving = ref(false)
const currentRow = ref(null)
const rescheduleForm = reactive({
  date: '',
  start_time: '',
  end_time: '',
  reason: ''
})

const openReschedule = (row) => {
  currentRow.value = row
  rescheduleForm.date = row.date
  rescheduleForm.start_time = row.start_time
  rescheduleForm.end_time = row.end_time
  rescheduleForm.reason = ''
  rescheduleVisible.value = true
}

const saveReschedule = async () => {
  if (!rescheduleForm.date || !rescheduleForm.start_time || !rescheduleForm.end_time) {
    ElMessage.warning('日期和时间都要填')
    return
  }
  rescheduleSaving.value = true
  try {
    const res = await adminRescheduleReservationApi(currentRow.value.id, {
      ...rescheduleForm
    })
    if (res.code === 200) {
      ElMessage.success('已改约，并通知了预约人')
      rescheduleVisible.value = false
      load()
    }
  } finally {
    rescheduleSaving.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.page {
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
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
