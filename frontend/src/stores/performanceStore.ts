import { defineStore } from 'pinia';
import { ref, onUnmounted } from 'vue';
import type { PerformanceMetrics } from '@/api/types';
import { fetchPerformanceStats, PerformanceStreamManager } from '@/api/performance';
import { useAppStore } from './appStore';

export const usePerformanceStore = defineStore('performance', () => {
  const currentMetrics = ref<PerformanceMetrics | null>(null);
  const historicalMetrics = ref<PerformanceMetrics[]>([]);
  const isStreaming = ref(false);

  const appStore = useAppStore();
  // This should ideally come from a shared config or appStore if it holds app-wide settings
  const maxHistory = 120; // Default history size

  let streamManager: PerformanceStreamManager | null = null;

  async function fetchCurrentStats() {
    // appStore.clearError(); // Clear only if this is a user-initiated action
    try {
      const stats = await fetchPerformanceStats();
      if (stats) {
        currentMetrics.value = stats;
        addHistoricalDataPoint(stats);
      } else {
        // appStore.setLastError("Failed to fetch initial performance stats.");
      }
    } catch (error) {
      // const errorMsg = error instanceof Error ? error.message : 'Unknown error fetching performance stats';
      // appStore.setLastError(errorMsg);
    }
  }

  function addHistoricalDataPoint(metrics: PerformanceMetrics) {
    const newHistory = [...historicalMetrics.value, metrics];
    historicalMetrics.value = newHistory.slice(-maxHistory);
  }

  function startStreamingMetrics() {
    if (isStreaming.value || streamManager) {
      return;
    }
    isStreaming.value = true;
    // appStore.clearError();

    streamManager = new PerformanceStreamManager(
      (metrics: PerformanceMetrics) => {
        currentMetrics.value = metrics;
        addHistoricalDataPoint(metrics);
      },
      (error: Error) => {
        // appStore.setLastError(`Performance Stream Error: ${error.message}`);
        console.error("Performance Stream Error:", error.message); // Log locally too
        isStreaming.value = false; // Allow restart attempt by user or logic
        streamManager = null; // Clear manager on persistent error state from manager
      },
      () => { // onComplete (WebSocket closed)
        isStreaming.value = false;
        streamManager = null;
      }
    );
  }

  function stopStreamingMetrics() {
    if (streamManager) {
      streamManager.closeStream("User requested stop");
      streamManager = null;
    }
    isStreaming.value = false;
  }

  onUnmounted(() => {
    stopStreamingMetrics();
  });

  return {
    currentMetrics,
    historicalMetrics,
    isStreaming,
    fetchCurrentStats,
    startStreamingMetrics,
    stopStreamingMetrics,
  };
});