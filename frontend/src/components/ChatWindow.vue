<template>
  <div class="flex-1 flex flex-col min-h-0">
    <!-- ── 消息区域 ── -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-8 py-6 space-y-5">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="message-enter flex items-center justify-center h-full">
        <div class="text-center space-y-4">
          <div class="w-20 h-20 mx-auto rounded-2xl flex items-center justify-center text-3xl"
            style="background: linear-gradient(135deg, #E8ECF8 0%, #DDE3F0 100%); box-shadow: 0 8px 24px rgba(107,125,179,0.10);">
            🍃
          </div>
          <h3 class="text-lg font-semibold font-kai" style="color: #2D3748;">您好，我是您的AI老中医问诊助手</h3>
          <p class="text-sm leading-relaxed max-w-sm mx-auto" style="color: #8899AA;">
            请您慢慢描述今日的不适，我来为您细细记录。
          </p>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, idx) in messages" :key="idx" class="message-enter" :style="{ animationDelay: '0.05s' }">
        <!-- AI 消息 -->
        <div v-if="msg.role === 'assistant'" class="flex gap-3 items-start max-w-[85%]">
          <div class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center text-base"
            style="background: linear-gradient(135deg, #E8ECF8 0%, #DDE3F0 100%); box-shadow: 0 2px 8px rgba(107,125,179,0.08);">
            🏺
          </div>
          <div class="flex-1 min-w-0 space-y-3">
            <div class="inline-block max-w-full px-5 py-3.5 rounded-2xl text-sm leading-relaxed"
              style="background: #F7F9FE; border: 1px solid #E8ECF5; box-shadow: 0 2px 8px rgba(107,125,179,0.04); color: #2D3748; border-bottom-left-radius: 6px;">
              {{ msg.content }}
            </div>
            <!-- 四诊档案表格 -->
            <div v-if="msg.table" class="space-y-3">
              <div class="flex items-center gap-2">
                <div class="flex-1 h-px" style="background: linear-gradient(90deg, transparent, #DDE3F0, transparent);"></div>
                <span class="text-sm font-semibold font-kai px-3 py-1 rounded-full" style="background: #E8ECF8; color: #6B7DB3;">📜 四诊档案</span>
                <div class="flex-1 h-px" style="background: linear-gradient(90deg, transparent, #DDE3F0, transparent);"></div>
              </div>
              <div v-html="renderMarkdown(msg.table)" class="markdown-content overflow-x-auto rounded-2xl"
                style="background: #FFFFFF; border: 1px solid #EEF1F8; box-shadow: 0 4px 16px rgba(107,125,179,0.06); padding: 0.25rem;"></div>
            </div>
          </div>
        </div>

        <!-- 用户消息 -->
        <div v-else class="flex justify-end">
          <div class="flex gap-3 items-start max-w-[75%]">
            <div class="inline-block px-5 py-3.5 rounded-2xl text-sm leading-relaxed"
              style="background: linear-gradient(135deg, #6B7DB3 0%, #5A6DA0 100%); color: #FFFFFF; box-shadow: 0 4px 12px rgba(107,125,179,0.20); border-bottom-right-radius: 6px;">
              {{ msg.content }}
            </div>
            <div class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center text-base"
              style="background: linear-gradient(135deg, #E8ECF8 0%, #DDE3F0 100%); box-shadow: 0 2px 8px rgba(107,125,179,0.08);">
              🌿
            </div>
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="message-enter flex gap-3 items-start max-w-[85%]">
        <div class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center text-base"
          style="background: linear-gradient(135deg, #E8ECF8 0%, #DDE3F0 100%); box-shadow: 0 2px 8px rgba(107,125,179,0.08);">
          🏺
        </div>
        <div class="inline-block px-6 py-4 rounded-2xl"
          style="background: #F7F9FE; border: 1px solid #E8ECF5; box-shadow: 0 2px 8px rgba(107,125,179,0.04); border-bottom-left-radius: 6px;">
          <span class="inline-flex items-center gap-2 text-sm" style="color: #8899AA;">
            <span class="flex gap-1">
              <span class="w-1.5 h-1.5 rounded-full animate-pulse" style="background: #6B7DB3; animation-delay: 0s;"></span>
              <span class="w-1.5 h-1.5 rounded-full animate-pulse" style="background: #6B7DB3; animation-delay: 0.2s;"></span>
              <span class="w-1.5 h-1.5 rounded-full animate-pulse" style="background: #6B7DB3; animation-delay: 0.4s;"></span>
            </span>
            AI老中医正在为您辨证…
          </span>
        </div>
      </div>

      <!-- 完成提示 -->
      <div v-if="isComplete" class="message-enter text-center pt-2">
        <p class="text-xs" style="color: #8899AA;">✨ 问诊已完成。如有新的不适，请刷新页面重新开始。</p>
      </div>
    </div>

    <!-- ── 输入区 ── -->
    <div class="flex-shrink-0 px-8 py-4" style="background: rgba(255,255,255,0.7); backdrop-filter: blur(12px); border-top: 1px solid #EEF1F8;">
      <div class="flex items-center gap-3 max-w-4xl mx-auto">
        <div class="flex-1 relative">
          <span class="absolute left-4 top-1/2 -translate-y-1/2 text-lg" style="opacity: 0.5;">✍️</span>
          <input ref="inputRef" v-model="userInput" :disabled="loading || isComplete" type="text"
            :placeholder="isComplete ? '问诊已完成' : '您哪里不舒服？慢慢讲……'"
            class="w-full pl-12 pr-5 py-3.5 text-sm rounded-2xl outline-none transition-all duration-200"
            style="background: #FFFFFF; border: 2px solid #EEF1F8; color: #2D3748; box-shadow: 0 2px 12px rgba(107,125,179,0.04);"
            @keydown.enter="sendMessage" />
        </div>
        <button :disabled="!userInput.trim() || loading || isComplete"
          class="flex-shrink-0 px-6 py-3.5 text-sm font-semibold rounded-2xl transition-all duration-200"
          :class="canSend ? 'cursor-pointer hover:opacity-90 active:scale-95' : 'cursor-not-allowed opacity-50'"
          style="background: linear-gradient(135deg, #6B7DB3 0%, #4A5D8F 100%); color: #FFFFFF; box-shadow: 0 4px 16px rgba(107,125,179,0.25);"
          @click="sendMessage">开始问诊</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps({ sessionId: { type: String, required: true } })
