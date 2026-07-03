<script setup>
import { onMounted } from 'vue'
import TabNav from '@/components/layout/TabNav.vue'
import Sidebar from '@/components/layout/Sidebar.vue'

// Warm the route chunks in the background so tab-to-tab navigation is instant
// (Vite dedupes these against the router's dynamic imports, so each loads once).
onMounted(() => {
  const prefetch = [
    () => import('@/components/dashboard/DashboardOverview.vue'),
    () => import('@/components/dashboard/HistoryTab.vue'),
    () => import('@/components/dashboard/SessionTab.vue'),
    () => import('@/components/dashboard/MembersTab.vue'),
    () => import('@/components/dashboard/OwnersTab.vue'),
    () => import('@/views/ProfileView.vue'),
    () => import('@/views/MemberDetailView.vue'),
  ]
  const run = () => prefetch.forEach((load) => load())
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(run)
  } else {
    setTimeout(run, 200)
  }
})
</script>

<template>
  <div class="min-h-screen md:flex">
    <Sidebar class="hidden md:flex" />

    <div class="min-w-0 flex-1">
      <main class="p-4 pb-24 sm:p-6 md:p-10 md:pb-10">
        <div class="mx-auto w-full max-w-5xl">
          <router-view />
        </div>
      </main>
    </div>

    <TabNav />
  </div>
</template>
