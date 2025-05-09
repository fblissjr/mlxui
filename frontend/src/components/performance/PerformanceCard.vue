<script setup lang="ts">
// Why: Define props for reusability. Using 'any' for icon initially,
// can be typed more strictly if using a specific icon library consistently.
import { FunctionalComponent, HTMLAttributes, VNodeProps } from 'vue';

interface Props {
  title: string;
  value: string | number;
  unit?: string;
  icon?: FunctionalComponent<HTMLAttributes & VNodeProps>; // For Lucide or similar SVG components
  iconClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  unit: '',
  iconClass: 'text-primary dark:text-primary-light',
});
</script>

<template>
  <!-- Why: Basic card structure for displaying a single performance metric. -->
  <div class="bg-white dark:bg-dark-surface rounded-lg shadow-md p-4">
    <div class="flex items-center justify-between mb-1">
      <h3 class="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">{{ title }}</h3>
      <component v-if="props.icon" :is="props.icon" :class="['w-5 h-5', props.iconClass]" />
    </div>
    <div class="flex items-baseline">
      <p class="text-2xl font-semibold text-gray-800 dark:text-dark-text-primary">{{ value }}</p>
      <p v-if="unit" class="ml-1.5 text-xs text-gray-500 dark:text-gray-400">{{ unit }}</p>
    </div>
  </div>
</template>