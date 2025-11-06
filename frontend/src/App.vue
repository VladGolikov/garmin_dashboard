<template>
  <div class="container">
    <h1>Garmin Mileage Dashboard</h1>

    <section class="stats">
      <div class="stat-card">
        <h2>Current Month</h2>
        <p class="value">{{ monthlyStats.current_month }} km</p>
      </div>
      <div class="stat-card">
        <h2>Previous Month</h2>
        <p class="value">{{ monthlyStats.previous_month }} km</p>
      </div>
      <div class="stat-card">
        <h2>Current Week</h2>
        <p class="value">{{ currentWeek }} km</p>
      </div>
      <div class="stat-card">
        <h2>Last 7 Days</h2>
        <p class="value">{{ last7Days }} km</p>
      </div>
    </section>

    <section class="weeks">
      <h2>Weekly Stats</h2>
      <ul>
        <li v-for="week in weeklyStats" :key="week.week_start">
          {{ week.week_start }}: <strong>{{ week.total_km }} km</strong>
        </li>
      </ul>
    </section>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'App',
  setup() {
    const monthlyStats = ref({ current_month: 0, previous_month: 0 })
    const currentWeek = ref(0)
    const last7Days = ref(0)
    const weeklyStats = ref([])

    const fetchStats = async () => {
      const responses = await Promise.all([
        fetch('/api/monthly'),
        fetch('/api/current_week'),
        fetch('/api/last7days'),
        fetch('/api/weekly')
      ])

      const [monthly, currentW, last7, weekly] = await Promise.all(
        responses.map(r => r.json())
      )

      monthlyStats.value = monthly
      currentWeek.value = currentW.km
      last7Days.value = last7.km
      weeklyStats.value = weekly.weeks
    }

    onMounted(() => {
      fetchStats()
    })

    return {
      monthlyStats,
      currentWeek,
      last7Days,
      weeklyStats
    }
  }
}
</script>

<style>
body {
  margin: 0;
  font-family: sans-serif;
  background-color: #f5f5f5;
}
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
.stat-card {
  display: inline-block;
  margin: 10px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 150px;
  text-align: center;
}
.stat-card h2 {
  margin: 0 0 10px;
  font-size: 1rem;
}
.stat-card .value {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0;
}
.weeks ul {
  list-style: none;
  padding: 0;
}
.weeks li {
  padding: 8px;
  border-bottom: 1px solid #eee;
}
</style>