<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold; display: flex; align-items: center">
          <span>AI智能助手</span>
          <el-tag v-if="effectiveModel" size="small" type="info" style="margin-left: 10px">
            当前模型：{{ effectiveModel }}（{{ sourceLabel }}）
          </el-tag>
          <el-button size="small" style="margin-left: auto" @click="openConfig">模型配置</el-button>
        </div>
      </template>

      <div
        ref="listRef"
        style="
          height: 480px;
          overflow-y: auto;
          padding: 8px 4px;
          background-color: #fafafa;
          border-radius: 6px;
        "
      >
        <div
          v-for="(item, index) in messages"
          :key="index"
          :style="{
            display: 'flex',
            justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start',
            marginBottom: '12px'
          }"
        >
          <div
            :style="{
              maxWidth: '70%',
              padding: '10px 12px',
              borderRadius: '8px',
              backgroundColor: item.role === 'user' ? '#409eff' : '#fff',
              color: item.role === 'user' ? '#fff' : '#333',
              lineHeight: '1.6',
              boxShadow: '0 1px 2px rgba(0, 0, 0, 0.06)'
            }"
          >
            <!-- 当前进行中的一句话，如「正在查询开放实验室…」 -->
            <div
              v-if="item.role === 'assistant' && item.status"
              style="margin-bottom: 6px; font-size: 12px; color: #909399"
            >
              {{ item.status }}
            </div>
            <!-- 本轮已发生的过程列表，只展示不回传给后端 -->
            <div
              v-if="item.role === 'assistant' && item.steps?.length"
              style="margin-bottom: 8px; font-size: 12px; color: #909399; line-height: 1.5"
            >
              <div v-for="(step, i) in item.steps" :key="i">· {{ step }}</div>
            </div>
            <div v-html="parseMarkdown(item.content)"></div>
          </div>
        </div>
      </div>
      <!-- 输入框 -->
      <div style="margin-top: 12px; display: flex; gap: 8px; align-items: flex-end">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          placeholder="问问实验室怎么预约、开放时间..."
          @keydown.enter.exact.prevent="handleSend"
          @keydown.enter.shift.stop
        ></el-input>
        <el-button type="primary" @click="handleSend" :loading="loading">发送</el-button>
      </div>
    </el-card>

    <el-dialog v-model="configVisible" title="模型配置" width="540">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 14px"
        :title="configHint"
      />
      <el-form label-width="90px">
        <el-form-item label="接口地址">
          <el-input
            v-model="cfg.base_url"
            placeholder="http://127.0.0.1:11434/v1 或 https://api.deepseek.com/v1"
          />
        </el-form-item>
        <el-form-item label="模型名">
          <el-input v-model="cfg.model" placeholder="qwen-local:latest / deepseek-chat" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="cfg.api_key"
            type="password"
            show-password
            :placeholder="
              myConfig?.has_key
                ? '已配置，留空表示不修改（任何人都看不到原 Key）'
                : '请输入 API Key'
            "
          />
        </el-form-item>
      </el-form>
      <div style="font-size: 12px; color: #909399; line-height: 1.9">
        · Key 只以密文保存在服务器，页面永远只显示「已配置」，主管理员也看不到<br />
        · 不配置自己的模型时，会自动使用系统默认配置
      </div>
      <template #footer>
        <el-button v-if="myConfig" type="danger" plain @click="clearMineConfig">
          清除我的配置
        </el-button>
        <el-button @click="configVisible = false">取消</el-button>
        <el-button type="primary" :loading="cfgSaving" @click="saveCfg">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { chatStreamApi } from '@/api/ai'
import {
  deleteMyAIConfig,
  getMyAIConfig,
  saveMyAIConfig
} from '@/api/aiConfig'
import { ref, reactive, computed, nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getUserInfo } from '@/utils/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify' // 过滤危险的 HTML，防止 XSS 攻击

// AI_CHAT_SESSION_CACHE_V1
const chatUser = getUserInfo()
const chatCacheKey = chatUser?.id != null
  ? `ai-chat-messages:v1:${chatUser.role || 'user'}:${chatUser.id}`
  : null

const readChatMessages = (fallback) => {
  if (!chatCacheKey) return fallback
  try {
    const cached = JSON.parse(sessionStorage.getItem(chatCacheKey))
    if (
      Array.isArray(cached) &&
      cached.length > 0 &&
      cached.every(item =>
        item &&
        ['user', 'assistant'].includes(item.role) &&
        typeof item.content === 'string'
      )
    ) {
      return cached.map(({ role, content }) => ({ role, content }))
    }
  } catch {
    // 缓存不可用时正常显示初始消息
  }
  return fallback
}

const messages = ref(readChatMessages([
  {
    role: 'assistant',
    content:
      '您好，我是实验室助手。你可以向我提问怎么预约、取消。也可以说（帮我预约明天下午的科学实验室），确认后我会帮你提交'
  }
]))
const input = ref('')
const loading = ref(false)
const listRef = ref()

// ===== 模型配置 =====
const configVisible = ref(false)
const cfgSaving = ref(false)
const myConfig = ref(null)
const defaultConfig = ref(null)
const effectiveSource = ref('none')
const effectiveModel = ref('')
const cfg = reactive({ base_url: '', model: '', api_key: '' })

const SOURCE_TEXT = {
  mine: '我的配置',
  default: '系统默认',
  env: '服务器默认',
  none: '未配置'
}
const sourceLabel = computed(() => SOURCE_TEXT[effectiveSource.value] || '未配置')

