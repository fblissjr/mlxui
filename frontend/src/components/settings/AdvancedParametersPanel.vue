<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGenerationStore, DEFAULT_GENERATION_PARAMS } from '@/stores/generationStore';
import type { GenerationParams, KVCacheOptions } from '@/api/types';
import { Trash2Icon, PlusCircleIcon, XIcon, InfoIcon } from 'lucide-vue-next';

const generationStore = useGenerationStore();

const stoppingStringInput = ref('');
const extraEosTokenInput = ref(''); // New for extra EOS
const logitBiasTokenInput = ref('');
const logitBiasValueInput = ref<number>(0);

const params = computed(() => generationStore.generationParams);
const kvCacheOptsFromStore = computed((): KVCacheOptions => { // Ensure it always returns KVCacheOptions
    return params.value.kv_cache_options || DEFAULT_GENERATION_PARAMS.kv_cache_options || 
           { bits: undefined, group_size: 64, quantized_kv_start: 5000, max_size: undefined };
});


interface ParamConfigItem {
  min?: number; max?: number; step?: number; label: string; description: string; type: 'range' | 'number' | 'text' | 'checkbox';
}

const ADV_PARAM_CONFIG: Record<string, ParamConfigItem> = {
    min_p: { min: 0.0, max: 1.0, step: 0.01, label: 'Min P', description: 'Min-p sampling (0 disables). Keeps tokens with prob > top_prob * min_p.', type: 'range' },
    min_tokens_to_keep: { min: 1, max: 100, step: 1, label: 'Min Tokens to Keep (for Min P)', description: 'Ensures at least this many tokens are kept after Min P filtering.', type: 'range' },
    repetition_context_size: { min: 0, max: 2048, step: 1, label: 'Repetition Context Size', description: 'Window size for repetition penalty.', type: 'range' },
    xtc_probability: { min: 0.0, max: 1.0, step: 0.01, label: 'XTC Probability', description: 'Probability of applying XTC sampling (experimental). 0 to disable.', type: 'range'},
    xtc_threshold: { min: 0.0, max: 0.5, step: 0.01, label: 'XTC Threshold', description: 'Probability threshold for XTC sampling candidates (experimental).', type: 'range'},
    num_draft_tokens: { min: 1, max: 10, step: 1, label: 'Draft Tokens', description: 'Number of draft tokens (speculative decoding).', type: 'range' },
};
const KV_PARAM_CONFIG: Record<keyof KVCacheOptions, ParamConfigItem> = {
    bits: { min: 1, max: 8, step: 1, label: 'KV Cache Bits', description: 'Quantization bits (e.g., 2, 4, 8). Empty/0 disables.', type: 'number' },
    group_size: { min: 1, max: 256, step: 1, label: 'KV Cache Group Size', description: 'Group size for quantization.', type: 'range' },
    quantized_kv_start: { min: 0, max: 32768, step: 128, label: 'KV Quantization Start Token', description: 'Token position to start quantizing KV cache.', type: 'range' },
    max_size: { min: 0, max: 16384, step: 256, label: 'KV Cache Max Size (Rotating)', description: 'Max tokens for rotating KV cache (0 or empty for default, if model supports it).', type: 'number' }
};

const handleParamChange = (key: keyof GenerationParams, eventOrValue: Event | boolean | string | number) => {
    let value: any;
    if (typeof eventOrValue === 'object' && eventOrValue !== null && 'target' in eventOrValue) {
        const target = eventOrValue.target as HTMLInputElement;
        value = target.type === 'checkbox' ? target.checked : target.value;
    } else {
        value = eventOrValue;
    }

    const configForKey = ADV_PARAM_CONFIG[key as string];

    if (configForKey?.type === 'range' && (key === 'min_p' || key === 'xtc_probability' || key === 'xtc_threshold')) { // Floats
        value = parseFloat(String(value));
        if (value !== undefined && isNaN(value as number)) value = undefined;
    } else if (configForKey?.type === 'range' || configForKey?.type === 'number') {
        value = (value === '' || value === null) ? undefined : parseInt(String(value), 10);
        if (value !== undefined && isNaN(value as number)) value = undefined;
    }
    generationStore.updateGenerationParams({ [key]: value });
};

