<script setup lang="ts">
// Why: Vue 3 Composition API for logic.
import { computed, onMounted, onUnmounted, watch } from 'vue';
import { useAppStore } from '@/stores/appStore';
import { usePerformanceStore } from '@/stores/performanceStore';
import { useModelStore } from '@/stores/modelStore'; // To display current model config
import PerformanceCard from './PerformanceCard.vue';
import PerformanceChart from './PerformanceChart.vue';
import { XIcon, ZapIcon, CpuIcon, DatabaseIcon, HelpCircleIcon } from 'lucide-vue-next'; // Using lucide for icons

const appStore = useAppStore();
const performanceStore = usePerformanceStore();
const modelStore = useModelStore();

const isDashboardOpen = computed(() => appStore.isDashboardOpen); // For transition
const currentMetrics = computed(() => performanceStore.currentMetrics);
const historicalMetrics = computed(() => performanceStore.historicalMetrics);
const currentModelForDisplay = computed(() => modelStore.currentModel);
// Assuming generationParams are in a generationStore or appStore
const generationParamsForDisplay = computed(() => {
    // If you create a generationStore, get it from there
    // For now, assuming it's somehow accessible or part of appStore if simplified
    // Replace this with actual store access:
    const genStore = /* useGenerationStore() */ { generationParams: { temperature: 0, top_p: 0, top_k: 0, max_tokens: 0 }};
    return genStore.generationParams;
});


// Why: Start/stop streaming when dashboard opens/closes or component mounts/unmounts.
onMounted(() => {
  if (appStore.isDashboardOpen) {
    performanceStore.fetchCurrentStats(); // Fetch initial stats
    performanceStore.startStreamingMetrics();
  }
});

watch(isDashboardOpen, (newValue) => {
  if (newValue) {
    performanceStore.fetchCurrentStats();
    performanceStore.startStreamingMetrics();
  } else {
    performanceStore.stopStreamingMetrics();
  }
});

onUnmounted(() => {
  performanceStore.stopStreamingMetrics();
});

const formatMemory = (bytes?: number): string => {
    if (bytes === undefined || bytes === null || isNaN(bytes)) return 'N/A';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

const closeDashboard = () => {
  appStore.toggleDashboard();
};
</script>

<template>
  <div
    class="fixed inset-0 bg-black/30 dark:bg-black/50 flex justify-end z-40 backdrop-blur-sm"
    @click.self="closeDashboard"
  >
    <div
      class="w-full max-w-xl md:max-w-2xl h-full bg-white dark:bg-dark-surface shadow-2xl overflow-y-auto flex flex-col transform transition-transform duration-300 ease-in-out"
      :class="{ 'translate-x-0': isDashboardOpen, 'translate-x-full': !isDashboardOpen }"
      @click.stop
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-border sticky top-0 bg-white dark:bg-dark-surface z-10">
        <h2 class="text-xl font-semibold text-gray-800 dark:text-dark-text-primary">Performance Dashboard</h2>
        <button
          @click="closeDashboard"
          class="p-1.5 rounded-full text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-border focus:outline-none focus:ring-2 focus:ring-primary"
          title="Close Dashboard"
        >
          <XIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Content Area -->
      <div class="p-4 space-y-6 flex-grow">
        <div v-if="!currentMetrics" class="text-center py-10 text-gray-500 dark:text-dark-text-secondary">
          <LoaderCircle class="w-8 h-8 mx-auto animate-spin text-primary mb-2" />
          Loading performance data...
        </div>
        <template v-else>
          <!-- Current Metrics Cards -->
          <div class="grid grid-cols-2 gap-4">
            <PerformanceCard
              title="Generation Speed"
              :value="currentMetrics.tokens_per_second?.toFixed(1) ?? 'N/A'"
              unit="tok/s"
              :icon="ZapIcon"
              iconClass="text-yellow-500"
            />
            <PerformanceCard
              title="Memory Usage (RSS)"
              :value="formatMemory(currentMetrics.memory_usage?.rss_mb ? currentMetrics.memory_usage.rss_mb * 1024 * 1024 : undefined)"
              unit=""
              :icon="DatabaseIcon"
              iconClass="text-blue-500"
            />
            <PerformanceCard
              title="CPU Usage"
              :value="currentMetrics.cpu_usage_percent?.toFixed(1) ?? 'N/A'"
              unit="%"
              :icon="CpuIcon"
              iconClass="text-green-500"
            />
             <PerformanceCard
                title="GPU Usage (Est.)"
                value="N/A"
                unit="%"
                :icon="HelpCircleIcon"
                iconClass="text-purple-500"
                title-hint="GPU usage metrics are not directly available from MLX yet."
             />
             <!-- TODO (Phase 3+): Add total generated tokens if tracked by adapter -->
          </div>

          <!-- Charts -->
          <div class="space-y-6">
            <div>
              <h3 class="text-md font-medium mb-1.5 text-gray-700 dark:text-dark-text-secondary">Generation Speed (tok/s)</h3>
              <div class="bg-gray-50 dark:bg-dark-bg rounded-lg shadow-inner p-2 h-48 md:h-56">
                <PerformanceChart
                  :data="historicalMetrics"
                  dataKey="tokens_per_second"
                  name="Tokens/sec"
                  strokeColor="#0ea5e9"
                />
              </div>
            </div>
            <div>
              <h3 class="text-md font-medium mb-1.5 text-gray-700 dark:text-dark-text-secondary">Memory Usage (RSS MB)</h3>
              <div class="bg-gray-50 dark:bg-dark-bg rounded-lg shadow-inner p-2 h-48 md:h-56">
                <PerformanceChart
                  :data="historicalMetrics"
                  dataKey="memory_usage.rss_mb"
                  name="Memory (MB)"
                  strokeColor="#8b5cf6"
                />
              </div>
            </div>
             <!-- TODO (Phase 3+): Add CPU Usage Chart -->
          </div>

           <!-- Current Config Snippet -->
           <div class="bg-gray-50 dark:bg-dark-bg rounded-lg shadow-inner p-4">
               <h3 class="text-md font-medium mb-2 text-gray-700 dark:text-dark-text-secondary">Current Setup</h3>
               <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-600 dark:text-dark-text-secondary">
                    <div>
                         <span class="font-semibold">Model:</span>
                         <span class="ml-1 font-mono truncate" :title="currentModelForDisplay?.id">
                             {{ currentModelForDisplay?.name || 'None' }}
                         </span>
                    </div>
                     <div>
                         <span class="font-semibold">Adapter:</span>
                         <span class="ml-1 font-mono truncate" :title="currentModelForDisplay?.adapter_path">
                             {{ currentModelForDisplay?.adapter_path || 'None' }}
                         </span>
                    </div>
                    <div>
                         <span class="font-semibold">Temp:</span>
                         <span class="ml-1 font-mono">
                              {{ generationParamsForDisplay.temperature?.toFixed(2) }}
                         </span>
                    </div>
                    <div>
                         <span class="font-semibold">Top P:</span>
                         <span class="ml-1 font-mono">
                              {{ generationParamsForDisplay.top_p?.toFixed(2) }}
                         </span>
                    </div>
                     <div>
                         <span class="font-semibold">Max Tokens:</span>
                         <span class="ml-1 font-mono">
                              {{ generationParamsForDisplay.max_tokens }}
                         </span>
                    </div>
                     <div>
                         <span class="font-semibold">Top K:</span>
                         <span class="ml-1 font-mono">
                              {{ generationParamsForDisplay.top_k }}
                         </span>
                    </div>
               </div>
           </div>
        </template>
      </div>
    </div>
  </div>
</template>