<template>
  <div class="user-page">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="page-head">
          <div class="head-text">
            <h2>
              用户管理
              <span class="count-badge">{{ total }}</span>
            </h2>
            <p>管理学生与管理员账号、角色和登录密码</p>
          </div>
          <div class="head-actions">
            <el-input
              placeholder="请输入账号或名称查询"
              v-model="params.keywords"
              style="width: 220px"
              clearable
              :prefix-icon="Search"
              @keyup.enter="handleSearch"
              @clear="handleSearch"
            ></el-input>
            <el-button @click="handleSearch">查询</el-button>
            <el-button type="primary" :icon="Plus" @click="handleCreate">新增</el-button>
            <el-button type="warning" plain :icon="UserFilled" @click="handleCreateAdmin">
              添加管理员
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :header-cell-style="{ backgroundColor: '#fafbfc', color: '#909399', fontWeight: 500 }"
        :data="tableData"
        row-key="id"
        class="user-table"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column label="用户" min-width="210">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="34" :src="row.avatar || undefined" class="user-avatar">
                {{ (row.name || row.username || '?').slice(0, 1) }}
              </el-avatar>
              <div class="user-meta">
                <div class="user-name">{{ row.name || row.username }}</div>
                <div class="user-account">@{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="联系方式" min-width="200" class-name="hide-mobile" label-class-name="hide-mobile">
          <template #default="{ row }">
            <div class="contact" :class="{ empty: !row.email }">{{ row.email || '—' }}</div>
            <div v-if="row.phone" class="contact-sub">{{ row.phone }}</div>
          </template>
        </el-table-column>

        <el-table-column label="角色" width="130">
          <template #default="{ row }">
            <el-tag v-if="row.is_primary" type="danger" effect="light" size="small">
              主管理员
            </el-tag>
            <el-tag v-else-if="row.role === 'admin'" type="warning" effect="light" size="small">
              管理员
            </el-tag>
            <el-tag v-else type="primary" effect="light" size="small">学生</el-tag>
            <div v-if="row.pending_admin === 1" class="pending-hint">申请管理员中</div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.pending_admin === 1" type="warning" size="small" effect="dark">
              待审核
            </el-tag>
            <span v-else class="status-dot" :class="row.status === 1 ? 'on' : 'off'">
              {{ row.status === 1 ? '正常' : '禁用' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <!-- 待审核的管理员申请：主管理员直接处理 -->
            <template v-if="row.pending_admin === 1 && isPrimaryUser">
              <div class="row-actions approve" style="gap: 10px">
                <el-button type="success" size="small" @click="handleApplication(row, true)">
                  通过
                </el-button>
                <el-button type="danger" size="small" plain @click="handleApplication(row, false)">
                  拒绝
                </el-button>
              </div>
            </template>

            <template v-else>
              <div class="row-actions">
                <el-button link class="act-main" @click="handleEdit(row)">编辑</el-button>
                <span v-if="canResetPassword(row)" class="act-sep"></span>
                <el-button
                  v-if="canResetPassword(row)"
                  link
                  class="act-sub"
                  @click="openResetPassword(row)"
                  >重置密码</el-button
                >
                <span v-if="hasMoreActions(row)" class="act-sep"></span>
                <el-dropdown
                  v-if="hasMoreActions(row)"
                  trigger="click"
                  @command="(cmd) => handleMore(cmd, row)"
                >
                  <el-button link class="act-more">
                    更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        v-if="isPrimaryUser && !row.is_primary"
                        command="role"
                      >
                        {{ row.role === 'admin' ? '取消管理员' : '设为管理员' }}
                      </el-dropdown-item>
                      <el-dropdown-item command="delete" :disabled="!!deleteTip(row)">
                        <span :style="deleteTip(row) ? '' : 'color:#f56c6c'">删除账号</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 10px; display: flex; justify-content: flex-end">
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="450">
      <el-alert
        v-if="form.is_primary"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 8px"
        title="主管理员账号受保护：不可删除、降级为普通用户或被禁用"
      />
      <el-alert
        v-if="adminMode"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 8px"
        title="新增的管理员拥有全部权限：实验室管理、设备管理、用户管理、预约审核"
      />
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="80px"
        style="width: 100%; padding-right: 30px; padding-top: 16px"
        v-loading="loading"
      >
        <el-form-item label="账号" prop="username">
          <!-- form.id 有值 那就disabled  也就是编辑的情形 -->
          <el-input :disabled="!!form.id" v-model="form.username" placeholer="请输入账号" />
        </el-form-item>
        <el-form-item v-if="!form.id" label="密码" prop="password">
          <el-input type="password" show-password v-model="form.password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholer="请输入名称" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" :disabled="adminMode || form.is_primary || !isPrimaryUser">
            <el-option label="学生" value="student"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
          <div v-if="!isPrimaryUser && !adminMode" style="font-size: 12px; color: #909399">
            只有主管理员可以调整用户角色
          </div>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholer="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholer="请输入手机号" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status" :disabled="form.is_primary">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="resetVisible" title="重置密码" width="420">
      <div class="reset-tip">
        正在为
        <b>{{ resetRow?.name || resetRow?.username }}</b>
        （{{ resetRow?.username }}）重置登录密码。
      </div>
      <el-input
        v-model="resetPwdForm.password"
        placeholder="留空则自动生成 8 位随机密码"
        show-password
        maxlength="30"
      />
      <div class="reset-hint">密码至少 6 位；重置后对方原来的密码立即失效。</div>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetSaving" @click="submitResetPassword">
          确定重置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Search, Plus, UserFilled, ArrowDown } from '@element-plus/icons-vue'
import {
  auditAdminApplicationApi,
  createUserApi,
  deleteUserApi,
  getUserInfo as getUserMeApi,
  getUserPageList,
  resetPasswordApi,
  updateUserApi
} from '@/api/user'
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUser } from '@/utils/user'

const { userInfo, updateUser } = useUser()
// 当前登录人是否主管理员：决定能不能删除/降级其他管理员
const isPrimaryUser = computed(() => userInfo.value?.is_primary === true)

// ===== 重置密码 =====
const resetVisible = ref(false)
const resetSaving = ref(false)
const resetRow = ref(null)
const resetPwdForm = reactive({ password: '' })

const canResetPassword = (row) => {
  if (!row || row.id === userInfo.value?.id) return false // 自己用「修改密码」
  if (row.is_primary) return false // 主管理员密码不能被重置
  if (row.role === 'admin' && !isPrimaryUser.value) return false // 管理员密码只有主管理员能重置
  return true
}

const openResetPassword = (row) => {
  resetRow.value = row
  resetPwdForm.password = ''
  resetVisible.value = true
}

const submitResetPassword = async () => {
  resetSaving.value = true
  try {
    const res = await resetPasswordApi(resetRow.value.id, resetPwdForm.password.trim() || null)
    if (res.code === 200) {
      resetVisible.value = false
      ElMessageBox.alert(
        `「${resetRow.value.name || resetRow.value.username}」的新密码是：${res.data.password}\n请把新密码告诉对方，登录后可以自己再改。`,
        '密码已重置',
        { confirmButtonText: '知道了', type: 'success' }
      )
    }
  } finally {
    resetSaving.value = false
  }
}

const params = reactive({
  page: 1,
  pageSize: 10,
  keywords: ''
})
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
// true 表示走「添加管理员」流程：角色锁定为 admin
const adminMode = ref(false)
const dialogTitle = computed(() => {
  if (form.id) return '编辑'
  return adminMode.value ? '添加管理员' : '新增'
})
const formRef = ref()
const form = reactive({
  username: '',
  name: '',
  role: 'student',
  email: '',
  phone: '',
  avatar: '',
  status: 1,
  is_primary: false,
  original_role: ''
})
const formLoading = ref(false)

// 行内「删除」是否禁用，以及禁用原因
const deleteTip = (row) => {
  if (row.is_primary) return '主管理员账号不可删除'
  if (row.role === 'admin' && !isPrimaryUser.value) return '只有主管理员可以删除管理员账号'
  return ''
}

// 「更多」里有没有可点的项（没有就不显示下拉）
const hasMoreActions = (row) => {
  const canToggleRole = isPrimaryUser.value && !row.is_primary && row.pending_admin !== 1
  return canToggleRole || !deleteTip(row)
}

const handleMore = (command, row) => {
  if (command === 'role') toggleRole(row)
  if (command === 'delete') handleDelete(row)
}

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 3, max: 10, message: '密码是3-10位', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式错误', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式错误', trigger: 'blur' }]
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    username: '',
    name: '',
    role: 'student',
    email: '',
    phone: '',
    avatar: '',
    status: 1,
    is_primary: false,
    original_role: ''
  })
}