const handleKvCacheOptionChange = (key: keyof KVCacheOptions, event: Event) => {
  const target = event.target as HTMLInputElement;
  let value: string | number | undefined = target.value;
  const configForKey = KV_PARAM_CONFIG[key];

  if (configForKey?.type === 'number' || configForKey?.type === 'range') {
      value = (target.value === '' || target.value === null) ? undefined : parseInt(target.value, 10);
      if (value !== undefined && isNaN(value as number)) value = undefined;
      if ((key === 'bits' || key === 'max_size') && (value === 0 || value === undefined)) {
        value = undefined;
      }
  }

  const currentOpts = params.value.kv_cache_options || DEFAULT_GENERATION_PARAMS.kv_cache_options || {};
  const newKvOpts: KVCacheOptions = { ...currentOpts, [key]: value };
  
  if (newKvOpts.bits === undefined) {
    // delete newKvOpts.group_size; // Optional: clear related if bits is disabled
    // delete newKvOpts.quantized_kv_start;
  }
  generationStore.updateGenerationParams({ kv_cache_options: newKvOpts });
};

const handleAddStoppingString = () => {
  const newString = stoppingStringInput.value;
  if (newString) {
    const currentStrings = params.value.stopping_strings || [];
    generationStore.updateGenerationParams({ stopping_strings: [...currentStrings, newString] });
    stoppingStringInput.value = '';
  }
};
const handleRemoveStoppingString = (index: number) => {
  const currentStrings = [...(params.value.stopping_strings || [])];
  currentStrings.splice(index, 1);
  generationStore.updateGenerationParams({ stopping_strings: newStrings });
};

const handleAddExtraEosToken = () => {
  const newToken = extraEosTokenInput.value.trim();
  if (newToken) {
    const currentTokens = params.value.extra_eos_tokens || [];
    if (!currentTokens.includes(newToken)) {
        generationStore.updateGenerationParams({ extra_eos_tokens: [...currentTokens, newToken] });
    }
    extraEosTokenInput.value = '';
  }
};
const handleRemoveExtraEosToken = (index: number) => {
  const currentTokens = [...(params.value.extra_eos_tokens || [])];
  currentTokens.splice(index, 1);
  generationStore.updateGenerationParams({ extra_eos_tokens: currentTokens });
};


const handleAddLogitBias = () => {
  const tokenStr = logitBiasTokenInput.value.trim();
  if (!tokenStr) return;
  const currentBias = params.value.logit_bias || {};
  generationStore.updateGenerationParams({ logit_bias: { ...currentBias, [tokenStr]: logitBiasValueInput.value } });
  logitBiasTokenInput.value = '';
  logitBiasValueInput.value = 0;
};
const handleRemoveLogitBias = (tokenKey: string) => {
  const currentBias = { ...(params.value.logit_bias || {}) };
  delete currentBias[tokenKey];
  generationStore.updateGenerationParams({ logit_bias: currentBias });
};
</script>

