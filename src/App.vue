<script setup>
import { computed, ref } from "vue"
import {
  ArrowLeft, Bell, Bot, CalendarDays, ChevronRight, CircleUserRound,
  CloudSun, Heart, Home, Leaf, LocateFixed, MapPinned, MessageCircle,
  Mic, Search, Send, Settings, SlidersHorizontal, Sparkles, Star,
  ThermometerSun, Trees, UserRound, Wind
} from "lucide-vue-next"

const images = {
  hero: "/assets/images/07-首页轮播-森林.jpg",
  lake: "/assets/images/03-森林湖泊山景.jpg",
  lakeside: "/assets/images/04-湖畔山林.jpg",
  dense: "/assets/images/05-密林自然景观.jpg",
  retreat: "/assets/images/02-山地康养度假.jpg"
}

const bases = [
  { id: 1, name: "青城山康养基地", area: "四川 · 成都 · 都江堰", distance: "12.5km", rating: "4.8", image: images.lake, tags: ["森林康养", "避暑", "空气优", "徒步"], temp: 22, aqi: 28, oxygen: 3200, humidity: 68, desc: "基地位于世界自然遗产地青城山周边，森林覆盖率高，空气清新，适合旅居、徒步、研学与亲子康养活动。" },
  { id: 2, name: "庐山康养基地", area: "江西 · 九江 · 庐山", distance: "68.3km", rating: "4.7", image: images.lakeside, tags: ["温泉", "湿地", "徒步"], temp: 21, aqi: 32, oxygen: 2860, humidity: 72, desc: "山地避暑与温泉疗养结合，适合周末度假、亲子自然课堂和慢行康养路线。" },
  { id: 3, name: "神农架自然基地", area: "湖北 · 神农架", distance: "256km", rating: "4.6", image: images.dense, tags: ["自然", "科考", "研学"], temp: 18, aqi: 18, oxygen: 3600, humidity: 76, desc: "自然教育资源丰富，适合生态研学、森林观察与深度自然体验。" },
  { id: 4, name: "长白山康养基地", area: "吉林 · 长白山", distance: "890km", rating: "4.5", image: images.retreat, tags: ["森林", "滑雪", "温泉"], temp: 16, aqi: 24, oxygen: 3010, humidity: 64, desc: "依托山地森林、雪季运动与温泉资源，提供四季康养和休闲度假服务。" }
]

const page = ref("home")
const selected = ref(bases[0])
const searchText = ref("")
const chatText = ref("")
const booked = ref(false)
const messages = ref([
  { role: "bot", text: "你好！我是森氧康养智能助手，很高兴为你服务。" },
  { role: "user", text: "推荐适合夏季避暑的基地" },
  { role: "bot", text: "为你推荐青城山康养基地和庐山康养基地，它们气温舒适、空气质量优秀。" }
])

const filteredBases = computed(() => {
  const keyword = searchText.value.trim()
  if (!keyword) return bases
  return bases.filter((item) => `${item.name}${item.area}${item.tags.join("")}`.includes(keyword))
})

function go(target) {
  page.value = target
  window.scrollTo({ top: 0, behavior: "smooth" })
}

function openDetail(base) {
  selected.value = base
  booked.value = false
  go("detail")
}

function sendMessage(text = chatText.value) {
  const value = text.trim()
  if (!value) return
  messages.value.push({ role: "user", text: value })
  chatText.value = ""
  setTimeout(() => messages.value.push({ role: "bot", text: "根据你的需求，青城山康养基地匹配度最高。空气质量优，夏季平均气温舒适，距离也更近。" }), 350)
}
</script>

