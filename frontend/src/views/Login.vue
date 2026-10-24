<template>
  <div class="login-container">
    <div class="login-box">
      <h1 style="font-size: 28px">实验室预约系统</h1>
      <div class="subtitle">基于Agent智能预约系统</div>

      <el-form ref="formRef" :rules="rules" :model="form" label-width="0px" style="width: 100%">
        <el-form-item prop="username">
          <el-input
            size="large"
            v-model="form.username"
            :placeholder="isAdmin ? '请输入管理员账号' : '请输入学生账号'"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            type="password"
            size="large"
            v-model="form.password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="login"
          />
        </el-form-item>
        <div>
          <el-button size="large" type="primary" style="width: 100%" @click="login" :loading="loadingValue">
            {{ isAdmin ? '管理员登录' : '登 录' }}
          </el-button>

          <div class="links">
            <router-link to="/register">注册账号</router-link>
            <span class="divider">|</span>
            <span class="link" @click="toggleAdmin">
              {{ isAdmin ? '返回学生登录' : '管理员登录' }}
            </span>
          </div>

          <div v-if="isAdmin" class="login-tip">
            管理员账号由主管理员创建，或注册后经主管理员审核通过
          </div>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { loginApi } from '@/api/auth'
import { useUser } from '@/utils/user'

const { saveLoginData } = useUser()

const formRef = ref()

// student = 普通登录，admin = 管理员登录（默认学生，管理员入口放在下面小字里）
const loginType = ref('student')
const isAdmin = computed(() => loginType.value === 'admin')

const form = reactive({
  username: '',
  password: ''
})

const loadingValue = ref(false)

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 切换入口时清掉校验提示，避免上一个入口的错误信息留在表单上
watch(loginType, () => {
  formRef.value?.clearValidate()
})

const toggleAdmin = () => {
  loginType.value = isAdmin.value ? 'student' : 'admin'
}

const login = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loadingValue.value = true
  try {
    const res = await loginApi({ ...form, role: loginType.value })
    if (res.code === 200) {
      saveLoginData(res.data)
      ElMessage.success(res.data.user?.role === 'admin' ? '管理员登录成功' : '登录成功')
      await router.push('/manager/home')
    }
  } finally {
    loadingValue.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
.login-box {
  width: min(400px, calc(100vw - 32px));
  border-radius: 8px;
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1);
  padding: 30px;
  text-align: center;
  background-color: white;
}
.subtitle {
  margin-top: 5px;
  margin-bottom: 24px;
  color: #909399;
  font-size: 13px;
}

.links {
  margin-top: 18px;
  font-size: 13px;
  color: #909399;
}
.links a {
  color: var(--el-color-primary);
}
.divider {
  margin: 0 8px;
  color: #dcdfe6;
}
.link {
  color: #c0c4cc;
  cursor: pointer;
}
.link:hover {
  color: var(--el-color-primary);
}

.login-tip {
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}
</style>
