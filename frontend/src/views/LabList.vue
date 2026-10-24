<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold; display: flex; justify-content: space-between">
          <span>实验室列表</span>
          <span style="font-size: 12px; font-weight: normal; color: #909399">
            状态每分钟自动刷新 · 最近更新 {{ updatedAt }}
          </span>
        </div>
      </template>
      <div style="margin-bottom: 10px">
        <el-input
          placeholder="请输入名称查询"
          v-model="params.keywords"
          style="width: 240px; margin-right: 8px"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        ></el-input>
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
      </div>

      <div>
        <el-row :gutter="16" v-loading="loading">
          <el-col
            v-for="item in tableData"
            :key="item.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            style="margin-bottom: 16px"
          >
            <el-card shadow="hover">
              <div class="lab-cover">
                <img v-if="item.img" :src="item.img" alt="" class="lab-img" />
                <div v-else class="lab-img lab-img--empty"></div>
                <el-tag
                  class="lab-state"
                  :type="stateOf(item).type"
                  effect="dark"
                  size="small"
                  round
                >
                  {{ stateOf(item).text }}
                </el-tag>
              </div>
              <div style="font-size: 16px; font-weight: bold; margin-top: 10px">
                {{ item.name }}
              </div>
              <div style="font-size: 13px; margin-top: 8px; color: #666">
                位置：{{ item.location || '-' }}
              </div>
              <div style="font-size: 13px; margin-top: 6px; color: #666">
                容量：{{ item.capacity }} 人
              </div>
              <div style="font-size: 13px; margin-top: 6px; color: #666">
                开放：{{
                  item.open_time && item.close_time ? `${item.open_time} - ${item.close_time}` : '-'
                }}
              </div>
              <div style="font-size: 13px; margin-top: 6px; color: #666">
                今日预约：{{ item.today_count || 0 }} 条
              </div>
              <div style="margin-top: 12px; display: flex; gap: 8px">
                <el-button style="flex: 1" @click="handleViewEquipment(item)">查看设备</el-button>
                <el-button
                  style="flex: 1"
                  type="primary"
                  :disabled="item.status !== 1"
                  @click="handleReserve(item)"
                >
                  {{ item.status === 1 ? '预约' : '已关闭' }}
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>

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
      </div>
    </el-card>

    <reserve-dialog
      v-model:visible="reserveVisible"
      :lab-id="currentLab?.id"
      :lab-name="currentLab?.name"
      :lab-capacity="currentLab?.capacity"
    ></reserve-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { getLabPageList } from '@/api/lab'
import { Search } from '@element-plus/icons-vue'
import router from '@/router'
import ReserveDialog from '@/components/ReserveDialog.vue'

const reserveVisible = ref(false)
const currentLab = ref(null)
const params = reactive({
  page: 1,
  page_size: 10,
  keywords: ''
})
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const updatedAt = ref('-')
let timer = null

// 当前状态：关闭 > 使用中 > 空闲
const stateOf = (lab) => {
  if (lab.status !== 1) return { type: 'info', text: '已关闭' }
  if (lab.busy_now) return { type: 'danger', text: `使用中 · 至 ${lab.busy_until}` }
  return { type: 'success', text: '空闲可预约' }
}

const handleViewEquipment = (lab) => {
  router.push({ path: '/manager/lab-equipment', query: { lab_id: lab.id } })
}

const handleReserve = (lab) => {
  currentLab.value = lab
  reserveVisible.value = true
}

// 加载分页数据；silent=true 时用于定时刷新，不显示 loading
const load = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const res = await getLabPageList(params)
    if (res.code === 200) {
      tableData.value = res.data?.list || []
      total.value = res.data?.total || 0
      updatedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    }
  } finally {
    if (!silent) loading.value = false
  }
}

const handleSearch = () => {
  params.page = 1
  load()
}

onMounted(() => {
  load()
  // 「当前状态」会随时间变化，每分钟静默刷新一次
  timer = setInterval(() => load(true), 60 * 1000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.lab-cover {
  position: relative;
}

.lab-img {
  display: block;
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 6px;
}

.lab-img--empty {
  background-color: #f5f7fa;
}

.lab-state {
  position: absolute;
  top: 8px;
  right: 8px;
}
</style>
