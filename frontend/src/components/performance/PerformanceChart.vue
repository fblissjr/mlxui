<script setup lang="ts">
// Why: Placeholder for a chart component. Actual implementation needs a charting library.
import { PropType, computed } from 'vue';
import type { PerformanceMetrics } from '@/api/types';

const props = defineProps({
  data: {
    type: Array as PropType<PerformanceMetrics[]>,
    required: true,
  },
  dataKey: {
    type: String as PropType<keyof PerformanceMetrics | string>, // Allow nested like 'memory_usage.rss_mb'
    required: true,
  },
  name: {
    type: String,
    required: true,
  },
  strokeColor: {
    type: String,
    default: '#4F46E5', // Default to primary color
  },
  // TODO (Phase 3+): Add more props for chart customization (axis labels, units, etc.)
});

// Why: Helper to get nested values for dataKey like 'memory_usage.rss_mb'
const getNestedValue = (item: PerformanceMetrics, key: string): number | undefined => {
    const keys = key.split('.');
    let value: any = item;
    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            return undefined;
        }
    }
    return typeof value === 'number' ? value : undefined;
};


const chartData = computed(() => {
  return props.data.map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString(), // Simple time format
    value: getNestedValue(item, props.dataKey as string) ?? 0, // Get value based on dataKey
  }));
});

// This is where you'd integrate a library like vue-chartjs or ECharts for Vue.
// For now, just display raw data or a message.
</script>

<template>
  <div class="w-full h-full p-2 border border-gray-200 dark:border-dark-border rounded-md">
    <p class="text-sm font-medium text-center mb-2">{{ name }}</p>
    <div v-if="chartData.length > 1" class="text-xs overflow-auto h-full">
      <!-- Placeholder: Actual chart rendering logic here -->
      <p class="text-center text-gray-400 dark:text-gray-500 mt-4">
        Chart for '{{ dataKey }}' would be rendered here.
      </p>
      <pre class="mt-2 max-h-40 overflow-y-auto bg-gray-100 dark:bg-dark-bg p-2 rounded text-xs">{{ JSON.stringify(chartData.slice(-10), null, 2) }}</pre>
    </div>
    <div v-else class="flex items-center justify-center h-full text-xs text-gray-400 dark:text-gray-500">
      Not enough data to display chart.
    </div>
  </div>
</template>