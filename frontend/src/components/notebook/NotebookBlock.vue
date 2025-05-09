<script setup lang="ts">
// Placeholder for Notebook Block
defineProps<{ initialContent: string }>();
</script>
<template>
  <div class="p-4 border rounded-md bg-white dark:bg-dark-surface">
    <pre>{{ initialContent }}</pre>
    <p class="text-xs italic text-gray-400 mt-2">(Notebook block placeholder)</p>
  </div>
</template>