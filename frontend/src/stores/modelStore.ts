import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { ModelInfo, ModelLoadResponse } from '@/api/types';
import { fetchLocalModels, loadModelByIdentifier, unloadCurrentModel, fetchCurrentModelInfo } from '@/api/models';
import { useAppStore } from './appStore';

export const useModelStore = defineStore('model', () => {
  const currentModel = ref<ModelInfo | null>(null);
  const availableModels = ref<ModelInfo[]>([]);
  const isModelLoading = ref(false);

  const appStore = useAppStore();

  async function fetchLocalModelsList() {
    if (isModelLoading.value && availableModels.value.length > 0) return; // Avoid concurrent fetches if already loading
    isModelLoading.value = true;
    appStore.clearError();
    try {
      const models = await fetchLocalModels();
      availableModels.value = models;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to fetch local models';
      appStore.setLastError(errorMsg);
      availableModels.value = [];
    } finally {
      isModelLoading.value = false;
    }
  }

  async function loadModel(identifier: string, adapterPath?: string) {
    if (isModelLoading.value) return;
    isModelLoading.value = true;
    appStore.clearError();
    // currentModel.value = null; // Optimistically clear or wait for response? Let's wait.

    try {
        const result: ModelLoadResponse = await loadModelByIdentifier(identifier, adapterPath);
        if (result.success && result.model_info) {
          currentModel.value = result.model_info;
          // If a new model is loaded, previous chat/notebook context might be invalid.
          // This could be handled by the generationStore watching currentModel.
        } else {
          const errorMsg = result.message || `Failed to load model '${identifier}'`;
          appStore.setLastError(errorMsg);
          // If loading failed, but a model was previously loaded, should we clear currentModel?
          // For now, let's assume backend reflects the true state, so if get_current_model_info
          // returns null after a failed load, that's fine.
        }
    } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error loading model';
        appStore.setLastError(errorMsg);
        currentModel.value = null; // Clear on exception
    } finally {
        isModelLoading.value = false;
    }
  }

  async function unloadModel() {
    if (!currentModel.value || isModelLoading.value) return;
    isModelLoading.value = true;
    appStore.clearError();
    const modelNameToUnload = currentModel.value.name;

    try {
        const result: ModelLoadResponse = await unloadCurrentModel();
        if (result.success) {
          currentModel.value = null;
        } else {
          const errorMsg = result.message || `Failed to unload model '${modelNameToUnload}'`;
          appStore.setLastError(errorMsg);
        }
    } catch (error) {
        const errorMsg = error instanceof Error ? error.message : `Unknown error unloading model '${modelNameToUnload}'`;
        appStore.setLastError(errorMsg);
    } finally {
        isModelLoading.value = false;
    }
  }

  async function fetchCurrentModelStatus() {
    // Avoid setting global loading for a status check unless it's the initial one
    // const initialLoad = !currentModel.value && availableModels.value.length === 0;
    // if (initialLoad) isModelLoading.value = true;
    appStore.clearError();
    try {
        const modelInfo = await fetchCurrentModelInfo();
        if (modelInfo && modelInfo.id) { // Check if modelInfo is not null and has an id
            currentModel.value = modelInfo;
        } else {
            currentModel.value = null;
        }
    } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Failed to fetch current model status';
        appStore.setLastError(errorMsg);
        currentModel.value = null; // Clear if status check fails
    } finally {
        // if (initialLoad) isModelLoading.value = false;
    }
  }

  return {
    currentModel,
    availableModels,
    isModelLoading,
    fetchLocalModelsList,
    loadModel,
    unloadModel,
    fetchCurrentModelStatus,
  };
});