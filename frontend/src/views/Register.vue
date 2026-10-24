<template>
  <div class="register-container">
    <div class="register-box">
      <h1 style="font-size: 24px">
        {{ isAdmin ? '申请管理员账号' : '注册账号' }}
      </h1>
      <div class="subtitle">实验室预约系统</div>

      <el-alert
        v-if="isAdmin"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 14px; text-align: left"
        title="管理员账号需要主管理员审核，通过后才能用「管理员登录」进入"
      />

      <el-form ref="formRef" :rules="rules" :model="form" label-width="0px" style="width: 100%">
        <el-form-item prop="username">
          <el-input
            size="large"
            v-model="form.username"
            placeholder="请输入账号"
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
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            type="password"
            size="large"
            v-model="form.confirmPassword"
            placeholder="请确认密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item v-if="isAdmin" prop="apply_note">
          <el-input
            v-model="form.apply_note"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="申请说明（至少 5 个字），例如：负责实验室排期与预约审核，需要管理员权限"
          />
        </el-form-item>
        <div>
          <el-button
            size="large"
            type="primary"
            :loading="loadingValue"
            style="width: 100%"
            @click="register"
            >{{ isAdmin ? '提交申请' : '注 册' }}</el-button
          >
          <div class="links">
            <router-link to="/login">已有账号，去登录</router-link>
            <span class="divider">|</span>
            <span class="link" @click="toggleAdmin">
              {{ isAdmin ? '返回学生注册' : '我是老师/管理员' }}
            </span>
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
import { registerApi } from '@/api/auth'
import router from '@/router'

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'student',
  apply_note: ''
})

// 管理员申请入口默认隐藏，点下面小字才切过来
const isAdmin = computed(() => form.role === 'admin')

const loadingValue = ref(false)

const formRef = ref()

const toggleAdmin = () => {
  form.role = isAdmin.value ? 'student' : 'admin'
  if (!isAdmin.value) form.apply_note = ''
  formRef.value?.clearValidate()
}

watch(isAdmin, () => {
  formRef.value?.clearValidate()
})

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else {
    if (value !== form.password) {
      callback(new Error('两次密码输入不一致'))
    } else {
      callback()
    }
  }
}
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ validator: validatePass, trigger: 'blur' }],
  apply_note: [
    {
      validator: (rule, value, callback) => {
        if (form.role === 'admin' && (!value || value.trim().length < 5)) {
          callback(new Error('申请说明至少 5 个字'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const register = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loadingValue.value = true
  try {
    const res = await registerApi({
      username: form.username,
      password: form.password,
      role: form.role,
      apply_note: form.role === 'admin' ? form.apply_note.trim() : null
    })
    if (res.code === 200) {
      if (form.role === 'admin') {
        ElMessage.success('管理员申请已提交，请等主管理员审核')
      } else {
        ElMessage.success('注册成功')
      }
      await router.push('/login')
    }
  } finally {
    loadingValue.value = false
  }
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
.register-box {
  width: min(380px, calc(100vw - 32px));
  border-radius: 8px;
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1);
  padding: 30px;
  text-align: center;
  background-color: white;
}
.subtitle {
  font-size: 13px;
  color: #909399;
  margin: 6px 0 20px;
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
</style>
