<template>
  <div class="page">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="page-head">
          <div class="head-text">
            <h2>
              实验室管理
              <span class="count-badge">{{ total }}</span>
            </h2>
            <p>维护实验室的开放时间、容量，以及每间实验室里的设备</p>
          </div>
          <div class="head-actions">
            <el-input
              placeholder="请输入名称查询"
              v-model="params.keywords"
              style="width: 220px"
              clearable
              :prefix-icon="Search"
              @keyup.enter="handleSearch"
              @clear="handleSearch"
            ></el-input>
            <el-button @click="handleSearch">查询</el-button>
            <el-button type="primary" :icon="Plus" @click="handleCreate">新增</el-button>
          </div>
        </div>
      </template>

      <el-table
        :header-cell-style="{ backgroundColor: '#fafbfc', color: '#909399', fontWeight: 500 }"
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="简介" class-name="hide-mobile" label-class-name="hide-mobile" />
        <el-table-column prop="img" label="封面" class-name="hide-mobile" label-class-name="hide-mobile">
          <template #default="{ row }">
            <div style="min-height: 50px">
              <img
                v-if="row.img"
                style="display: block; width: 50px; height: 50px"
                :src="row.img"
                alt=""
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" />
        <el-table-column prop="capacity" label="容量" />
        <el-table-column label="开放时间">
          <template #default="{ row }"> {{ row.open_time }} - {{ row.close_time }} </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '开启' : '关闭' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" text bg @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" text bg @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="params.page"
          v-model:page-size="params.pageSize"
          :total="total"
          background
          layout="total, prev, pager, next"
          @current-change="load"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑' : '新增'"
      width="720"
      class="lab-dialog"
      top="6vh"
    >
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="80px"
        style="width: 100%; padding-right: 30px; padding-top: 8px"
        v-loading="loading"
      >
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="base">
            <el-form-item label="名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入名称" />
            </el-form-item>
            <el-form-item label="简介">
              <el-input type="textarea" v-model="form.description" placeholder="请输入简介" />
            </el-form-item>
            <el-form-item label="封面">
              <el-upload
                class="avatar-uploader"
                :http-request="handleFileUpload"
                :show-file-list="false"
                accept="image/jpeg,image/png,image/gif,image/webp"
                :before-upload="beforeAvatarUpload"
              >
                <img v-if="form.img" :src="form.img" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
            </el-form-item>
            <el-form-item label="位置">
              <el-input type="textarea" v-model="form.location" placeholder="请输入位置" />
            </el-form-item>
            <el-form-item label="容量" prop="capacity">
              <el-input-number :min="1" v-model="form.capacity" />
            </el-form-item>
            <el-form-item label="开放时间">
              <el-time-picker
                v-model="form.open_time"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="开始时间"
                style="width: 140px; margin-right: 8px"
              />
              <el-time-picker
                v-model="form.close_time"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="结束时间"
                style="width: 140px"
              />
            </el-form-item>
            <el-form-item label="状态">
              <el-radio-group v-model="form.status">
                <el-radio :value="1">正常</el-radio>
                <el-radio :value="0">禁用</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-tab-pane>

          <el-tab-pane :label="`实验室设备（${form.equipments.length}）`" name="equipment">
            <div class="eq-tip">
              设备从「设备库」里选；设备库里还没有的话，点下面的「添加到设备库」先建一条。
              编辑时删掉设备会同步删除（已有预约记录的设备删不了）。
            </div>
            <div v-if="form.equipments.length" class="eq-list">
              <div class="eq-head">
                <span style="width: 200px">设备（来自设备库）</span>
                <span style="width: 160px">型号规格</span>
                <span style="width: 110px">数量</span>
                <span style="width: 100px">状态</span>
                <span style="width: 60px"></span>
              </div>
              <div v-for="(eq, index) in form.equipments" :key="index" class="eq-row">
                <el-select
                  v-model="eq.catalog_id"
                  size="small"
                  filterable
                  placeholder="选择设备"
                  style="width: 200px"
                  @change="onPickCatalog(eq)"
                >
                  <el-option
                    v-for="cat in catalogOptions"
                    :key="cat.id"
                    :label="cat.name"
                    :value="cat.id"
                  />
                </el-select>
                <el-input
                  v-model="eq.spec"
                  size="small"
                  placeholder="默认用设备库的规格"
                  style="width: 160px"
                />
                <el-input-number v-model="eq.quantity" :min="1" size="small" style="width: 110px" />
                <el-select v-model="eq.status" size="small" style="width: 100px">
                  <el-option :value="1" label="正常" />
                  <el-option :value="0" label="维修" />
                </el-select>
                <el-button type="danger" text size="small" @click="removeEquip(index)">
                  删除
                </el-button>
              </div>
            </div>
            <div v-else class="eq-empty">还没有设备，点下面的「添加设备」</div>

            <div style="display: flex; gap: 8px; margin-top: 10px">
              <el-button
                size="small"
                :icon="Plus"
                :disabled="!catalogOptions.length"
                @click="addEquip"
              >
                添加设备
              </el-button>
              <el-button size="small" @click="openCatalogDialog">添加到设备库</el-button>
              <span v-if="!catalogOptions.length" class="eq-empty-hint">
                设备库里还没有设备，先点「添加到设备库」建一条
              </span>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>

    <!-- 往设备库里加一条 -->
    <el-dialog v-model="catalogDialogVisible" title="添加到设备库" width="420">
      <el-form label-width="80px">
        <el-form-item label="设备名称" required>
          <el-input v-model="catalogForm.name" placeholder="如：3D打印机" />
        </el-form-item>
        <el-form-item label="型号规格">
          <el-input v-model="catalogForm.spec" placeholder="如：FDM 300x300" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="catalogForm.category" placeholder="如：加工设备（可空）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="catalogDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="catalogSaving" @click="saveCatalog">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Search, Plus } from '@element-plus/icons-vue'
