<script setup lang="ts">
// Placeholder for Notebook Mode
import { ref } from 'vue';
// import NotebookBlock from './NotebookBlock.vue'; // Uncomment when NotebookBlock is implemented

const blocks = ref([{ id: '1', content: '### Welcome to Notebook Mode!\n\nThis feature is under construction.' }]);
</script>

<template>
  <div class="space-y-4">
    <h2 class="text-2xl font-semibold text-gray-800 dark:text-dark-text-primary">Notebook Mode</h2>
    <div class="p-6 bg-yellow-50 dark:bg-yellow-700/20 border border-yellow-300 dark:border-yellow-600 rounded-lg">
        <p class="text-yellow-700 dark:text-yellow-200">
            Notebook mode is currently under development.
            The plan is to allow for mixed markdown and code/generation blocks, similar to Jupyter or ExUI.
        </p>
    </div>
    <!-- TODO (Phase 3+): Implement actual notebook block rendering and interaction -->
    <!-- <NotebookBlock v-for="block in blocks" :key="block.id" :initial-content="block.content" /> -->
    <!-- <button class="btn btn-secondary mt-4">Add Block</button> -->
  </div>
</template>