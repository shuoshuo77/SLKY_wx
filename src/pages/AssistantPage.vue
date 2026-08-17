<script setup>
import { ArrowLeft, Bot, Flame, Mic, Send, Settings } from "lucide-vue-next"

defineProps({
  messages: { type: Array, default: () => [] },
  hotBases: { type: Array, default: () => [] }
})

const chatText = defineModel("chatText", { type: String, default: "" })
const emit = defineEmits(["go", "openDetail", "sendMessage"])

function go(target) { emit("go", target) }
function openDetail(base) { emit("openDetail", base) }
function sendMessage(text) { emit("sendMessage", text) }
</script>

<template>
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>智能助手</h1><button><Settings/></button></header>
          <section class="chat-list"><div v-for="(message, index) in messages" :key="index" class="message" :class="message.role"><span v-if="message.role === 'bot'" class="avatar"><Bot/></span><p>{{ message.text }}</p></div><article v-if="hotBases[0]" class="recommend-card" @click="openDetail(hotBases[0])"><img :src="hotBases[0].image"><div><b>{{ hotBases[0].name }}</b><span>{{ hotBases[0].area }}</span><em><Flame :size="13"/> 热度 {{ hotBases[0].viewCount }}</em></div></article></section>
          <div class="quick-prompts"><button @click="sendMessage('环境怎么样？')">环境怎么样？</button><button @click="sendMessage('附近有什么基地？')">附近有什么基地？</button></div>
          <div class="chat-composer"><input v-model="chatText" placeholder="输入你的问题..." @keyup.enter="sendMessage()"><Mic/><button @click="sendMessage()"><Send/></button></div>
        </template>
