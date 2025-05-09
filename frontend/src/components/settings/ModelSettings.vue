<script setup lang="ts">
// Why: Composition API with <script setup> for concise component logic.
import { computed, onMounted, ref, watch } from 'vue';
import { useModelStore } from '@/stores/modelStore';
import { useAppStore } from '@/stores/appStore';
import type { ModelInfo } from '@/api/types'; // Using type for clarity
import { RefreshCwIcon, AlertTriangleIcon, LoaderCircle } from 'lucide-vue-next';

const modelStore = useModelStore();
const appStore = useAppStore();

// Why: Local state for UI elements like input fields.
const manualIdentifier = ref('');
const adapterPath = ref('');
const isLoadingList = ref(false); // Specific loading state for the list

// Why: Computed properties to reactively get data from the store.
const availableModels = computed(() => modelStore.availableModels);
const currentModel = computed(() => modelStore.currentModel);
const isModelLoadingGlobal = computed(() => modelStore.isModelLoading); // Global loading state
const loadError = computed(() => appStore.lastError); // Display global errors

// Why: onMounted hook to fetch initial data when the component is created.
onMounted(async () => {
  if (availableModels.value.length === 0) { // Fetch only if list is empty
    await refreshModelLists();
  }
  // Check if a model is already loaded (e.g., from a previous session or default load)
  if (!currentModel.value) {
    await modelStore.fetchCurrentModelStatus();
  }
});

// Why: Method to encapsulate list refreshing logic.
const refreshModelLists = async () => {
  isLoadingList.value = true;
  appStore.clearError(); // Clear previous errors
  await modelStore.fetchLocalModelsList();
  isLoadingList.value = false;
};

// Why: Handles the action of loading a model.
const handleLoadModel = async (identifier: string, adapter?: string) => {
  if (!identifier.trim() || isModelLoadingGlobal.value) return;
  appStore.clearError();
  await modelStore.loadModel(identifier.trim(), adapter?.trim() || undefined);
  // Clear inputs after attempt
  manualIdentifier.value = '';
  adapterPath.value = '';
  // Optionally refresh the list again, especially if a Hub model was loaded and is now cached
  // await refreshModelLists();
};

// Why: Handles unloading the currently active model.
const handleUnloadModel = async () => {
  if (!currentModel.value || isModelLoadingGlobal.value) return;
  appStore.clearError();
  await modelStore.unloadModel();
};

// Why: Watch for changes in currentModel to potentially clear manual inputs
// or perform other UI updates if needed.
watch(currentModel, (newModel) => {
  if (newModel) {
    // If a model gets loaded successfully, potentially clear the manual input fields
    // if they match the loaded model to avoid re-loading the same.
    // Or, update them to reflect the current model's details.
    // For now, let's clear them after an attempt in handleLoadModel.
  }
});

</script>