import {
  createLabApi,
  deleteLabApi,
  getLabPageList,
  saveLabEquipmentsApi,
  updateLabApi
} from '@/api/lab'
import { getEquipmentPageList } from '@/api/equipment'
import { createCatalogApi, getCatalogList } from '@/api/equipmentCatalog'
import { uploadFileApi } from '@/api/file'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const params = reactive({
  page: 1,
  pageSize: 10,
  keywords: ''
})
// 弹窗里的 tab：base（基本信息）/ equipment（设备）
const activeTab = ref('base')
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({
  name: '',
  description: '',
  img: '',
  location: '',
  capacity: 1,
  open_time: '',
  close_time: '',
  status: 1,
  equipments: []
})
const formLoading = ref(false)

// ===== 设备库 =====
const catalogOptions = ref([])
const catalogDialogVisible = ref(false)
const catalogSaving = ref(false)
const catalogForm = reactive({ name: '', spec: '', category: '' })

const loadCatalog = async () => {
  try {
    const res = await getCatalogList()
    if (res.code === 200) catalogOptions.value = res.data || []
  } catch {
    catalogOptions.value = []
  }
}

const rules = {
  name: [{ required: true, message: '请输入实验室名称', trigger: 'blur' }],
  capacity: [{ required: true, message: '请输入容量', trigger: 'blur' }]
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    name: '',
    description: '',
    img: '',
    location: '',
    capacity: 20,
    open_time: '08:00',
    close_time: '18:00',
    status: 1,
    equipments: []
  })
}

// ===== 实验室设备：在实验室弹窗里直接增删改（设备来自设备库） =====
const addEquip = () => {
  if (!catalogOptions.value.length) {
    ElMessage.warning('设备库里还没有设备，先点「添加到设备库」建一条')
    return
  }
  form.equipments.push({
    id: null,
    catalog_id: null,
    name: '',
    spec: '',
    quantity: 1,
    status: 1
  })
}

const removeEquip = (index) => {
  form.equipments.splice(index, 1)
}

// 选中设备库条目后，把名称和默认规格带过来
const onPickCatalog = (eq) => {
  const cat = catalogOptions.value.find((item) => item.id === eq.catalog_id)
  if (!cat) return
  eq.name = cat.name
  if (!eq.spec) eq.spec = cat.spec || ''
}

const openCatalogDialog = () => {
  catalogForm.name = ''
  catalogForm.spec = ''
  catalogForm.category = ''
  catalogDialogVisible.value = true
}

// 设备库里没有 → 就地加一条，并自动选中刚才那一行
const saveCatalog = async () => {
  if (!catalogForm.name.trim()) {
    ElMessage.warning('请输入设备名称')
    return
  }
  catalogSaving.value = true
  try {
    const res = await createCatalogApi({
      name: catalogForm.name.trim(),
      spec: catalogForm.spec.trim() || null,
      category: catalogForm.category.trim() || null
    })
    if (res.code === 200) {
      catalogOptions.value.unshift(res.data)
      // 如果有一行刚添加还没选，自动给它选上
      const emptyRow = form.equipments.find((item) => !item.catalog_id)
      if (emptyRow) {
        emptyRow.catalog_id = res.data.id
        onPickCatalog(emptyRow)
      }
      catalogDialogVisible.value = false
      ElMessage.success('已加入设备库')
    }
  } finally {
    catalogSaving.value = false
  }
}