const handleCreate = () => {
  resetForm()
  adminMode.value = false
  dialogVisible.value = true
}

// 添加管理员：打开同一个表单，角色预设并锁定为 admin
const handleCreateAdmin = () => {
  resetForm()
  form.role = 'admin'
  adminMode.value = true
  dialogVisible.value = true
}

const handleEdit = (row) => {
  resetForm()
  adminMode.value = false
  Object.assign(form, {
    id: row.id,
    username: row.username,
    name: row.name,
    role: row.role,
    email: row.email,
    phone: row.phone,
    avatar: row.avatar,
    status: row.status,
    is_primary: !!row.is_primary,
    original_role: row.role
  })
  dialogVisible.value = true
}

// 主管理员：一键把学生设为管理员 / 把管理员降为普通用户
const toggleRole = (row) => {
  const toAdmin = row.role !== 'admin'
  const action = toAdmin ? '设为管理员' : '取消管理员'
  ElMessageBox.confirm(
    toAdmin
      ? `把「${row.name}」设为管理员？他会拥有实验室/设备/用户管理和预约审核权限。`
      : `取消「${row.name}」的管理员身份？他将变回普通学生，不能再进管理菜单。`,
    action,
    { type: 'warning', confirmButtonText: action, cancelButtonText: '取消' }
  )
    .then(async () => {
      const res = await updateUserApi(row.id, { role: toAdmin ? 'admin' : 'student' })
      if (res.code === 200) {
        ElMessage.success(toAdmin ? '已设为管理员' : '已取消管理员身份')
        load()
      }
    })
    .catch(() => {})
}