<template>
  <div class="space-y-5">
    <h3 class="text-lg font-semibold text-gray-800 dark:text-dark-text-primary">Model Selection</h3>

    <!-- Error Display -->
    <div v-if="loadError" class="p-3 bg-red-100 dark:bg-red-700/20 text-red-700 dark:text-red-200 rounded-md text-sm flex items-center">
      <AlertTriangleIcon class="w-5 h-5 mr-2 shrink-0" />
      <span>{{ loadError }}</span>
    </div>

    <!-- Currently Loaded Model Info -->
    <div v-if="currentModel" class="p-3 bg-green-50 dark:bg-green-700/20 rounded-md border border-green-200 dark:border-green-600">
      <h4 class="font-medium text-sm text-gray-700 dark:text-dark-text-secondary mb-1.5">Currently Loaded:</h4>
      <div class="text-sm space-y-0.5">
        <p><strong class="font-semibold">Name:</strong> {{ currentModel.name }}</p>
        <p class="truncate" :title="currentModel.id">
          <strong class="font-semibold">Identifier:</strong> {{ currentModel.id }} ({{ currentModel.source }})
        </p>
        <p v-if="currentModel.adapter_path">
          <strong class="font-semibold">Adapter:</strong> {{ currentModel.adapter_path }}
        </p>
        <div v-if="currentModel.config" class="text-xs opacity-80">
          <span v-if="currentModel.config.model_type">Type: {{ currentModel.config.model_type }}</span>
          <span v-if="currentModel.config.quantization" class="ml-2">
            | Quant: {{ currentModel.config.quantization.bits }}bit, G{{ currentModel.config.quantization.group_size }}
          </span>
        </div>
      </div>
      <button
        @click="handleUnloadModel"
        :disabled="isModelLoadingGlobal"
        class="mt-3 btn btn-danger !text-xs !py-1 !px-2.5"
      >
        <LoaderCircle v-if="isModelLoadingGlobal" class="w-4 h-4 mr-1.5 animate-spin" />
        {{ isModelLoadingGlobal ? 'Processing...' : 'Unload Model' }}
      </button>
    </div>
    <div v-else-if="!isModelLoadingGlobal" class="p-3 bg-yellow-50 dark:bg-yellow-700/20 rounded-md text-sm text-yellow-700 dark:text-yellow-200">
      No model is currently loaded.
    </div>

    <!-- Load by Identifier (Path or Hub ID) -->
    <div class="space-y-3">
      <div>
        <label for="manual-identifier" class="block text-sm font-medium text-gray-700 dark:text-dark-text-secondary mb-1">
          Load Model by Path or Hub ID
        </label>
        <input
          id="manual-identifier"
          type="text"
          v-model="manualIdentifier"
          placeholder="/path/to/local_model or username/repo-name"
          :disabled="isModelLoadingGlobal"
        />
      </div>
      <div>
        <label for="adapter-path" class="block text-sm font-medium text-gray-700 dark:text-dark-text-secondary mb-1">
          Optional Adapter Path (Local)
        </label>
        <input
          id="adapter-path"
          type="text"
          v-model="adapterPath"
          placeholder="/path/to/adapter_weights"
          :disabled="isModelLoadingGlobal"
        />
      </div>
      <button
        @click="handleLoadModel(manualIdentifier, adapterPath)"
        :disabled="!manualIdentifier.trim() || isModelLoadingGlobal"
        class="btn btn-primary w-full sm:w-auto"
      >
        <LoaderCircle v-if="isModelLoadingGlobal" class="w-4 h-4 mr-1.5 animate-spin" />
        {{ isModelLoadingGlobal ? 'Loading...' : 'Load Model' }}
      </button>
    </div>

    <!-- Locally Discovered Models -->
    <div>
      <div class="flex justify-between items-center mb-1.5">
        <label class="block text-sm font-medium text-gray-700 dark:text-dark-text-secondary">
          Locally Discovered Models
        </label>
        <button
          @click="refreshModelLists"
          :disabled="isLoadingList || isModelLoadingGlobal"
          class="text-xs text-primary hover:text-primary-dark dark:text-primary-light dark:hover:text-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
          title="Rescan configured directories"
        >
          <RefreshCwIcon class="w-3.5 h-3.5 mr-1" :class="{'animate-spin': isLoadingList}" />
          {{ isLoadingList ? 'Scanning...' : 'Refresh List' }}
        </button>
      </div>
      <div class="max-h-60 overflow-y-auto border border-gray-300 dark:border-dark-border rounded-md bg-gray-50 dark:bg-dark-surface">
        <div v-if="isLoadingList && availableModels.length === 0" class="p-4 text-center text-sm text-gray-500 dark:text-dark-text-secondary flex items-center justify-center">
           <LoaderCircle class="w-4 h-4 mr-2 animate-spin"/> Loading models...
        </div>
        <div v-else-if="!isLoadingList && availableModels.length === 0" class="p-4 text-center text-sm text-gray-500 dark:text-dark-text-secondary">
          No local models found in scanned directories.
          <p class="text-xs mt-1">Use the input above to load by specific path or Hub ID.</p>
        </div>
        <div v-else>
          <div
            v-for="model in availableModels"
            :key="model.id"
            class="p-2.5 border-b border-gray-200 dark:border-dark-border last:border-b-0 hover:bg-gray-100 dark:hover:bg-dark-border/50"
            :class="{'bg-primary/10 dark:bg-primary/20': currentModel?.id === model.id}"
          >
            <div class="flex justify-between items-center">
              <div>
                <div class="font-medium text-sm text-gray-800 dark:text-dark-text-primary">{{ model.name }}</div>
                <div class="text-xs text-gray-500 dark:text-dark-text-secondary truncate" :title="model.id">
                  Path: {{ model.id }}
                </div>
              </div>
              <button
                v-if="currentModel?.id !== model.id"
                @click="handleLoadModel(model.id, model.adapter_path)"
                :disabled="isModelLoadingGlobal"
                class="btn btn-primary !text-xs !py-1 !px-2 shrink-0"
              >
                <LoaderCircle v-if="isModelLoadingGlobal" class="w-3 h-3 mr-1 animate-spin" />
                Load
              </button>
              <span v-else class="text-xs font-semibold text-green-600 dark:text-green-400 px-2">Loaded</span>
            </div>
          </div>
        </div>
      </div>
      <!-- TODO (Phase 3+): Display configured scan directories from backend config -->
      <!-- <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
        Scanned directories: {{ appConfig.models.scan_directories.join(', ') }}
      </p> -->
    </div>
  </div>
</template>