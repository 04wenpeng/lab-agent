<template>
  <div class="page">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="page-head">
          <div class="head-text">
            <h2>
              设备库
              <span class="count-badge">{{ rows.length }}</span>
            </h2>
            <p>全局设备清单：给实验室添加设备时从这里选，没有的先在这里登记</p>
          </div>
          <div class="head-actions">
            <el-button type="primary" :icon="Plus" @click="openCreate">新增设备</el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="rows"
        v-loading="loading"
        style="width: 100%"
        :header-cell-style="{ backgroundColor: '#fafbfc', color: '#909399', fontWeight: 500 }"
      >
        <el-table-column prop="name" label="设备名称" min-width="180" />
        <el-table-column prop="spec" label="默认型号规格" min-width="180">
          <template #default="{ row }">{{ row.spec || '-' }}</template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="140">
          <template #default="{ row }">{{ row.category || '-' }}</template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="180">
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" text bg size="small" @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" text bg size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && rows.length === 0" class="empty">设备库还是空的，点右上角「新增设备」</div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑设备' : '新增设备'" width="440">
      <el-form label-width="90px">
        <el-form-item label="设备名称" required>
          <el-input v-model="form.name" placeholder="如：3D打印机" />
        </el-form-item>
        <el-form-item label="默认规格">
          <el-input v-model="form.spec" placeholder="如：FDM 300x300" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="如：加工设备（可空）" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createCatalogApi,
  deleteCatalogApi,
  getCatalogList,
  updateCatalogApi
} from '@/api/equipmentCatalog'

const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const form = reactive({ id: null, name: '', spec: '', category: '', description: '' })

const load = async () => {
  loading.value = true
  try {
    const res = await getCatalogList()
    if (res.code === 200) rows.value = res.data || []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, { id: null, name: '', spec: '', category: '', description: '' })
  dialogVisible.value = true
}

const openEdit = (row) => {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    spec: row.spec || '',
    category: row.category || '',
    description: row.description || ''
  })
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请输入设备名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      spec: form.spec.trim() || null,
      category: form.category.trim() || null,
      description: form.description.trim() || null
    }
    const res = form.id
      ? await updateCatalogApi(form.id, payload)
      : await createCatalogApi(payload)
    if (res.code === 200) {
      ElMessage.success(form.id ? '修改成功' : '已加入设备库')
      dialogVisible.value = false
      load()
    }
  } finally {
    saving.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`从设备库删除「${row.name}」？`, '确认删除', { type: 'warning' })
    .then(async () => {
      const res = await deleteCatalogApi(row.id)
      if (res.code === 200) {
        ElMessage.success('已删除')
        load()
      }
    })
    .catch(() => {})
}

onMounted(load)
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
.empty {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 20px 0;
}
</style>
