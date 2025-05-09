import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { checkBackendHealth as checkBackendHealthApi } from '@/api/health';

export interface AppStoreState {
  currentMode: 'chat' | 'notebook';
  isSettingsPanelOpen: boolean;
  isDashboardOpen: boolean;
  backendStatus: 'checking' | 'online' | 'offline';
  lastError: string | null;
  theme: 'light' | 'dark' | 'system';
}

export const useAppStore = defineStore('app', () => {
  const currentMode = ref<'chat' | 'notebook'>('chat');
  const isSettingsPanelOpen = ref(false);
  const isDashboardOpen = ref(false);
  const backendStatus = ref<'checking' | 'online' | 'offline'>('checking');
  const lastError = ref<string | null>(null);
  const theme = ref<'light' | 'dark' | 'system'>('system'); // Default to system

  function setMode(mode: 'chat' | 'notebook') {
    currentMode.value = mode;
  }

  function toggleSettingsPanel() {
    isSettingsPanelOpen.value = !isSettingsPanelOpen.value;
    if (isSettingsPanelOpen.value) isDashboardOpen.value = false;
  }

  function toggleDashboard() {
    isDashboardOpen.value = !isDashboardOpen.value;
    if (isDashboardOpen.value) isSettingsPanelOpen.value = false;
  }

  function setBackendStatus(status: 'checking' | 'online' | 'offline') {
    backendStatus.value = status;
  }

  function setLastError(error: string | null) {
    lastError.value = error;
    if (error) {
        console.error("Global Error Set:", error);
    }
  }

  function clearError() {
    lastError.value = null;
  }

  async function checkBackendHealth() {
    setBackendStatus('checking');
    const isHealthy = await checkBackendHealthApi();
    const newStatus = isHealthy ? 'online' : 'offline';
    setBackendStatus(newStatus);
    if (!isHealthy && backendStatus.value !== 'offline') { // Avoid redundant errors
        setLastError("Backend is offline or not responding to health checks.");
    } else if (isHealthy && lastError.value === "Backend is offline or not responding to health checks.") {
        clearError();
    }
  }

  function setTheme(newTheme: 'light' | 'dark' | 'system') {
    theme.value = newTheme;
    if (newTheme === 'system') {
        localStorage.removeItem('theme');
        applySystemTheme();
    } else {
        localStorage.setItem('theme', newTheme);
        document.documentElement.classList.toggle('dark', newTheme === 'dark');
    }
  }

  function applySystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
  }

  function initializeTheme() {
    const storedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null;
    if (storedTheme && storedTheme !== 'system') {
        setTheme(storedTheme);
    } else {
        setTheme('system'); // Applies system theme and sets up listener
    }
    // Listener for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        if (theme.value === 'system') {
            document.documentElement.classList.toggle('dark', event.matches);
        }
    });
  }


  return {
    currentMode,
    isSettingsPanelOpen,
    isDashboardOpen,
    backendStatus,
    lastError,
    theme,
    setMode,
    toggleSettingsPanel,
    toggleDashboard,
    setBackendStatus,
    setLastError,
    clearError,
    checkBackendHealth,
    setTheme,
    initializeTheme
  };
});