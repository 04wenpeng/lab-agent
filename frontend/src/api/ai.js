import { getToken } from '@/utils/auth'
import request from '@/utils/request'

/**
 * AI对话请求
 */
export function chatApi(data) {
  return request({
    url: '/api/ai/chat',
    method: 'post',
    data,
    timeout: 90000
  })
}

/**
 * 流式对话请求
 */
export async function chatStreamApi(data, onEvent) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL
  const token = getToken()
  const res = await fetch(`${baseUrl}/api/ai/chat/stream`, {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(data)
  })
  if (res.status === 401) {
    throw new Error('登录已失效， 请重新登录')
  }
  if (!res.ok || !res.body) {
    throw new Error('流式接口请求失败')
  }
  const contentType = res.headers.get('content-type')
  if (!contentType.includes('text/event-stream')) {
    throw new Error('流式接口返回异常')
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read() // {done: true, value: {}}
    if (done) break // 结束的标识
    buffer += decoder.decode(value, { stream: true }) //  stream: true 表示后面可能还要字节

    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() // buffer可能是不完整的内容  留着到下一轮继续拼接
    for (const chunk of chunks) {
      const line = chunk
        .split('\n')
        .map((item) => item.trim())
        .find((item) => item.startsWith('data:'))
      if (!line) continue
      const res = line.slice(5).trim()
      if (!res || res === '[DONE]') continue
      try {
        onEvent(JSON.parse(res))
      } catch {}
    }
  }
}
