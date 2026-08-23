<script setup>
import { ref } from "vue"
import { ArrowLeft, CloudSun, Leaf, MapPinned, Settings, ThermometerSun, Wind } from "lucide-vue-next"

const emit = defineEmits(["go", "notify"])
const periods = ["实时监测", "7天趋势", "30天趋势"]
const activePeriod = ref(periods[0])
function go(target) { emit("go", target) }
function selectPeriod(period) { activePeriod.value = period }
</script>

<template>
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>环境监测</h1><button aria-label="监测说明" @click="emit('notify', '环境数据当前为示例展示，后续可接入实时监测设备。')"><Settings/></button></header>
          <section class="monitor-body"><p class="location"><MapPinned/> 青城山康养基地</p><div class="time-tabs"><button v-for="period in periods" :key="period" :class="{ active: activePeriod === period }" @click="selectPeriod(period)">{{ period }}</button></div><div class="aqi-ring"><small>空气质量</small><strong>优</strong><span>AQI 28</span></div><div class="monitor-list"><p><Leaf/>负氧离子 <b>3200 <small>个/cm³</small></b></p><p><ThermometerSun/>温度 <b>22℃</b></p><p><CloudSun/>湿度 <b>68%</b></p><p><Wind/>PM2.5 <b>12 <small>μg/m³</small></b></p></div><p class="updated">{{ activePeriod }} · 数据更新时间：今天 10:30</p></section>
        </template>
