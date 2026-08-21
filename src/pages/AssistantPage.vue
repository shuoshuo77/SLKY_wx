<script setup>
import { ArrowLeft, Bot, LoaderCircle, Mic, Send, Settings } from "lucide-vue-next"

defineProps({
  messages: { type: Array, default: () => [] },
  isSending: { type: Boolean, default: false },
  error: { type: String, default: "" }
})

const chatText = defineModel("chatText", { type: String, default: "" })
const emit = defineEmits(["go", "sendMessage"])

function go(target) {
  emit("go", target)
}

function sendMessage(text) {
  emit("sendMessage", text)
}
</script>

<template>
  <div class="assistant-page">
    <header class="page-header">
      <button @click="go('home')"><ArrowLeft /></button>
      <h1>智能助手</h1>
      <button><Settings /></button>
    </header>

    <section class="chat-list">
      <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
        <span v-if="message.role === 'bot'" class="avatar"><Bot /></span>
        <p>{{ message.text }}</p>
      </div>
      <div v-if="isSending" class="message bot loading">
        <span class="avatar"><Bot /></span>
        <p><LoaderCircle /> 正在思考...</p>
      </div>
      <p v-if="error" class="chat-error">{{ error }}</p>
    </section>

    <div class="quick-prompts">
      <button @click="sendMessage('广东有什么基地推荐？')">广东有什么基地推荐？</button>
      <button @click="sendMessage('推荐一个适合夏季避暑的基地')">避暑推荐</button>
      <button @click="sendMessage('项目里可以预约参访吗？')">基地可以预约吗？</button>
    </div>

    <div class="chat-composer">
      <input
        v-model="chatText"
        :disabled="isSending"
        placeholder="输入你的问题..."
        @keyup.enter="sendMessage()"
      >
      <Mic />
      <button :disabled="isSending || !chatText.trim()" @click="sendMessage()"><Send /></button>
    </div>
  </div>
</template>