const loadEquipments = async (labId) => {
  try {
    const res = await getEquipmentPageList({ page: 1, page_size: 100, lab_id: labId })
    if (res.code !== 200) {
      form.equipments = []
      return
    }
    const rows = []
    for (const item of res.data?.list || []) {
      // 老数据没有 catalog_id：按名字在设备库里找，找不到就补一条，保证下拉框能显示
      let catalogId = item.catalog_id
      if (!catalogId) {
        const matched = catalogOptions.value.find((cat) => cat.name === item.name)
        if (matched) {
          catalogId = matched.id
        } else {
          const created = await createCatalogApi({ name: item.name, spec: item.spec })
          if (created.code === 200) {
            catalogOptions.value.unshift(created.data)
            catalogId = created.data.id
          }
        }
      }
      rows.push({
        id: item.id,
        catalog_id: catalogId || null,
        name: item.name,
        spec: item.spec || '',
        quantity: item.quantity,
        status: item.status
      })
    }
    form.equipments = rows
  } catch {
    form.equipments = []
  }
}

const handleCreate = () => {
  resetForm()
  activeTab.value = 'base'
  loadCatalog()
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  resetForm()
  Object.assign(form, {
    id: row.id,
    name: row.name,
    description: row.description,
    img: row.img,
    location: row.location,
    capacity: row.capacity,
    open_time: row.open_time,
    close_time: row.close_time,
    status: row.status
  })
  dialogVisible.value = true
  activeTab.value = 'base'
  await loadCatalog()
  loadEquipments(row.id)
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除实验室 [${row.name}] ？`, '确认删除', { type: 'warning' }).then(
    async () => {
      const res = await deleteLabApi(row.id)
      if (res.code === 200) {
        ElMessage.success('删除成功')
        load()
      }
    }
  )
}

// 保存
const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  // 设备行：必须从设备库选
  const unselected = form.equipments.some((item) => item.id === null && !item.catalog_id)
  if (unselected && form.equipments.length) {
    ElMessage.warning('有设备还没有从设备库选择')
    return
  }
  const equipments = form.equipments
    .filter((item) => item.catalog_id)
    .map((item) => ({
      id: item.id || null,
      catalog_id: item.catalog_id,
      name: item.name,
      spec: item.spec || '',
      quantity: item.quantity || 1,
      status: item.status
    }))
  const names = equipments.map((item) => item.name)
  if (new Set(names).size !== names.length) {
    ElMessage.warning('同一实验室里设备名称不能重复')
    return
  }

  formLoading.value = true
  try {
    const payload = { ...form }
    delete payload.equipments
    const res = form.id ? await updateLabApi(form.id, payload) : await createLabApi(payload)
    if (res.code === 200) {
      // 新建时拿返回的 id 再存设备
      const labId = form.id || res.data?.id
      if (labId) {
        const eqRes = await saveLabEquipmentsApi(labId, equipments)
        if (eqRes.code !== 200) return
      }
      dialogVisible.value = false
      ElMessage.success('操作成功')
      load()
    }
  } finally {
    formLoading.value = false
  }
}

// 加载分页数据
const load = async () => {
  loading.value = true
  try {
    const res = await getLabPageList({
      page: params.page,
      page_size: params.pageSize,
      keywords: params.keywords
    })
    if (res.code === 200) {
      tableData.value = res.data?.list
      total.value = res.data?.total
    }
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  params.page = 1
  load()
}

const beforeAvatarUpload = (file) => {
  const imageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!imageTypes.includes(file.type)) {
    ElMessage.error('只能上传图片')
    return false
  }
  if (file.size / 1024 / 1024 > 2) {
    ElMessage.error('上传图片大小不能超过2M')
    return false
  }
  return true
}

const handleFileUpload = async ({ file }) => {
  try {
    const res = await uploadFileApi(file)
    if (res.code === 200) {
      form.img = res.data?.url
    }
  } catch {}
}

onMounted(() => {
  load()
  loadCatalog()
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
  align-items: center;
}
.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.avatar-uploader .avatar {
  width: 130px;
  height: 130px;
  display: block;
}

.eq-list {
  margin: 0 0 10px 80px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 8px 10px;
  background: #fafbfc;
}
.eq-head {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.eq-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}
.eq-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.7;
  margin-bottom: 10px;
}
.eq-empty {
  font-size: 12px;
  color: #c0c4cc;
  padding: 10px 0;
}
.eq-empty-hint {
  font-size: 12px;
  color: #e6a23c;
  line-height: 32px;
}
</style>
<style>
/* 弹窗里内容较多（带设备清单），让 body 滚动，footer 始终可见 */
.lab-dialog .el-dialog__body {
  max-height: 62vh;
  overflow-y: auto;
}
.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}
.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}
.el-icon.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 130px;
  height: 130px;
  text-align: center;
}
</style>
