<script setup lang="ts">
// Import computed and ref from Vue
import { computed, ref } from 'vue';
import { useAppStore } from '@/stores/appStore';
import { useModelStore } from '@/stores/modelStore';
// Assuming you've installed and want to use lucide-vue-next icons
import { SunIcon, MoonIcon, SettingsIcon, LayoutDashboardIcon, TerminalSquareIcon, BookTextIcon, LoaderCircleIcon } from 'lucide-vue-next';

interface Props {
  backendStatus: 'checking' | 'online' | 'offline';
}
const props = defineProps<Props>();

const appStore = useAppStore();
const modelStore = useModelStore();

const currentMode = computed(() => appStore.currentMode);
const currentModelName = computed(() => {
    if (modelStore.currentModel?.name) {
        // Truncate long model names for display
        const name = modelStore.currentModel.name;
        return name.length > 25 ? name.substring(0, 22) + '...' : name;
    }
    return 'None Loaded';
});
const fullModelId = computed(() => modelStore.currentModel?.id || ''); // For title attribute
const isModelLoading = computed(() => modelStore.isModelLoading);
const currentTheme = computed(() => appStore.theme);


const toggleTheme = () => {
  const newTheme = currentTheme.value === 'dark' ? 'light' : (currentTheme.value === 'light' ? 'system' : 'dark');
  appStore.setTheme(newTheme);
};

const displayThemeIcon = computed(() => {
    if (currentTheme.value === 'dark') return MoonIcon;
    if (currentTheme.value === 'light') return SunIcon;
    // For 'system', you might want to check window.matchMedia again or have a generic icon
    // For simplicity, defaulting to Sun for system if not dark.
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return MoonIcon;
    }
    return SunIcon;
});
const themeTitle = computed(() => {
    if (currentTheme.value === 'dark') return "Switch to Light Theme";
    if (currentTheme.value === 'light') return "Switch to System Theme";
    return "Switch to Dark Theme";
});


const backendStatusIndicatorClass = computed(() => {
  if (props.backendStatus === 'online') return 'bg-green-500';
  if (props.backendStatus === 'offline') return 'bg-red-500';
  return 'bg-yellow-400 animate-pulse';
});

const backendStatusTitle = computed(() => {
    if (props.backendStatus === 'online') return 'Backend Online';
    if (props.backendStatus === 'offline') return 'Backend Offline';
    return 'Checking Backend...';
});
</script>

<template>
  <header class="bg-white dark:bg-dark-surface shadow-sm sticky top-0 z-50 print:hidden">
    <div class="container mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center">
          <div class="flex-shrink-0 font-bold text-xl text-primary dark:text-primary-light">
            mlx<span class="font-light text-gray-700 dark:text-gray-300">ui</span>
          </div>
          <!-- Mode Switcher -->
          <nav class="hidden md:ml-6 md:flex md:space-x-1" aria-label="Tabs">
            <button
              @click="appStore.setMode('chat')"
              :class="[
                'px-3 py-2 font-medium text-sm rounded-md flex items-center gap-1.5 transition-colors duration-150',
                currentMode === 'chat'
                  ? 'bg-primary-light/20 text-primary dark:bg-primary-dark/30 dark:text-primary-light'
                  : 'text-gray-500 dark:text-dark-text-secondary hover:text-gray-700 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-dark-border',
              ]"
              aria-current="page"
            >
              <TerminalSquareIcon class="w-4 h-4" /> Chat
            </button>
            <button
              @click="appStore.setMode('notebook')"
              :class="[
                'px-3 py-2 font-medium text-sm rounded-md flex items-center gap-1.5 transition-colors duration-150',
                currentMode === 'notebook'
                  ? 'bg-primary-light/20 text-primary dark:bg-primary-dark/30 dark:text-primary-light'
                  : 'text-gray-500 dark:text-dark-text-secondary hover:text-gray-700 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-dark-border',
              ]"
            >
              <BookTextIcon class="w-4 h-4" /> Notebook
            </button>
          </nav>
        </div>

        <div class="flex items-center space-x-2 sm:space-x-3">
           <!-- Status Indicators -->
           <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-text-secondary">
               <div class="flex items-center gap-1 cursor-default" :title="backendStatusTitle">
                   <span
                       class="w-2.5 h-2.5 rounded-full shrink-0"
                       :class="backendStatusIndicatorClass"
                   ></span>
                   <span>Backend</span>
               </div>
               <div class="flex items-center gap-1 cursor-default" :title="isModelLoading ? 'Model Loading...' : (modelStore.currentModel ? `Loaded: ${fullModelId}` : 'No Model Loaded')">
                   <span
                       class="w-2.5 h-2.5 rounded-full shrink-0"
                       :class="[modelStore.currentModel && !isModelLoading ? 'bg-green-500' : 'bg-gray-400', isModelLoading ? 'animate-pulse' : '']"
                   ></span>
                   <span class="hidden sm:inline truncate max-w-[100px] md:max-w-[150px] lg:max-w-[200px]">{{ currentModelName }}</span>
                   <LoaderCircleIcon v-if="isModelLoading" class="w-3.5 h-3.5 animate-spin text-primary dark:text-primary-light"/>
               </div>
           </div>

          <!-- Action Buttons -->
          <button @click="toggleTheme" :title="themeTitle" class="p-2 rounded-full text-gray-500 dark:text-dark-text-secondary hover:bg-gray-100 dark:hover:bg-dark-border focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary dark:focus:ring-offset-dark-bg">
              <component :is="displayThemeIcon" class="w-5 h-5" />
          </button>
          <button @click="appStore.toggleDashboard()" title="Performance Dashboard" class="p-2 rounded-full text-gray-500 dark:text-dark-text-secondary hover:bg-gray-100 dark:hover:bg-dark-border focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary dark:focus:ring-offset-dark-bg">
            <LayoutDashboardIcon class="w-5 h-5" />
          </button>
          <button @click="appStore.toggleSettingsPanel()" title="Settings" class="p-2 rounded-full text-gray-500 dark:text-dark-text-secondary hover:bg-gray-100 dark:hover:bg-dark-border focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary dark:focus:ring-offset-dark-bg">
            <SettingsIcon class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </header>
</template>