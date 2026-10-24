<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center">
          <span style="font-size: 16px; font-weight: bold">公告</span>
          <el-button
            v-if="isAdmin"
            type="primary"
            size="small"
            style="margin-left: auto"
            @click="openCreate"
          >
            发布公告
          </el-button>
        </div>
      </template>

      <div v-loading="loading">
        <el-empty v-if="!loading && !rows.length" description="还没有公告" />
        <div v-for="item in rows" :key="item.id" class="notice">
          <div class="head">
            <span class="title">{{ item.title }}</span>
            <!-- 发布人/主管理员标签只给管理员看，普通用户只看标题和时间 -->
            <el-tag
              v-if="isAdmin && item.is_primary_author"
              size="small"
              type="danger"
              effect="plain"
            >
              主管理员
            </el-tag>
            <span class="meta">
              <template v-if="isAdmin">{{ item.author_name || '管理员' }} · </template>
              {{ item.create_time?.replace('T', ' ').slice(0, 16) }}
            </span>
            <el-button
              v-if="item.can_edit"
              type="primary"
              text
              size="small"
              :style="item.can_delete ? '' : 'margin-left: auto'"
              @click="openEdit(item)"
            >
              编辑
            </el-button>
            <el-button
              v-if="item.can_delete"
              type="danger"
              text
              size="small"
              :style="item.can_edit ? '' : 'margin-left: auto'"
              @click="handleDelete(item)"
            >
              删除
            </el-button>
          </div>
          <div class="content">{{ item.content }}</div>
        </div>
      </div>

      <div v-if="isAdmin" class="tip">
        主管理员可以删除任何人的公告；普通管理员只能删除自己发布的。
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑公告' : '发布公告'" width="520">
      <el-form label-width="70px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" maxlength="100" show-word-limit placeholder="一句话说清楚" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            maxlength="1000"
            show-word-limit
            placeholder="公告正文"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ form.id ? '保存' : '发布' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createAnnouncementApi,
  deleteAnnouncementApi,
  getAnnouncementsApi,
  updateAnnouncementApi
} from '@/api/announcement'

const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const form = reactive({ id: null, title: '', content: '' })

const userInfo = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('userInfo') || '{}')
  } catch {
    return {}
  }
})
const isAdmin = computed(() => userInfo.value?.role === 'admin')

const load = async () => {
  loading.value = true
  try {
    const res = await getAnnouncementsApi()
    if (res.code === 200) rows.value = res.data || []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  form.id = null
  form.title = ''
  form.content = ''
  dialogVisible.value = true
}

const openEdit = (item) => {
  form.id = item.id
  form.title = item.title
  form.content = item.content
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('标题和内容都要填')
    return
  }
  saving.value = true
  try {
    const payload = { title: form.title.trim(), content: form.content.trim() }
    const res = form.id
      ? await updateAnnouncementApi(form.id, payload)
      : await createAnnouncementApi(payload)
    if (res.code === 200) {
      ElMessage.success(form.id ? '已保存' : '已发布')
      dialogVisible.value = false
      load()
    }
  } finally {
    saving.value = false
  }
}

const handleDelete = (item) => {
  ElMessageBox.confirm(`删除公告「${item.title}」？`, '确认删除', { type: 'warning' })
    .then(async () => {
      const res = await deleteAnnouncementApi(item.id)
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
.notice {
  border-bottom: 1px solid #f0f2f5;
  padding: 14px 2px;
}
.notice:last-child {
  border-bottom: none;
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.meta {
  font-size: 12px;
  color: #909399;
}
.content {
  margin-top: 8px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
}
.tip {
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
}
</style>
