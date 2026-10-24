<template>
  <div>
    <el-dialog
      :model-value="visible"
      title="预约"
      width="470"
      @open="onOpen"
      @close="emit('update:visible', false)"
    >
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="80px"
        style="width: 100%; padding-right: 30px; padding-top: 16px"
      >
        <el-form-item label="实验室">
          <el-input :model-value="labName" disabled />
        </el-form-item>
        <el-form-item label="设备">
          <el-input :model-value="equipmentName" disabled />
        </el-form-item>
        <el-form-item label="预约日期" prop="date"
          ><el-date-picker
            v-model="form.date"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            placeholder="请选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="开始时间" prop="startTime"
          ><el-time-picker
            v-model="form.startTime"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="请选择开始时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="endTime"
          ><el-time-picker
            v-model="form.endTime"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="请选择结束时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="使用人数" prop="people">
          <el-input-number v-model="form.people" :min="1" :max="labCapacity || 999" />
          <span v-if="labCapacity" class="hint">最多 {{ labCapacity }} 人（实验室容量）</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input type="textarea" v-model="form.remark" placeholder="请输入备注信息" />
        </el-form-item>
        <div v-if="rulesInfo" class="rules-tip">
          <el-icon><InfoFilled /></el-icon>
          当前规则：最多提前 {{ rulesInfo.advance_days }} 天预约，单次不超过
          {{ rulesInfo.max_hours }} 小时，每人每天最多 {{ rulesInfo.daily_limit }} 次
        </div>
      </el-form>
      <template #footer>
        <el-button @click="emit('update:visible', false)">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { createReservationApi } from '@/api/reservation'
import { getReservationRulesApi } from '@/api/setting'
import { InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref, reactive } from 'vue'

const props = defineProps({
  visible: Boolean,
  labId: Number,
  labName: String,
  labCapacity: Number,
  equipmentId: Number,
  equipmentName: String
})
const submitting = ref(false)
const emit = defineEmits(['update:visible'])
const formRef = ref()
const rulesInfo = ref(null)
const form = reactive({
  date: '',
  startTime: '09:00',
  endTime: '18:00',
  people: 1,
  remark: ''
})
const rules = {
  date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  people: [{ required: true, message: '请填写使用人数', trigger: 'change' }]
}

const onOpen = async () => {
  formRef.value?.resetFields()
  form.people = 1
  try {
    const res = await getReservationRulesApi()
    if (res.code === 200) rulesInfo.value = res.data
  } catch {
    rulesInfo.value = null
  }
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const res = await createReservationApi({
      lab_id: props.labId,
      equipment_id: props.equipmentId,
      date: form.date,
      start_time: form.startTime,
      end_time: form.endTime,
      people: form.people,
      remark: form.remark
    })

    if (res.code === 200) {
      ElMessage.success('预约已提交，AI 正在自动审核，几秒后到「我的预约」看结果')
      emit('update:visible', false)
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.hint {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
.rules-tip {
  margin-left: 80px;
  font-size: 12px;
  color: #909399;
  line-height: 1.8;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