// 删除用户信息
const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除用户 [${row.username}] ？`, '确认删除', { type: 'warning' }).then(
    async () => {
      const res = await deleteUserApi(row.id)
      if (res.code === 200) {
        ElMessage.success('删除用户成功')
        load()
      }
    }
  )
}

// 保存用户
const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  formLoading.value = true
  try {
    const res = form.id ? await updateUserApi(form.id, form) : await createUserApi(form)
    if (res.code === 200) {
      const msg = form.id ? '修改成功' : adminMode.value ? '管理员已添加' : '添加成功'
      dialogVisible.value = false
      adminMode.value = false
      ElMessage.success(msg)
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
    const res = await getUserPageList({
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

// 审核「注册为管理员」的申请
const handleApplication = (row, approve) => {
  const action = approve ? '通过' : '拒绝'
  const tip = approve
    ? `通过「${row.name}」的管理员申请？通过后他可以用「管理员登录」进入后台。`
    : `拒绝「${row.name}」的管理员申请？账号会作为普通学生启用。`
  ElMessageBox.confirm(tip, `${action}管理员申请`, { type: 'warning' })
    .then(async () => {
      const res = await auditAdminApplicationApi(row.id, approve)
      if (res.code === 200) {
        ElMessage.success(approve ? '已通过，并通知了申请人' : '已拒绝，账号已作为学生启用')
        load()
      }
    })
    .catch(() => {})
}

const handleSearch = async () => {
  params.page = 1
  load()
}

onMounted(async () => {
  // 刷新当前登录人信息，拿到最新的 is_primary（老会话的 localStorage 里没有这个字段）
  try {
    const me = await getUserMeApi()
    if (me.code === 200) updateUser(me.data)
  } catch (e) {
    /* 忽略：拿不到就按普通管理员处理，按钮只会更保守 */
  }
  load()
})
</script>

<style scoped>
.user-page {
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

.row-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}
/* 通过 / 拒绝 这类实心按钮要留出间距，不能贴一起 */
.row-actions.approve {
  gap: 8px;
}
.row-actions.approve .el-button {
  height: 26px;
  padding: 0 12px;
}
.row-actions .el-button {
  margin-left: 0;
  padding: 0 4px;
  height: 24px;
}
.act-main {
  color: var(--el-color-primary);
  font-weight: 500;
}
.act-sub {
  color: #606266;
}
.act-sub:hover {
  color: var(--el-color-primary);
}
.act-more {
  color: #a8abb2;
}
.act-more:hover {
  color: var(--el-color-primary);
}
.act-sep {
  width: 1px;
  height: 12px;
  background: #ebeef5;
  margin: 0 2px;
}

.user-table :deep(td) {
  padding: 10px 0;
}
.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user-avatar {
  background: #eef6ff;
  color: #409eff;
  font-weight: 600;
  flex-shrink: 0;
}
.user-name {
  font-size: 14px;
  color: #303133;
  line-height: 1.4;
}
.user-account {
  font-size: 12px;
  color: #a8abb2;
}
.contact {
  font-size: 13px;
  color: #606266;
}
.contact.empty {
  color: #d0d3d9;
}
.contact-sub {
  font-size: 12px;
  color: #a8abb2;
  margin-top: 2px;
}
.pending-hint {
  margin-top: 3px;
  font-size: 11px;
  color: #e6a23c;
}
.status-dot {
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.status-dot::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.status-dot.on {
  color: #67c23a;
}
.status-dot.off {
  color: #f56c6c;
}

.reset-tip {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.7;
}
.reset-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #a8abb2;
}
</style>
