<script setup lang="ts">
import { ref, watch } from 'vue';
import { SendHorizonal } from 'lucide-vue-next';

// Why: Define props and emits for component communication.
const props = defineProps<{
  isGenerating: boolean;
}>();

const emit = defineEmits<{
  (e: 'sendMessage', message: string): void;
}>();

const currentMessage = ref('');
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const handleSubmit = () => {
  if (currentMessage.value.trim() && !props.isGenerating) {
    emit('sendMessage', currentMessage.value.trim());
    currentMessage.value = ''; // Clear input after sending
    // Why: Auto-resize on submit as well to shrink if text is cleared
    autoResizeTextarea();
  }
};

// Why: Handle Shift+Enter for newline, Enter for submit.
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault(); // Prevent default newline on Enter
    handleSubmit();
  }
  // Optional: Handle Ctrl+Enter or Cmd+Enter for submit if preferred
  // if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
  //   handleSubmit();
  // }
};

// Why: Auto-resize textarea height based on content.
const autoResizeTextarea = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'; // Reset height
    // Set to scrollHeight to fit content, with a max height
    const maxHeight = 128; // Example max height (8rem)
    textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, maxHeight)}px`;
  }
};

// Why: Watch for changes in currentMessage to trigger auto-resize.
watch(currentMessage, autoResizeTextarea);

</script>

<template>
  <form @submit.prevent="handleSubmit" class="flex items-end gap-2 p-2 border-t border-gray-200 dark:border-dark-border">
    <textarea
      ref="textareaRef"
      v-model="currentMessage"
      @keydown="handleKeydown"
      :disabled="props.isGenerating"
      placeholder="Type your message... (Shift+Enter for newline)"
      class="flex-grow p-2.5 text-sm rounded-lg border border-gray-300 dark:border-dark-border bg-white dark:bg-dark-surface focus:ring-2 focus:ring-primary focus:border-transparent resize-none overflow-y-auto transition-all duration-150"
      rows="1"
      style="min-height: 44px;"></textarea>
    <button
      type="submit"
      :disabled="!currentMessage.trim() || props.isGenerating"
      class="btn btn-primary !py-2.5 !px-3.5 shrink-0"
      title="Send Message"
    >
      <SendHorizonal class="w-5 h-5" />
    </button>
  </form>
</template>