<template>
  <div class="p-1 space-y-5">
    <h3 class="text-lg font-semibold text-gray-800 dark:text-dark-text-primary mb-3">Advanced Parameters</h3>

    <div v-for="(config, key) in ADV_PARAM_CONFIG" :key="key" class="mb-4">
      <div class="flex justify-between items-center mb-1">
        <label :for="String(key)" class="text-sm font-medium text-gray-700 dark:text-dark-text-secondary flex items-center">
          {{ config.label }}
          <InfoIcon v-if="config.description" class="w-3.5 h-3.5 ml-1.5 text-gray-400 dark:text-gray-500 cursor-help" :title="config.description"/>
        </label>
        <span class="text-xs font-mono text-gray-500 dark:text-dark-text-secondary">
          {{ params[key as keyof GenerationParams] }}
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
    </div>

    <div class="p-3 border border-gray-200 dark:border-dark-border rounded-md space-y-3 bg-gray-50 dark:bg-dark-surface">
      <div class="flex items-center justify-between">
        <label for="use_speculative" class="text-sm font-medium text-gray-700 dark:text-dark-text-secondary flex items-center">
            Enable Speculative Decoding
            <InfoIcon class="w-3.5 h-3.5 ml-1.5 text-gray-400 dark:text-gray-500 cursor-help" title="Uses a smaller 'draft' model to potentially speed up generation."/>
        </label>
        <input
          type="checkbox"
          id="use_speculative"
          :checked="params.use_speculative || false"
          @change="handleParamChange('use_speculative', ($event.target as HTMLInputElement).checked)"
          class="h-4 w-4 rounded border-gray-300 dark:border-dark-border text-primary focus:ring-primary"
        />
      </div>
      <template v-if="params.use_speculative">
        <div>
          <label for="draft_model_identifier" class="block text-sm font-medium mb-1 text-gray-700 dark:text-dark-text-secondary">Draft Model Identifier</label>
          <input
            type="text"
            id="draft_model_identifier"
            :value="params.draft_model_identifier || ''"
            @input="handleParamChange('draft_model_identifier', ($event.target as HTMLInputElement).value)"
            placeholder="Path or Hub ID of draft model"
            class="mt-1 w-full p-2"
          />
        </div>
        <div v-if="ADV_PARAM_CONFIG.num_draft_tokens">
            <div class="flex justify-between items-center mb-1">
                <label for="num_draft_tokens" class="text-sm font-medium text-gray-700 dark:text-dark-text-secondary">{{ ADV_PARAM_CONFIG.num_draft_tokens.label }}</label>
                <span class="text-xs font-mono text-gray-500 dark:text-dark-text-secondary">{{ params.num_draft_tokens }}</span>
            </div>
            <input
                type="range"
                id="num_draft_tokens"
                :min="ADV_PARAM_CONFIG.num_draft_tokens.min" :max="ADV_PARAM_CONFIG.num_draft_tokens.max" :step="ADV_PARAM_CONFIG.num_draft_tokens.step"
                :value="params.num_draft_tokens ?? DEFAULT_GENERATION_PARAMS.num_draft_tokens"
                @input="handleParamChange('num_draft_tokens', $event)"
                class="w-full h-2 bg-gray-200 dark:bg-dark-border rounded-lg appearance-none cursor-pointer range-sm"
            />
        </div>
      </template>
    </div>

    <div class="p-3 border border-gray-200 dark:border-dark-border rounded-md space-y-3 bg-gray-50 dark:bg-dark-surface">
        <h4 class="text-sm font-medium text-gray-700 dark:text-dark-text-secondary mb-1 flex items-center">
            KV Cache Options
             <InfoIcon class="w-3.5 h-3.5 ml-1.5 text-gray-400 dark:text-gray-500 cursor-help" title="Options for Key-Value cache during generation. Quantization enabled by setting 'KV Cache Bits'."/>
        </h4>
        <div v-for="(config, key) in KV_PARAM_CONFIG" :key="key">
             <div class="flex justify-between items-center mb-1">
                <label :for="`kv_cache_options.${key}`" class="text-sm font-medium text-gray-700 dark:text-dark-text-secondary">{{ config.label }}</label>
                <span class="text-xs font-mono text-gray-500 dark:text-dark-text-secondary">
                    {{ kvCacheOptsFromStore[key as keyof KVCacheOptions] ?? (key === 'bits' || key === 'max_size' ? 'Auto' : DEFAULT_GENERATION_PARAMS.kv_cache_options![key as keyof KVCacheOptions] ) }}
                </span>
            </div>
             <input
                v-if="config.type === 'number'"
                type="number"
                :id="`kv_cache_options.${key}`"
                :min="config.min" :max="config.max" :step="config.step"
                :value="(kvCacheOptsFromStore[key as keyof KVCacheOptions] === undefined || kvCacheOptsFromStore[key as keyof KVCacheOptions] === null) ? '' : String(kvCacheOptsFromStore[key as keyof KVCacheOptions])"
                @input="handleKvCacheOptionChange(key as keyof KVCacheOptions, $event)"
                :placeholder="key === 'bits' || key === 'max_size' ? 'Auto/Disabled (empty or 0)' : String(DEFAULT_GENERATION_PARAMS.kv_cache_options![key as keyof KVCacheOptions])"
                class="mt-1 w-full p-2"
            />
            <input
                v-else-if="config.type === 'range'"
                type="range"
                :id="`kv_cache_options.${key}`"
                :min="config.min" :max="config.max" :step="config.step"
                :value="kvCacheOptsFromStore[key as keyof KVCacheOptions] ?? DEFAULT_GENERATION_PARAMS.kv_cache_options![key as keyof KVCacheOptions]"
                @input="handleKvCacheOptionChange(key as keyof KVCacheOptions, $event)"
                class="w-full h-2 bg-gray-200 dark:bg-dark-border rounded-lg appearance-none cursor-pointer range-sm mt-1"
            />
        </div>
    </div>

    <div class="space-y-1">
      <label for="extra_eos_token_input" class="block text-sm font-medium text-gray-700 dark:text-dark-text-secondary flex items-center">
          Extra End-of-Sequence Tokens
          <InfoIcon class="w-3.5 h-3.5 ml-1.5 text-gray-400 dark:text-gray-500 cursor-help" title="Additional tokens that signify the end of generation. Can be token ID or string."/>
      </label>
      <div class="flex gap-2">
        <input
          type="text"
          id="extra_eos_token_input"
          v-model="extraEosTokenInput"
          placeholder="Add token (e.g., <|eot_id|> or 12345)"
          @keydown.enter.prevent="handleAddExtraEosToken"
          class="flex-1 p-2"
        />
        <button @click="handleAddExtraEosToken" class="btn btn-secondary !py-2 !px-3 text-xs">
          <PlusCircleIcon class="w-4 h-4 mr-1 inline" />Add EOS
        </button>
      </div>
      <div v-if="params.extra_eos_tokens && params.extra_eos_tokens.length > 0" class="flex flex-wrap gap-1.5 mt-2">
        <span
          v-for="(token, index) in params.extra_eos_tokens" :key="index"
          class="bg-gray-200 dark:bg-dark-border text-gray-700 dark:text-dark-text-secondary text-xs px-2 py-1 rounded-full flex items-center"
        >
          {{ token }}
          <button @click="handleRemoveExtraEosToken(index)" class="ml-1.5 text-red-500 hover:text-red-700" title="Remove">
            <XIcon class="w-3 h-3" />
          </button>
        </span>
      </div>
    </div>

    <div class="space-y-1">
      <label class="block text-sm font-medium text-gray-700 dark:text-dark-text-secondary">Stopping Strings</label>
      <!-- ... stopping strings input ... (same as before) -->
       <div class="flex gap-2">
        <input
          type="text"
          id="stopping_string_input"
          v-model="stoppingStringInput"
          placeholder="Add sequence (e.g., '\nUser:')"
          @keydown.enter.prevent="handleAddStoppingString"
          class="flex-1 p-2"
        />
        <button @click="handleAddStoppingString" class="btn btn-secondary !py-2 !px-3 text-xs">
          <PlusCircleIcon class="w-4 h-4 mr-1 inline" />Add Stop
        </button>
      </div>
      <div v-if="params.stopping_strings && params.stopping_strings.length > 0" class="flex flex-wrap gap-1.5 mt-2">
        <span
          v-for="(str, index) in params.stopping_strings" :key="index"
          class="bg-gray-200 dark:bg-dark-border text-gray-700 dark:text-dark-text-secondary text-xs px-2 py-1 rounded-full flex items-center"
        >
          <pre class="inline bg-transparent p-0 m-0 text-xs whitespace-pre-wrap">{{ JSON.stringify(str) }}</pre>
          <button @click="handleRemoveStoppingString(index)" class="ml-1.5 text-red-500 hover:text-red-700" title="Remove">
            <XIcon class="w-3 h-3" />
          </button>
        </span>
      </div>
    </div>

    <div class="space-y-1">
      <label class="block text-sm font-medium text-gray-700 dark:text-dark-text-secondary">Logit Bias</label>
      <!-- ... logit bias input ... (same as before) -->
       <div class="flex gap-2 items-center">
        <input
          type="text"
          v-model="logitBiasTokenInput"
          placeholder="Token ID string"
          class="flex-1 p-2"
        />
        <input
          type="number"
          v-model.number="logitBiasValueInput"
          step="0.1"
          class="w-24 p-2"
        />
        <button @click="handleAddLogitBias" :disabled="!logitBiasTokenInput.trim()" class="btn btn-secondary !py-2 !px-3 text-xs">
            <PlusCircleIcon class="w-4 h-4 mr-1 inline" />Add Bias
        </button>
      </div>
      <div v-if="params.logit_bias && Object.keys(params.logit_bias).length > 0" class="mt-2 max-h-28 overflow-y-auto space-y-0.5 text-xs">
        <div v-for="(value, tokenKey) in params.logit_bias" :key="tokenKey" class="flex justify-between items-center bg-gray-100 dark:bg-dark-border/50 px-2 py-0.5 rounded">
          <span class="font-mono">ID: {{ tokenKey }}</span>
          <span class="font-mono">Bias: {{ value.toFixed(1) }}</span>
          <button @click="handleRemoveLogitBias(tokenKey)" class="text-red-500 hover:text-red-700" title="Remove">
            <XIcon class="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>