const configHint = computed(() => {
  if (myConfig.value?.has_key) {
    return `当前生效：我的配置（${effectiveModel.value || '—'}）`
  }
  if (effectiveSource.value === 'default' || effectiveSource.value === 'env') {
    return `当前生效：${sourceLabel.value}（${effectiveModel.value || '—'}）。想用自己的模型，填在下面保存即可`
  }
  return '还没有可用的模型配置，请填写接口地址、模型名和 API Key'
})

const loadConfig = async () => {
  try {
    const res = await getMyAIConfig()
    if (res.code !== 200) return
    myConfig.value = res.data?.my_config || null
    defaultConfig.value = res.data?.default_config || null
    effectiveSource.value = res.data?.effective_source || 'none'
    effectiveModel.value = res.data?.effective_model || ''
  } catch {
    // 拿不到配置不影响聊天
  }
}

const openConfig = async () => {
  await loadConfig()
  const base = myConfig.value || defaultConfig.value
  cfg.base_url = base?.base_url || ''
  cfg.model = base?.model || ''
  cfg.api_key = ''
  configVisible.value = true
}

const saveCfg = async () => {
  if (!cfg.base_url.trim() || !cfg.model.trim()) {
    ElMessage.warning('接口地址和模型名都要填')
    return
  }
  if (!myConfig.value?.has_key && !cfg.api_key.trim()) {
    ElMessage.warning('第一次配置必须填 API Key')
    return
  }
  cfgSaving.value = true
  try {
    const res = await saveMyAIConfig({
      base_url: cfg.base_url.trim(),
      model: cfg.model.trim(),
      api_key: cfg.api_key.trim() || null
    })
    if (res.code === 200) {
      ElMessage.success('已保存，之后的对话用你的配置')
      configVisible.value = false
      cfg.api_key = ''
      await loadConfig()
    }
  } finally {
    cfgSaving.value = false
  }
}

const clearMineConfig = () => {
  ElMessageBox.confirm('删除后你会改用系统默认配置，确定？', '提示', { type: 'warning' })
    .then(async () => {
      const res = await deleteMyAIConfig()
      if (res.code === 200) {
        ElMessage.success('已清除')
        configVisible.value = false
        await loadConfig()
      }
    })
    .catch(() => {})
}

const scrollToBottom = () => {
  nextTick(() => {
    const elem = listRef.value
    if (elem) elem.scrollTop = elem.scrollHeight
  })
}

watch(
  () => messages.value.map(({ role, content }) => ({ role, content })),
  history => {
    if (!chatCacheKey) return
    try {
      sessionStorage.setItem(
        chatCacheKey,
        JSON.stringify(history.filter(item => item.content.trim()))
      )
    } catch {
      // 存储不可用或空间不足时，不影响对话
    }
  },
  { deep: true }
)

onMounted(() => {
  scrollToBottom()
  loadConfig()
  applyQueryPrompt()
})

// 从首页的「知识库问答 / 智能 Agent」卡片进来时，把预设问题填到输入框（不自动发送）
const route = useRoute()
const applyQueryPrompt = () => {
  const q = route.query?.q
  if (typeof q === 'string' && q.trim()) {
    input.value = q.trim()
  }
}
watch(() => route.query?.q, applyQueryPrompt)

const handleSend = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  scrollToBottom()

  // 必须用 reactive：普通对象 push 后再改字段，视图可能不更新
  const assistant = reactive({
    role: 'assistant',
    content: '', // 正文：靠 token 一点点拼
    status: '正在思考…', // 当前状态文案
    steps: [] // 过程流水，不进下次 history
  })
  messages.value.push(assistant)

  const history = messages.value
    .filter((item) => item.role === 'user' || item.role === 'assistant')
    .slice(0, -1) // 去掉刚插入的空助手，避免把空 content 送回去
    // 只保留 role/content；status、steps 丢掉
    .map(({ role, content }) => ({ role, content }))

  try {
    // 第二个参数是回调：每解析出一条 SSE 事件就进一次
    await chatStreamApi({ messages: history }, (evt) => {
      if (evt.type === 'status') {
        assistant.status = evt.message || '正在思考…'
      } else if (evt.type === 'tool_start') {
        const label = evt.label || evt.name || '工具'
        assistant.status = `正在${label}…`
        assistant.steps.push(`开始：${label}`)
      } else if (evt.type === 'tool_end') {
        const label = evt.label || evt.name || '工具'
        assistant.status = `${label}完成`
        assistant.steps.push(`完成：${label}`)
        if (evt.preview) {
          assistant.steps.push(`输出结果${evt.preview}`)
        }
      } else if (evt.type === 'token') {
        assistant.content += evt.content || '' // 打字机：追加，不是覆盖
        assistant.status = '' // 开始出字后清掉「正在…」，避免叠在一起
      } else if (evt.type === 'done') {
        assistant.status = ''
        // 注意：不要在这里再 append 一整段正文，否则会双份
      } else if (evt.type === 'error') {
        assistant.status = ''
        if (!assistant.content) {
          assistant.content = evt.message || '请求失败'
        }
        ElMessage.error(evt.message || '请求失败')
      }
      scrollToBottom()
    })
  } catch (err) {
    assistant.status = ''
    if (!assistant.content) {
      assistant.content = err.message || '网络异常'
    }
    ElMessage.error(err.message || '网络异常')
  } finally {
    loading.value = false
    assistant.status = ''
    scrollToBottom()
  }
}

// 将 markdown 字符串转换为安全的 HTML 字符串
const parseMarkdown = (text) => {
  if (!text) return ''
  marked.setOptions({ breaks: true }) // 把 \n 转换成 <br>
  // 使用 marked 解析，然后用 DOMPurify 清理
  const rawHtml = marked.parse(text)
  return DOMPurify.sanitize(rawHtml)
}
</script>
