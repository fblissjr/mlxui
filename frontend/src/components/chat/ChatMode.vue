<script setup lang="ts">
import { ref, computed, onUnmounted, nextTick, watch } from 'vue';
import ChatInput from './ChatInput.vue';
import ChatMessageDisplay from './ChatMessage.vue';
import { useGenerationStore } from '@/stores/generationStore';
import { useModelStore } from '@/stores/modelStore';
import { useAppStore } from '@/stores/appStore';
import type { ChatMessage as ChatMessageType } from '@/api/types';
import { LoaderCircle, MessageSquarePlusIcon, Trash2Icon, StopCircleIcon } from 'lucide-vue-next';

const generationStore = useGenerationStore();
const modelStore = useModelStore();
const appStore = useAppStore();

const conversation = ref<ChatMessageType[]>([]);
const messagesEndRef = ref<HTMLElement | null>(null);

const isGenerating = computed(() => generationStore.isGenerating);
const currentModel = computed(() => modelStore.currentModel);
const backendStatus = computed(() => appStore.backendStatus);

const scrollToBottom = () => {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
};

watch(conversation, scrollToBottom, { deep: true });
watch(isGenerating, (newVal, oldVal) => {
    if (newVal || (!newVal && oldVal)) { // Scroll on start or end of generation
        scrollToBottom();
    }
});

const handleSendMessage = (userInput: string) => {
  if (!userInput.trim() || !currentModel.value || backendStatus.value !== 'online') {
    if (!currentModel.value) appStore.setLastError("Cannot send message: No model is loaded.");
    if (backendStatus.value !== 'online') appStore.setLastError("Cannot send message: Backend is offline.");
    return;
  }
  appStore.clearError();

  const userMessage: ChatMessageType = {
    id: crypto.randomUUID(),
    role: 'user',
    content: userInput,
    timestamp: Date.now(),
  };
  conversation.value.push(userMessage);

  const assistantMsgId = crypto.randomUUID();
  const assistantPlaceholder: ChatMessageType = {
    id: assistantMsgId,
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
  };
  conversation.value.push(assistantPlaceholder);

  // Prepare messages for the backend, including history for templating
  const messagesForBackend = conversation.value
    .filter(m => m.role === 'user' || (m.role === 'assistant' && m.id !== assistantMsgId)) // Exclude empty placeholder
    .map(m => ({ role: m.role, content: m.content }));
    // TODO: Add system prompt if defined in settings, prepend to messagesForBackend

  generationStore.startGenerationStream(
    { messages: messagesForBackend }, // Send the conversation history
    (chunkText: string) => {
      const assistantMsg = conversation.value.find(m => m.id === assistantMsgId);
      if (assistantMsg && assistantMsg.role === 'assistant') {
        assistantMsg.content += chunkText;
      }
    },
    () => { // onStreamComplete
      const assistantMsg = conversation.value.find(m => m.id === assistantMsgId);
      if (assistantMsg && assistantMsg.content === '' && !isGenerating.value) {
          // If stream completed but content is still empty (e.g., stop word immediately hit)
          assistantMsg.content = "[Empty response]";
      }
    },
    (errorMessage: string) => {
      const assistantMsg = conversation.value.find(m => m.id === assistantMsgId);
      if (assistantMsg && assistantMsg.role === 'assistant') {
        assistantMsg.content = `Sorry, an error occurred: ${errorMessage}`;
        assistantMsg.role = 'error';
      } else {
        conversation.value.push({
            id: crypto.randomUUID(), role: 'error',
            content: `Stream Error: ${errorMessage}`, timestamp: Date.now()
        });
      }
    }
  );
};

const handleStopGeneration = () => {
  generationStore.stopGenerationStream();
};

const handleNewChat = () => {
    if (isGenerating.value) {
        generationStore.stopGenerationStream("New chat started");
    }
    conversation.value = [];
    appStore.clearError();
    // Reset any ongoing stream output in the store as well
    generationStore.currentOutputStream = ""; 
    generationStore.lastChunk = null;
    // The backend's _update_prompt_cache will reset if new_prompt_tokens are different
    // than its internal prompt_cache_tokens. So, starting a new chat (which leads to
    // a different initial message list) will effectively reset the backend cache context.
};

onUnmounted(() => {
  if (isGenerating.value) {
    generationStore.stopGenerationStream("Component unmounted");
  }
});
</script>

<template>
  <div class="flex flex-col h-full max-h-[calc(100vh-10rem)] sm:max-h-[calc(100vh-12rem)] print:max-h-full print:h-auto">
    <div class="flex justify-end mb-2 print:hidden">
        <button @click="handleNewChat" class="btn btn-secondary !text-xs !py-1.5 !px-3" title="Start a new chat session">
           <Trash2Icon class="w-3.5 h-3.5 mr-1.5"/> New Chat
       </button>
    </div>

    <div class="flex-grow overflow-y-auto mb-4 p-1 sm:p-2 space-y-3 pr-1 bg-white dark:bg-dark-surface shadow-inner rounded-md print:overflow-visible print:shadow-none print:p-0">
      <ChatMessageDisplay
        v-for="message in conversation"
        :key="message.id"
        :message="message"
      />
      <div ref="messagesEndRef"></div>
      <div v-if="conversation.length === 0 && !isGenerating && currentModel" class="text-center text-gray-400 dark:text-gray-500 py-10">
        <MessageSquarePlusIcon class="w-12 h-12 sm:w-16 sm:h-16 mx-auto opacity-30" />
        <p class="mt-2 text-sm sm:text-base">Type a message below to start.</p>
      </div>
    </div>

    <div v-if="isGenerating" class="flex flex-col items-center mb-2 space-y-2 px-2 print:hidden">
        <div class="flex items-center text-sm text-gray-500 dark:text-dark-text-secondary">
            <LoaderCircle class="w-4 h-4 mr-2 animate-spin text-primary" />
            Generating...
        </div>
        <button
            @click="handleStopGeneration"
            class="btn btn-danger !py-1 !px-3 text-xs flex items-center"
        >
            <StopCircleIcon class="w-3.5 h-3.5 mr-1.5"/> Stop
        </button>
    </div>

    <div class="mt-auto border-t border-gray-200 dark:border-dark-border pt-2 print:hidden">
      <div v-if="!currentModel" class="text-center p-3 text-sm text-gray-500 dark:text-dark-text-secondary bg-gray-100 dark:bg-dark-surface rounded-md mb-2 shadow">
        Please load a model from <button @click="appStore.toggleSettingsPanel" class="text-primary dark:text-primary-light underline hover:text-primary-dark dark:hover:text-primary font-medium">Settings</button> to start chatting.
      </div>
       <div v-else-if="backendStatus !== 'online'" class="text-center p-3 text-sm text-yellow-700 dark:text-yellow-300 bg-yellow-50 dark:bg-yellow-800/30 border border-yellow-300 dark:border-yellow-700 rounded-md mb-2 shadow">
        Backend is {{ backendStatus }}. Chat functionality may be limited.
      </div>
      <ChatInput
        :isGenerating="isGenerating"
        @send-message="handleSendMessage"
        :disabled="!currentModel || isGenerating || backendStatus !== 'online'"
      />
    </div>
  </div>
</template>