const emit = defineEmits(['complete'])

const messages = ref([])
const userInput = ref('')
const loading = ref(false)
const isComplete = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)

const canSend = computed(() => userInput.value.trim() && !loading.value && !isComplete.value)

const md = new MarkdownIt({ html: false, linkify: false, typographer: true })
function renderMarkdown(text) { return text ? md.render(text) : '' }

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
}

async function sendMessage() {
  const text = userInput.value.trim()
  if (!text || loading.value || isComplete.value) return

  messages.value.push({ role: 'user', content: text, table: null })
  userInput.value = ''
  await scrollToBottom()

  loading.value = true
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: props.sessionId, message: text }),
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()

    messages.value.push({ role: 'assistant', content: data.reply || '……', table: data.table || null })

    if (data.is_complete) {
      isComplete.value = true
      const info = data.collected_info || {}
      emit('complete', {
        patient_name: info.patient_name || '匿名患者',
        collected_info: info,
        markdown_table: data.table || '',
      })
    }
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，AI老中医此刻有些疲惫，网络似乎不太通畅。请您稍后再试。',
      table: null,
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}
</script>

<style scoped>
input::placeholder {
  color: #B8C5E0;
  font-family: 'KaiTi', 'STKaiti', '楷体', 'Noto Serif SC', serif;
}
input:focus {
  border-color: #6B7DB3 !important;
  box-shadow: 0 0 0 4px rgba(107, 125, 179, 0.08) !important;
}
</style>
