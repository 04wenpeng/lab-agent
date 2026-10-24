<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">
          <span>我的预约记录</span>
        </div>
      </template>
      <div style="margin-bottom: 10px">
        <el-select
          placeholder="请选择状态"
          v-model="params.status"
          style="width: 200px; margin-right: 8px"
          clearable
          @change="handleSearch"
          @clear="handleSearch"
        >
          <el-option :value="0" label="待审核" />
          <el-option :value="1" label="已通过" />
          <el-option :value="2" label="已拒绝" />
          <el-option :value="3" label="已取消" />
        </el-select>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
      <el-table
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#333' }"
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="lab_name" label="实验室" min-width="120" />
        <el-table-column label="预约类型" class-name="hide-mobile" label-class-name="hide-mobile">
          <template #default="{ row }">
            <el-tag :type="row.type === '实验室' ? 'success' : 'primary'">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="设备" class-name="hide-mobile" label-class-name="hide-mobile">
          <template #default="{ row }">
            {{ row.equipment_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column label="预约时段" width="160">
          <template #default="{ row }"> {{ row.start_time }} - {{ row.end_time }} </template>
        </el-table-column>
        <el-table-column prop="people" label="人数" width="70" />
        <el-table-column prop="remark" label="备注" class-name="hide-mobile" label-class-name="hide-mobile" />
        <el-table-column label="处理说明" width="180">
          <template #default="{ row }">
            <span v-if="row.audit_source === 'ai'" style="color: #409eff">
              AI 自动审核{{ row.status === 2 ? '：' + (row.cancel_reason || '未通过') : ' 通过' }}
            </span>
            <span v-else-if="row.cancel_reason" style="color: #e6a23c">
              {{ row.status === 3 ? '取消原因：' : '调整原因：' }}{{ row.cancel_reason }}
            </span>
            <span v-else-if="row.audit_by_name" style="color: #909399">
              {{ row.audit_by_name }} 于 {{ formatTime(row.audit_time) }} 处理
            </span>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="签到" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.checked_in === 1" type="success" size="small">已签到</el-tag>
            <el-tag v-else-if="row.no_show === 1" type="danger" size="small">未签到</el-tag>
            <span v-else-if="row.status === 1" style="color: #e6a23c; font-size: 12px"
              >待签到</span
            >
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="预约状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230">
          <template #default="{ row }">
            <el-button v-if="canCancel(row)" type="danger" text bg @click="handleCancel(row)"
              >取消</el-button
            >
            <el-button
              v-if="canModify(row)"
              type="primary"
              text
              bg
              @click="openModify(row)"
              >修改</el-button
            >
            <el-button
              v-if="row.status === 1 && row.checked_in !== 1"
              type="success"
              text
              bg
              @click="handleCheckIn(row)"
              >签到</el-button
            >
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 10px; display: flex; justify-content: flex-end">
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

    <!-- 学生自己改预约 -->
    <el-dialog v-model="modifyVisible" title="修改预约" width="470">
      <el-form :model="modifyForm" label-width="80px" style="padding-right: 20px">
        <el-form-item label="实验室">
          <el-input :model-value="modifyRow?.lab_name" disabled />
        </el-form-item>
        <el-form-item label="预约日期" required>
          <el-date-picker
            v-model="modifyForm.date"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="开始时间" required>
          <el-time-picker
            v-model="modifyForm.start_time"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" required>
          <el-time-picker
            v-model="modifyForm.end_time"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="使用人数">
          <el-input-number v-model="modifyForm.people" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="modifyForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <div class="modify-tip">
        这是第 {{ (modifyRow?.modify_count || 0) + 1 }} 次修改，每条预约最多改
        {{ modifyLimit }} 次
        <template v-if="modifyRules.modify_window_days > 0">
          ，且提交后 {{ modifyRules.modify_window_days }} 天内才能改
        </template>
        <template v-if="modifyRules.modify_before_days > 0">
          ，进场前 {{ modifyRules.modify_before_days }} 天内不能再改
        </template>
        ；改完立即生效（已通过的直接按新时段使用）。
      </div>
      <template #footer>
        <el-button @click="modifyVisible = false">取消</el-button>
        <el-button type="primary" :loading="modifying" @click="submitModify">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {
  cancelReservationApi,
  checkInReservationApi,
  getReservationPageList,
  modifyReservationApi
} from '@/api/reservation'
import { getReservationRulesApi } from '@/api/setting'
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
const statusType = (status) => {
  return { 0: 'warning', 1: 'success', 2: 'danger', 3: 'info' }[status] || '-'
}
const statusText = (status) => {
  return { 0: '待审核', 1: '已通过', 2: '已拒绝', 3: '已取消' }[status] || '-'
}
const formatTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getMonth() + 1}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(
    date.getMinutes()
  )}`
}
const loading = ref(false)
const tableData = ref([])
const params = reactive({
  page: 1,
  page_size: 10,
  status: null,
  // 管理员也能预约，这页永远只看自己的（后端默认给管理员返回全部）
  mine: true
})
const total = ref(0)

// ===== 自己改预约 =====
const modifyVisible = ref(false)
const modifying = ref(false)
const modifyRow = ref(null)
const modifyLimit = ref(2)
const modifyRules = ref({ modify_window_days: 0, modify_before_days: 0 })
const cancelBeforeDays = ref(0)

// 还没开始、状态是待审核/已通过，且没进「开始前 N 天」的禁区，才能自己取消
const canCancel = (row) => {
  if (row.status !== 0 && row.status !== 1) return false
  if (!notStarted(row)) return false
  const limit = cancelBeforeDays.value || 0
  if (limit > 0) {
    const startAt = new Date(`${row.date}T${row.start_time}:00`).getTime()
    if (!Number.isNaN(startAt) && startAt - Date.now() < limit * 86400000) return false
  }
  return true
}
const modifyForm = reactive({
  date: '',
  start_time: '09:00',
  end_time: '10:00',
  people: 1,
  remark: ''
})

// 还没开始才能改（开始时间已经过了就不行）
const notStarted = (row) => {
  const at = new Date(`${row.date}T${row.start_time}:00`)
  return !Number.isNaN(at.getTime()) && at.getTime() > Date.now()
}

const canModify = (row) => {
  if (row.status !== 0 && row.status !== 1) return false
  if (!notStarted(row)) return false
  if ((row.modify_count || 0) >= modifyLimit.value) return false

  // 提交后 N 天内才能改
  const windowDays = modifyRules.value.modify_window_days || 0
  if (windowDays > 0 && row.create_time) {
    const created = new Date(row.create_time).getTime()
    if (!Number.isNaN(created) && Date.now() - created > windowDays * 86400000) return false
  }

  // 离开场不足 N 天就不能自己改
  const beforeDays = modifyRules.value.modify_before_days || 0
  if (beforeDays > 0) {
    const startAt = new Date(`${row.date}T${row.start_time}:00`).getTime()
    if (!Number.isNaN(startAt) && startAt - Date.now() < beforeDays * 86400000) return false
  }
  return true
}

const openModify = (row) => {
  modifyRow.value = row
  modifyForm.date = row.date
  modifyForm.start_time = row.start_time
  modifyForm.end_time = row.end_time
  modifyForm.people = row.people || 1
  modifyForm.remark = row.remark || ''
  modifyVisible.value = true
}

const submitModify = async () => {
  if (!modifyForm.date || !modifyForm.start_time || !modifyForm.end_time) {
    ElMessage.warning('日期和时间都要填')
    return
  }
  modifying.value = true
  try {
    const res = await modifyReservationApi(modifyRow.value.id, {
      date: modifyForm.date,
      start_time: modifyForm.start_time,
      end_time: modifyForm.end_time,
      people: modifyForm.people,
      remark: modifyForm.remark
    })
    if (res.code === 200) {
      ElMessage.success('修改成功')
      modifyVisible.value = false
      load()
    }
  } finally {
    modifying.value = false
  }
}

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

const handleCancel = (row) => {
  ElMessageBox.confirm(`确认取消 [${row.lab_name}] 的预约？`, '确认取消', { type: 'warning' }).then(
    async () => {
      const res = await cancelReservationApi(row.id)
      if (res.code === 200) {
        ElMessage.success('取消预约成功')
        load()
      }
    }
  )
}

const handleCheckIn = (row) => {
  ElMessageBox.confirm(
    `确认签到 [${row.lab_name}] ${row.date} ${row.start_time}-${row.end_time} 的预约？`,
    '签到确认',
    { type: 'info' }
  ).then(async () => {
    const res = await checkInReservationApi(row.id)
    if (res.code === 200) {
      ElMessage.success('签到成功')
      load()
    }
  })
}

const handleSearch = () => {
  params.page = 1
  load()
}

onMounted(async () => {
  load()
  try {
    const res = await getReservationRulesApi()
    if (res.code === 200 && res.data) {
      modifyLimit.value = res.data.modify_limit ?? 2
      modifyRules.value = {
        modify_window_days: res.data.modify_window_days || 0,
        modify_before_days: res.data.modify_before_days || 0
      }
      cancelBeforeDays.value = res.data.cancel_before_days || 0
    }
  } catch {
    modifyLimit.value = 2
  }
})
</script>

<style scoped>
.modify-tip {
  padding: 0 20px 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.8;
}
</style>
