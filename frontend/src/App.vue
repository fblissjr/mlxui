<script setup lang="ts">
import { onMounted, computed, watch } from 'vue';
import Header from './components/Header.vue';
import ChatMode from './components/chat/ChatMode.vue';
import NotebookMode from './components/notebook/NotebookMode.vue';
import SettingsPanel from './components/settings/SettingsPanel.vue';
import PerformanceDashboard from './components/performance/PerformanceDashboard.vue';
import { useAppStore } from './stores/appStore';
import { useModelStore } from './stores/modelStore';
import { usePerformanceStore } from './stores/performanceStore';
import { LoaderCircle } from 'lucide-vue-next';


const appStore = useAppStore();
const modelStore = useModelStore();
const performanceStore = usePerformanceStore();

const isSettingsPanelOpen = computed(() => appStore.isSettingsPanelOpen);
const isDashboardOpen = computed(() => appStore.isDashboardOpen);
const currentMode = computed(() => appStore.currentMode);
const backendStatus = computed(() => appStore.backendStatus);
const lastError = computed(() => appStore.lastError);
const currentTheme = computed(() => appStore.theme);


onMounted(() => {
  appStore.initializeTheme(); // Initialize theme on app mount
  appStore.checkBackendHealth();
  modelStore.fetchCurrentModelStatus(); // Check if a model was already loaded
  modelStore.fetchLocalModelsList(); // Populate local models list

  if (isDashboardOpen.value) { // Start if initially open
    performanceStore.startStreamingMetrics();
  }
});

watch(isDashboardOpen, (newValue) => {
  if (newValue) {
    performanceStore.fetchCurrentStats(); // Fetch initial stats when opened
    performanceStore.startStreamingMetrics();
  } else {
    performanceStore.stopStreamingMetrics();
  }
});

watch(currentTheme, (newTheme) => {
    // This logic is now handled by appStore.setTheme and initializeTheme
    // document.documentElement.classList.remove('light', 'dark');
    // if (newTheme === 'dark' || (newTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    //     document.documentElement.classList.add('dark');
    // } else {
    //     document.documentElement.classList.add('light');
    // }
}, { immediate: true }); // Apply theme immediately

const retryBackendConnection = () => {
    appStore.checkBackendHealth();
};

</script>

<template>
  <div
    :class="[
      'min-h-screen flex flex-col',
      'bg-gray-100 dark:bg-dark-bg',
      'text-gray-900 dark:text-dark-text-primary'
    ]"
  >
    <Header :backendStatus="backendStatus" />

    <main class="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8 relative">
      <div v-if="lastError" class="fixed top-20 left-1/2 -translate-x-1/2 z-[60] w-full max-w-md p-3 bg-red-100 dark:bg-red-700/30 border border-red-400 dark:border-red-600 rounded-md text-red-700 dark:text-red-200 text-sm shadow-lg">
          <div class="flex items-start">
            <p class="flex-grow"><strong class="font-semibold">Error:</strong> {{ lastError }}</p>
            <button @click="appStore.clearError()" class="ml-2 text-red-500 dark:text-red-300 hover:text-red-700 dark:hover:text-red-100 text-xs font-bold">×</button>
          </div>
      </div>

      <div v-if="backendStatus === 'online'">
        <ChatMode v-if="currentMode === 'chat'" />
        <NotebookMode v-else-if="currentMode === 'notebook'" />
        <div v-else class="text-center p-10">Unknown mode: {{ currentMode }}</div>
      </div>
      <div v-else-if="backendStatus === 'offline'" class="text-center p-10 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg shadow">
        <h2 class="text-2xl font-semibold text-red-700 dark:text-red-300">Backend Server Offline</h2>
        <p class="mt-3 text-gray-600 dark:text-gray-400">
          Please ensure the mlxui backend server is running.
        </p>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-500">
          You can usually start it with: <code class="bg-gray-200 dark:bg-dark-surface px-2 py-1 rounded-md font-mono">python -m mlxui</code>
        </p>
        <button
          @click="retryBackendConnection"
          class="mt-6 btn btn-primary"
        >
          Retry Connection
        </button>
      </div>
      <div v-else class="text-center p-10 text-gray-500 dark:text-gray-400">
        <div class="flex items-center justify-center">
          <LoaderCircle class="animate-spin -ml-1 mr-3 h-6 w-6 text-primary" />
          Connecting to backend...
        </div>
      </div>

      <transition
        enter-active-class="transition ease-out duration-300"
        enter-from-class="transform opacity-0 translate-x-full"
        enter-to-class="transform opacity-100 translate-x-0"
        leave-active-class="transition ease-in duration-200"
        leave-from-class="transform opacity-100 translate-x-0"
        leave-to-class="transform opacity-0 translate-x-full"
      >
        <SettingsPanel v-if="isSettingsPanelOpen" />
      </transition>

      <transition
        enter-active-class="transition ease-out duration-300"
        enter-from-class="transform opacity-0 translate-x-full"
        enter-to-class="transform opacity-100 translate-x-0"
        leave-active-class="transition ease-in duration-200"
        leave-from-class="transform opacity-100 translate-x-0"
        leave-to-class="transform opacity-0 translate-x-full"
      >
        <PerformanceDashboard v-if="isDashboardOpen" />
      </transition>
    </main>

    <footer class="bg-white dark:bg-dark-surface shadow-inner mt-auto">
      <div class="container mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="text-center text-sm text-gray-500 dark:text-dark-text-secondary">
          <p>mlxui: A workbench for mlx-lm models on Apple Silicon</p>
          <p class="mt-1">
            Powered by MLX and mlx-lm
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
main {
  min-height: calc(100vh - 8rem);
}
</style>