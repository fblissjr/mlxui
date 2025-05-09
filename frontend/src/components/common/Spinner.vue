<template>
    <svg
      class="animate-spin"
      :class="[sizeClass, colorClass]"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        :stroke-width="strokeWidth"
      ></circle>
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  </template>
  
  <script setup lang="ts">
  import { computed } from 'vue';
  
  interface Props {
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
    color?: string;
    stroke?: number;
  }
  
  const props = withDefaults(defineProps<Props>(), {
    size: 'md',
    color: 'text-primary',
    stroke: 4,
  });
  
  const sizeClass = computed(() => {
    switch (props.size) {
      case 'xs': return 'h-3 w-3';
      case 'sm': return 'h-4 w-4';
      case 'md': return 'h-5 w-5';
      case 'lg': return 'h-8 w-8';
      case 'xl': return 'h-12 w-12';
      default: return 'h-5 w-5';
    }
  });
  
  const colorClass = computed(() => props.color);
  const strokeWidth = computed(() => props.stroke);
  </script>