<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold; display: flex; align-items: center">
          <span>AI 模型配置</span>
          <el-button type="primary" size="small" style="margin-left: auto" @click="openDefault">
            设置系统默认
          </el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 14px">
        API Key 只以密文保存在服务器：这里只能看到「已配置 / 未配置」，<b>主管理员也看不到 Key 内容</b>。
        每个人可以有自己的配置；没有自己配置的人，自动使用系统默认。
      </el-alert>

      <el-table :data="rows" v-loading="loading" style="width: 100%">
        <el-table-column prop="owner_name" label="归属" width="130">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="warning" effect="plain">系统默认</el-tag>
            <span v-else>{{ row.owner_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column prop="base_url" label="接口地址" min-width="220" show-overflow-tooltip />
        <el-table-column prop="model" label="模型" width="170" show-overflow-tooltip />
        <el-table-column label="API Key" width="110">
          <template #default="{ row }">
            <el-tag :type="row.has_key ? 'success' : 'info'" effect="plain" size="small">
              {{ row.has_key ? '已配置' : '未配置' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_default && row.has_key"
              type="warning"
              text
              bg
              size="small"
              @click="handlePromote(row)"
              >设为默认</el-button
            >
            <el-button
              text
              bg
              size="small"
              :type="row.status === 1 ? 'info' : 'success'"
              @click="toggleStatus(row)"
              >{{ row.status === 1 ? '停用' : '启用' }}</el-button
            >
            <el-button
              v-if="!row.is_default"
              type="danger"
              text
              bg
              size="small"
              @click="handleDelete(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="设置系统默认模型" width="540">
      <el-form label-width="90px">
        <el-form-item label="接口地址">
          <el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" />
        </el-form-item>
        <el-form-item label="模型名">
          <el-input v-model="form.model" placeholder="deepseek-chat" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="hasDefault ? '已配置，留空表示不修改' : '请输入 API Key'"
          />
        </el-form-item>
      </el-form>
      <div style="font-size: 12px; color: #909399">
        保存后，所有没有个人配置的人都会用这个模型。Key 保存为密文，列表里只显示「已配置」。
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveDefault">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteAIConfig,
  getAIConfigList,
  promoteAIConfig,
  saveDefaultAIConfig,
  setAIConfigStatus
} from '@/api/aiConfig'

const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const form = reactive({ base_url: '', model: '', api_key: '' })

const defaultRow = computed(() => rows.value.find((row) => row.is_default))
const hasDefault = computed(() => !!defaultRow.value)

const load = async () => {
  loading.value = true
  try {
    const res = await getAIConfigList()
    if (res.code === 200) rows.value = res.data || []
  } finally {
    loading.value = false
  }
}

const openDefault = () => {
  form.base_url = defaultRow.value?.base_url || ''
  form.model = defaultRow.value?.model || ''
  form.api_key = ''
  dialogVisible.value = true
}

const saveDefault = async () => {
  if (!form.base_url.trim() || !form.model.trim()) {
    ElMessage.warning('接口地址和模型名都要填')
    return
  }
  if (!hasDefault.value && !form.api_key.trim()) {
    ElMessage.warning('第一次设置必须填 API Key')
    return
  }
  saving.value = true
  try {
    const res = await saveDefaultAIConfig({
      base_url: form.base_url.trim(),
      model: form.model.trim(),
      api_key: form.api_key.trim() || null
    })
    if (res.code === 200) {
      ElMessage.success('系统默认配置已保存')
      dialogVisible.value = false
      load()
    }
  } finally {
    saving.value = false
  }
}

const handlePromote = (row) => {
  ElMessageBox.confirm(
    `把「${row.owner_name}」的配置复制成系统默认？Key 会在服务器内部复制，不会显示出来。`,
    '提示',
    { type: 'warning' }
  )
    .then(async () => {
      const res = await promoteAIConfig(row.id)
      if (res.code === 200) {
        ElMessage.success('已设为系统默认')
        load()
      }
    })
    .catch(() => {})
}

const toggleStatus = async (row) => {
  const res = await setAIConfigStatus(row.id, row.status === 1 ? 0 : 1)
  if (res.code === 200) {
    ElMessage.success(row.status === 1 ? '已停用' : '已启用')
    load()
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`删除「${row.owner_name}」的配置？`, '提示', { type: 'warning' })
    .then(async () => {
      const res = await deleteAIConfig(row.id)
      if (res.code === 200) {
        ElMessage.success('已删除')
        load()
      }
    })
    .catch(() => {})
}

onMounted(load)
</script>
