import { ENDPOINTS } from './constants';
import type { ModelInfo, ModelLoadRequest, ModelLoadResponse } from './types';

export const fetchLocalModels = async (): Promise<ModelInfo[]> => {
    const response = await fetch(ENDPOINTS.MODELS.LIST);
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to fetch local models list" }));
        throw new Error(errorData.detail || `HTTP error ${response.status}`);
    }
    // The backend returns a list directly, not nested under {"models": ...}
    const data: ModelInfo[] = await response.json();
    return data;
};

export const loadModelByIdentifier = async (identifier: string, adapterPath?: string): Promise<ModelLoadResponse> => {
    const requestBody: ModelLoadRequest = { identifier, adapter_path: adapterPath };
    const response = await fetch(ENDPOINTS.MODELS.LOAD, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
    });
    const data: ModelLoadResponse = await response.json();
    if (!response.ok) {
        // Use message from response if available, otherwise construct one
        throw new Error(data.message || `HTTP error ${response.status}`);
    }
    return data;
};

export const unloadCurrentModel = async (): Promise<ModelLoadResponse> => {
    const response = await fetch(ENDPOINTS.MODELS.UNLOAD, { method: 'POST' });
    const data: ModelLoadResponse = await response.json();
     if (!response.ok) {
        throw new Error(data.message || `HTTP error ${response.status}`);
    }
    return data;
};

export const fetchCurrentModelInfo = async (): Promise<ModelInfo | null> => {
    const response = await fetch(ENDPOINTS.MODELS.CURRENT);
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to fetch current model info" }));
        throw new Error(errorData.detail || `HTTP error ${response.status}`);
    }
    if (response.status === 204 || response.headers.get("content-length") === "0") { // No content
        return null;
    }
    const data: ModelInfo | null = await response.json();
    return data;
};