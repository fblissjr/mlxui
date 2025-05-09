<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGenerationStore } from '@/stores/generationStore';
import { useModelStore } from '@/stores/modelStore';
import { FolderUpIcon, FolderDownIcon, ScissorsIcon, LoaderCircle } from 'lucide-vue-next';

const generationStore = useGenerationStore();
const modelStore = useModelStore();

const cacheFilenameBase = ref('mlxui_kv_cache'); // Default base filename
const trimTokensInput = ref<number>(100);

const operationStatus = computed(() => generationStore.cacheOperationStatus);
const isLoading = computed(() => generationStore.cacheOperationStatus.isLoading);
const isModelLoaded = computed(() => modelStore.currentModel !== null && modelStore.currentModel.is_loaded);

// Why: Filename logic centralized
const getFilenameWithExt = () => `${cacheFilenameBase.value.trim() || 'mlxui_kv_cache'}.safetensors`;

const handleSave = () => {
  if (!cacheFilenameBase.value.trim()) {
    generationStore.cacheOperationStatus = { message: "Filename cannot be empty.", type: 'error', isLoading: false };
    return;
  }
  generationStore.saveCache(getFilenameWithExt());
};

const handleLoad = () => {
  if (!cacheFilenameBase.value.trim()) {
    generationStore.cacheOperationStatus = { message: "Filename cannot be empty.", type: 'error', isLoading: false };
    return;
  }
  generationStore.loadCache(getFilenameWithExt());
};

const handleTrim = () => {
  if (trimTokensInput.value < 1) {
    generationStore.cacheOperationStatus = { message: "Tokens to trim must be at least 1.", type: 'error', isLoading: false };
    return;
  }
  generationStore.trimCache(trimTokensInput.value);
};

</script>

<template>
  <div class="p-1 space-y-4">
    <h3 class="text-lg font-semibold text-gray-800 dark:text-dark-text-primary mb-3">KV Cache Management</h3>

    <!-- Status Message -->
    <div v-if="operationStatus.message"
      :class="[
        'p-2.5 rounded-md text-sm',
        operationStatus.type === 'success' ? 'bg-green-100 dark:bg-green-700/30 text-green-700 dark:text-green-200' :
        operationStatus.type === 'error' ? 'bg-red-100 dark:bg-red-700/30 text-red-700 dark:text-red-200' :
        'bg-blue-100 dark:bg-blue-700/30 text-blue-700 dark:text-blue-200'
      ]"
    >
      {{ operationStatus.message }}
    </div>

    <p class="text-xs text-gray-500 dark:text-gray-400">
      Manage the Key-Value cache for the currently loaded model. This cache stores processed prompt tokens to speed up subsequent generations with similar prefixes.
    </p>

    <!-- Cache Size Info (Placeholder) -->
    <div v-if="operationStatus.success && typeof operationStatus.cache_size === 'number'" class="text-sm text-gray-600 dark:text-gray-400">
      Estimated cache size after operation: <span class="font-semibold">{{ operationStatus.cache_size }} tokens</span>
    </div>
    <div v-else-if="!isModelLoaded" class="text-sm text-yellow-600 dark:text-yellow-400 italic">
      Load a model to manage its KV cache.
    </div>


    <!-- Filename Input -->
    <div>
      <label for="cache-filename" class="block text-sm font-medium text-gray-700 dark:text-dark-text-secondary mb-1">
        Cache Filename Base
      </label>
      <input
        id="cache-filename"
        type="text"
        v-model="cacheFilenameBase"
        placeholder="e.g., my_chat_context"
        :disabled="isLoading"
        class="mt-1"
      />
      <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
        Final filename will be: <span class="font-mono">{{ getFilenameWithExt() }}</span>. Saved in backend's cache directory.
      </p>
    </div>

    <!-- Save/Load Buttons -->
    <div class="grid grid-cols-2 gap-3">
      <button @click="handleSave" class="btn btn-primary !text-sm" :disabled="isLoading || !isModelLoaded" title="Save current KV cache to file">
        <LoaderCircle v-if="isLoading && operationStatus.message.includes('Saving')" class="w-4 h-4 mr-1.5 animate-spin"/>
        <FolderUpIcon v-else class="w-4 h-4 mr-1.5"/>
        Save Cache
      </button>
      <button @click="handleLoad" class="btn btn-secondary !text-sm !bg-green-600 hover:!bg-green-700 text-white" :disabled="isLoading || !isModelLoaded" title="Load KV cache from file">
         <LoaderCircle v-if="isLoading && operationStatus.message.includes('Loading')" class="w-4 h-4 mr-1.5 animate-spin"/>
        <FolderDownIcon v-else class="w-4 h-4 mr-1.5"/>
        Load Cache
      </button>
    </div>

    <!-- Trim Controls -->
    <div class="pt-4 border-t border-gray-200 dark:border-dark-border">
      <label for="trim-tokens" class="block text-sm font-medium text-gray-700 dark:text-dark-text-secondary mb-1">
        Trim Tokens from Start of Cache
      </label>
      <div class="flex gap-3 items-center">
        <input
          id="trim-tokens"
          type="number"
          min="1"
          v-model.number="trimTokensInput"
          :disabled="isLoading"
          class="w-28"
        />
        <button @click="handleTrim" class="btn btn-secondary !text-sm !bg-yellow-500 hover:!bg-yellow-600 text-white" :disabled="isLoading || !isModelLoaded" title="Trim tokens from the current KV cache">
          <LoaderCircle v-if="isLoading && operationStatus.message.includes('Trimming')" class="w-4 h-4 mr-1.5 animate-spin"/>
          <ScissorsIcon v-else class="w-4 h-4 mr-1.5"/>
          Trim Cache
        </button>
      </div>
    </div>
  </div>
</template>