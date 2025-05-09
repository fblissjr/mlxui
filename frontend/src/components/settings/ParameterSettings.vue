<script setup lang="ts">
import { computed } from 'vue';
import { useGenerationStore, DEFAULT_GENERATION_PARAMS } from '@/stores/generationStore';
import type { GenerationParams } from '@/api/types';
import { InfoIcon } from 'lucide-vue-next';

const generationStore = useGenerationStore();

const params = computed({
  get: () => generationStore.generationParams,
  set: (value) => generationStore.updateGenerationParams(value),
});

// Define which basic parameters are controlled here and their config
const PARAM_CONFIGS: Record<keyof Pick<GenerationParams, 'temperature' | 'max_tokens' | 'top_p' | 'top_k' | 'repetition_penalty' | 'seed' | 'ignore_chat_template'>, any> = {
    temperature: { min: 0.0, max: 2.0, step: 0.01, label: 'Temperature', description: 'Controls randomness. 0.0 = deterministic. Higher is more creative.', type: 'range' },
    max_tokens: { min: 1, max: 16384, step: 1, label: 'Max New Tokens', description: 'Maximum number of new tokens to generate.', type: 'range' }, // Increased max
    top_p: { min: 0.0, max: 1.0, step: 0.01, label: 'Top P (Nucleus Sampling)', description: 'Considers tokens with cumulative probability >= top_p. 1.0 to disable.', type: 'range' },
    top_k: { min: 0, max: 200, step: 1, label: 'Top K', description: 'Sample from the K most likely tokens. 0 to disable.', type: 'range' },
    repetition_penalty: { min: 0.0, max: 3.0, step: 0.01, label: 'Repetition Penalty', description: 'Penalizes recently seen tokens. >1.0 discourages, <1.0 encourages. 1.0 = none.', type: 'range' },
    seed: { label: 'Seed', description: 'PRNG seed for reproducibility. Empty or -1 for random.', type: 'number' },
    ignore_chat_template: { label: 'Ignore Chat Template', description: 'Send raw prompt/messages to the model without applying its chat template.', type: 'checkbox' }
};

const handleParamChange = (key: keyof GenerationParams, event: Event | boolean) => {
  let value: string | number | boolean | undefined;
  const target = event instanceof Event ? event.target as HTMLInputElement : null;

  if (typeof event === 'boolean') { // For checkbox
    value = event;
  } else if (target) {
    value = target.value;
    const configForKey = PARAM_CONFIGS[key as keyof typeof PARAM_CONFIGS];
    if (configForKey?.type === 'range' || configForKey?.type === 'number') {
      if (key === 'seed') {
          value = target.value === '' ? undefined : parseInt(target.value, 10);
          if (value !== undefined && isNaN(value as number)) value = undefined;
          if (value === -1) value = undefined;
      } else {
          value = parseFloat(target.value);
      }
    }
  } else {
    return; // Should not happen
  }
  generationStore.updateGenerationParams({ [key]: value });
};

const handleResetDefaults = () => {
  const defaultsToReset: Partial<GenerationParams> = {};
  for (const key of Object.keys(PARAM_CONFIGS) as Array<keyof typeof PARAM_CONFIGS>) {
    defaultsToReset[key] = DEFAULT_GENERATION_PARAMS[key];
  }
  generationStore.updateGenerationParams(defaultsToReset);
};

</script>

<template>
  <div class="p-1 space-y-1">
    <h3 class="text-lg font-semibold text-gray-800 dark:text-dark-text-primary mb-3">
      Generation Parameters
    </h3>

    <div v-for="(config, key) in PARAM_CONFIGS" :key="key" class="mb-4">
      <div class="flex justify-between items-center mb-1">
        <label :for="String(key)" class="text-sm font-medium text-gray-700 dark:text-dark-text-secondary flex items-center">
          {{ config.label }}
          <InfoIcon v-if="config.description" class="w-3.5 h-3.5 ml-1.5 text-gray-400 dark:text-gray-500 cursor-help" :title="config.description"/>
        </label>
        <span v-if="config.type !== 'checkbox'" class="text-xs font-mono text-gray-500 dark:text-dark-text-secondary">
          {{ key === 'seed' && (params[key as keyof GenerationParams] === undefined || params[key as keyof GenerationParams] === -1) ? 'Random' : params[key as keyof GenerationParams] }}
        </span>
      </div>
      <input
        v-if="config.type === 'range'"
        type="range"
        :id="String(key)"
        :min="config.min"
        :max="config.max"
        :step="config.step"
        :value="params[key as keyof GenerationParams] ?? DEFAULT_GENERATION_PARAMS[key as keyof GenerationParams]"
        @input="handleParamChange(key as keyof GenerationParams, $event)"
        class="w-full h-2 bg-gray-200 dark:bg-dark-border rounded-lg appearance-none cursor-pointer range-sm"
      />
      <input
        v-else-if="config.type === 'number' && key === 'seed'"
        type="number"
        :id="String(key)"
        :value="(params[key as keyof GenerationParams] === undefined || params[key as keyof GenerationParams] === null) ? '' : String(params[key as keyof GenerationParams])"
        @input="handleParamChange(key as keyof GenerationParams, $event)"
        :placeholder="config.description.includes('random') ? 'Random (-1 or empty)' : String(config.min)"
        class="mt-1 w-full p-2 border border-gray-300 dark:border-dark-border rounded-md bg-white dark:bg-dark-surface focus:ring-primary focus:border-primary"
      />
      <div v-else-if="config.type === 'checkbox'" class="flex items-center mt-1">
        <input
            type="checkbox"
            :id="String(key)"
            :checked="!!params[key as keyof GenerationParams]"
            @change="handleParamChange(key as keyof GenerationParams, ($event.target as HTMLInputElement).checked)"
            class="h-4 w-4 rounded border-gray-300 dark:border-dark-border text-primary focus:ring-primary"
        />
        <label :for="String(key)" class="ml-2 text-sm text-gray-600 dark:text-gray-300">{{ config.description }}</label>
      </div>
       <!-- <p v-if="config.type !== 'checkbox'" class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ config.description }}</p> -->
    </div>

    <div class="mt-5">
      <button @click="handleResetDefaults" class="btn btn-secondary !text-xs">
        Reset Basic Parameters
      </button>
    </div>
  </div>
</template>