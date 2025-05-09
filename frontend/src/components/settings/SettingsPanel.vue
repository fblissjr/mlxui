<script setup lang="ts">
import { ref } from 'vue';
import { useAppStore } from '@/stores/appStore';
import ModelSettings from './ModelSettings.vue';
import ParameterSettings from './ParameterSettings.vue';
import AdvancedParametersPanel from './AdvancedParametersPanel.vue';
import CacheManagementPanel from './CacheManagementPanel.vue';
import { XIcon } from 'lucide-vue-next'; // Using lucide for icons

type Tab = 'model' | 'parameters' | 'advanced' | 'cache';

const appStore = useAppStore();
const activeTab = ref<Tab>('model'); // Default to model settings

const tabs: Array<{ id: Tab; label: string }> = [
  { id: 'model', label: 'Model' },
  { id: 'parameters', label: 'Parameters' },
  { id: 'advanced', label: 'Advanced' },
  { id: 'cache', label: 'KV Cache' },
];

// Why: Centralized function to close the panel, called by button or App.vue overlay click.
const closePanel = () => {
  appStore.toggleSettingsPanel();
};
</script>

<template>
  <!-- Why: Fixed positioning for an overlay panel. High z-index to appear on top. -->
  <div class="fixed inset-0 bg-black/30 dark:bg-black/50 flex justify-end z-40 backdrop-blur-sm" @click.self="closePanel">
    <!-- Why: stopPropagation on the panel itself to prevent clicks inside from closing it. -->
    <div
      class="w-full max-w-md md:max-w-lg h-full bg-white dark:bg-dark-surface shadow-2xl flex flex-col transform transition-transform duration-300 ease-in-out"
      :class="{ 'translate-x-0': appStore.isSettingsPanelOpen, 'translate-x-full': !appStore.isSettingsPanelOpen }"
      @click.stop
    >
      <!-- Panel Header -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-border sticky top-0 bg-white dark:bg-dark-surface z-10">
        <h2 class="text-xl font-semibold text-gray-800 dark:text-dark-text-primary">Settings</h2>
        <button
          @click="closePanel"
          class="p-1.5 rounded-full text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-border focus:outline-none focus:ring-2 focus:ring-primary"
          title="Close Settings"
        >
          <XIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Tabs Navigation -->
      <div class="border-b border-gray-200 dark:border-dark-border">
        <nav class="-mb-px flex space-x-1 px-3" aria-label="Tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'whitespace-nowrap py-3 px-3 border-b-2 font-medium text-sm transition-colors duration-150',
              activeTab === tab.id
                ? 'border-primary text-primary dark:border-primary-light'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-dark-text-secondary dark:hover:text-dark-text-primary dark:hover:border-dark-border',
            ]"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Panel Content -->
      <!-- Why: overflow-y-auto allows content to scroll if it exceeds panel height. -->
      <div class="flex-grow p-4 overflow-y-auto space-y-6">
        <ModelSettings v-if="activeTab === 'model'" />
        <ParameterSettings v-if="activeTab === 'parameters'" />
        <AdvancedParametersPanel v-if="activeTab === 'advanced'" />
        <CacheManagementPanel v-if="activeTab === 'cache'" />
        <!-- TODO (Phase 3+): Add more settings sections/tabs as needed -->
      </div>
    </div>
  </div>
</template>