<template>
  <div class="stage">
    <div class="phone-shell">
      <main class="app-view">
        <template v-if="page === 'home'">
          <header class="brand-bar">
            <div class="brand"><Trees :size="25"/><strong>森氧康养</strong></div>
            <div class="header-actions"><Bell :size="19"/><Settings :size="19"/></div>
          </header>

          <section class="hero" :style="{ backgroundImage: `url(${images.hero})` }">
            <div class="hero-copy"><h1>呼吸自然<br>享受健康生活</h1><p>探索优质康养基地</p></div>
            <div class="search-box">
              <Search :size="18"/><input v-model="searchText" placeholder="搜索基地名称、位置、特色..." @keyup.enter="go('bases')"><button @click="go('bases')">搜索</button>
            </div>
          </section>

          <section class="service-grid">
            <button @click="go('bases')"><span><Search/></span><b>基地查询</b></button>
            <button @click="go('assistant')"><span><Bot/></span><b>智能推荐</b></button>
            <button @click="go('monitor')"><span><Leaf/></span><b>环境监测</b></button>
            <button @click="openDetail(bases[0])"><span><Sparkles/></span><b>健康指南</b></button>
          </section>

          <section class="section-block">
            <div class="section-heading"><h2>热门基地</h2><button @click="go('bases')">更多 <ChevronRight :size="15"/></button></div>
            <article v-for="base in bases.slice(0, 3)" :key="base.id" class="base-row" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div><h3>{{ base.name }}</h3><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div><p>{{ base.distance }} <Star :size="14"/> {{ base.rating }}</p></div>
              <Heart class="heart" :size="20"/>
            </article>
          </section>
        </template>

        <template v-else-if="page === 'bases'">
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>基地列表</h1><button><SlidersHorizontal/></button></header>
          <div class="list-search"><Search :size="18"/><input v-model="searchText" placeholder="搜索基地名称或地区"></div>
          <div class="chip-row"><button class="active">全部</button><button>康养</button><button>徒步</button><button>研学</button><button>生态</button></div>
          <section class="base-list">
            <article v-for="base in filteredBases" :key="base.id" class="base-card" @click="openDetail(base)">
              <img :src="base.image" :alt="base.name">
              <div class="base-card-content"><h3>{{ base.name }}</h3><p class="muted">{{ base.area }}</p><p class="rating"><Star :size="14"/> {{ base.rating }}　{{ base.distance }}</p><div class="tags"><span v-for="tag in base.tags.slice(0, 3)" :key="tag">{{ tag }}</span></div></div>
              <Heart class="heart" :size="19"/>
            </article>
          </section>
        </template>

        <template v-else-if="page === 'detail'">
          <header class="page-header overlay"><button @click="go('bases')"><ArrowLeft/></button><h1>基地详情</h1><button><Heart/></button></header>
          <img class="detail-cover" :src="selected.image" :alt="selected.name">
          <section class="detail-body">
            <h1>{{ selected.name }}</h1><p class="muted">{{ selected.area }}</p>
            <div class="tags"><span v-for="tag in selected.tags" :key="tag">{{ tag }}</span></div>
            <p class="detail-rating"><Star :size="17"/> <b>{{ selected.rating }}</b>（128条评价）<em>{{ selected.distance }}</em></p>
            <div class="metric-grid">
              <div><Wind/><small>空气质量</small><b>优</b><span>AQI {{ selected.aqi }}</span></div>
              <div><Leaf/><small>负氧离子</small><b>{{ selected.oxygen }}</b><span>个/cm³</span></div>
              <div><ThermometerSun/><small>温度</small><b>{{ selected.temp }}℃</b><span>舒适</span></div>
              <div><CloudSun/><small>湿度</small><b>{{ selected.humidity }}%</b><span>适宜</span></div>
            </div>
            <h2>基地介绍</h2><p class="description">{{ selected.desc }}</p>
            <h2>康养服务</h2><div class="services"><span>森林步道</span><span>环境体验</span><span>康养餐食</span><span>导览服务</span></div>
          </section>
          <div class="action-bar"><button class="ghost" @click="go('map')"><LocateFixed/>导航</button><button class="primary" @click="booked = true">{{ booked ? '预约成功' : '预约参访' }}</button></div>
        </template>

        <template v-else-if="page === 'map'">
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>地图找基地</h1><button><SlidersHorizontal/></button></header>
          <section class="map-panel">
            <div class="map-grid"></div>
            <button v-for="(base, index) in bases" :key="base.id" class="pin" :style="{ left: `${18 + index * 19}%`, top: `${26 + (index % 2) * 22}%` }" @click="selected = base"><MapPinned/></button>
          </section>
          <article class="map-result" @click="openDetail(selected)"><img :src="selected.image"><div><h3>{{ selected.name }}</h3><div class="tags"><span v-for="tag in selected.tags.slice(0,2)" :key="tag">{{ tag }}</span></div><p><Star :size="14"/> {{ selected.rating }}　{{ selected.distance }}</p></div><ChevronRight/></article>
        </template>

        <template v-else-if="page === 'monitor'">
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>环境监测</h1><button><Settings/></button></header>
          <section class="monitor-body"><p class="location"><MapPinned/> 青城山康养基地</p><div class="time-tabs"><b>实时监测</b><span>7天趋势</span><span>30天趋势</span></div><div class="aqi-ring"><small>空气质量</small><strong>优</strong><span>AQI 28</span></div><div class="monitor-list"><p><Leaf/>负氧离子 <b>3200 <small>个/cm³</small></b></p><p><ThermometerSun/>温度 <b>22℃</b></p><p><CloudSun/>湿度 <b>68%</b></p><p><Wind/>PM2.5 <b>12 <small>μg/m³</small></b></p></div><p class="updated">数据更新时间：今天 10:30</p></section>
        </template>

        <template v-else-if="page === 'assistant'">
          <header class="page-header"><button @click="go('home')"><ArrowLeft/></button><h1>智能助手</h1><button><Settings/></button></header>
          <section class="chat-list"><div v-for="(message, index) in messages" :key="index" class="message" :class="message.role"><span v-if="message.role === 'bot'" class="avatar"><Bot/></span><p>{{ message.text }}</p></div><article class="recommend-card" @click="openDetail(bases[0])"><img :src="bases[0].image"><div><b>青城山康养基地</b><span>22℃ · AQI 28</span><em><Star :size="13"/> 4.8　12.5km</em></div></article></section>
          <div class="quick-prompts"><button @click="sendMessage('环境怎么样？')">环境怎么样？</button><button @click="sendMessage('附近有什么基地？')">附近有什么基地？</button></div>
          <div class="chat-composer"><input v-model="chatText" placeholder="输入你的问题..." @keyup.enter="sendMessage()"><Mic/><button @click="sendMessage()"><Send/></button></div>
        </template>

        <template v-else-if="page === 'profile'">
          <header class="profile-head"><div class="profile-avatar"><UserRound/></div><div><h1>森林爱好者</h1><p>ID: 12345678</p></div><Bell/><Settings/></header>
          <section class="profile-stats"><div><b>12</b><span>我的收藏</span></div><div><b>5</b><span>我的预约</span></div><div><b>18</b><span>浏览记录</span></div></section>
          <section class="profile-menu"><h2>我的服务</h2><div class="menu-grid"><button><Heart/><span>我的收藏</span></button><button><CalendarDays/><span>我的预约</span></button><button><MapPinned/><span>我的足迹</span></button><button><MessageCircle/><span>我的评价</span></button></div></section>
          <section class="settings-list"><button><Bell/>消息通知<ChevronRight/></button><button><MessageCircle/>意见反馈<ChevronRight/></button><button><CircleUserRound/>关于我们<ChevronRight/></button><button><Settings/>设置<ChevronRight/></button></section>
        </template>
      </main>

      <nav v-if="!['detail','monitor'].includes(page)" class="bottom-nav">
        <button :class="{ active: page === 'home' || page === 'bases' }" @click="go('home')"><Home/><span>首页</span></button>
        <button :class="{ active: page === 'map' }" @click="go('map')"><MapPinned/><span>地图</span></button>
        <button :class="{ active: page === 'assistant' }" @click="go('assistant')"><Bot/><span>智能助手</span></button>
        <button :class="{ active: page === 'profile' }" @click="go('profile')"><UserRound/><span>我的</span></button>
      </nav>
    </div>
  </div>
</template>
