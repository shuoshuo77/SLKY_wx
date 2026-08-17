<script setup>
import { ArrowLeft, CloudSun, Leaf, MapPinned, Settings, ThermometerSun, Wind } from "lucide-vue-next"

const emit = defineEmits(["go"])
function go(target) { emit("go", target) }
</script>

<template>
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>环境监测</h1><button><Settings/></button></header>
          <section class="monitor-body"><p class="location"><MapPinned/> 青城山康养基地</p><div class="time-tabs"><b>实时监测</b><span>7天趋势</span><span>30天趋势</span></div><div class="aqi-ring"><small>空气质量</small><strong>优</strong><span>AQI 28</span></div><div class="monitor-list"><p><Leaf/>负氧离子 <b>3200 <small>个/cm³</small></b></p><p><ThermometerSun/>温度 <b>22℃</b></p><p><CloudSun/>湿度 <b>68%</b></p><p><Wind/>PM2.5 <b>12 <small>μg/m³</small></b></p></div><p class="updated">数据更新时间：今天 10:30</p></section>
        </template>
