<script setup lang="ts">
// Why: Using Vue's `PropType` for typed props definition.
import { PropType, computed } from 'vue';
import { ChatMessage as ChatMessageType } from '@/api/types'; // Import the type
// TODO (Phase 3+): Add Markdown rendering (e.g., using 'marked' or 'markdown-it')
// import { marked } from 'marked';

const props = defineProps({
  message: {
    type: Object as PropType<ChatMessageType>,
    required: true,
  },
});

// Why: Computed properties for dynamic classes based on message role.
const messageContainerClass = computed(() => [
  'flex mb-3',
  props.message.role === 'user' ? 'justify-end' : 'justify-start',
]);

const messageBubbleClass = computed(() => [
  'max-w-xs md:max-w-md lg:max-w-lg xl:max-w-2xl px-4 py-2 rounded-lg shadow-sm',
  props.message.role === 'user'
    ? 'bg-primary text-white dark:bg-primary-dark'
    : props.message.role === 'assistant'
    ? 'bg-gray-200 text-gray-800 dark:bg-dark-surface dark:text-dark-text-primary'
    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-700/30 dark:text-yellow-300 text-xs italic', // System or Error message
]);

// Why: Render message content as pre-formatted text to preserve whitespace and newlines.
// TODO (Phase 3+): Replace this with Markdown rendering for rich text.
const renderedContent = computed(() => {
    // if (props.message.role === 'assistant') {
    //    return marked.parse(props.message.content); // Example
    // }
    return props.message.content;
});

</script>

<template>
  <div :class="messageContainerClass">
    <div :class="messageBubbleClass">
      <!-- Why: Display role for assistant/system messages (optional for user). -->
      <p v-if="props.message.role !== 'user'" class="text-xs font-semibold mb-1 capitalize opacity-70">
        {{ props.message.role }}
      </p>
      <!-- Why: Use `whitespace-pre-wrap` to respect newlines and spaces from the model. -->
      <!-- If using markdown, v-html would be used here with the parsed content. -->
      <div class="text-sm whitespace-pre-wrap break-words" v-text="renderedContent"></div>
      <!-- TODO (Phase 3+): Add timestamp display if desired -->
      <!-- <p class="text-xs text-right mt-1 opacity-60">{{ new Date(props.message.timestamp).toLocaleTimeString() }}</p> -->
    </div>
  </div>
</template>