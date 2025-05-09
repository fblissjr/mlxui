import { ENDPOINTS } from './constants';
import type { ConfigUpdateRequest, ConfigUpdateResponse } from './types';

export const fetchBackendConfig = async (): Promise<Record<string, any> | null> => {
  try {
    const response = await fetch(ENDPOINTS.CONFIG.GET);
    if (!response.ok) {
      throw new Error(`HTTP error fetching config: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching backend config:', error);
    return null;
  }
};

export const updateBackendConfig = async (key: string, value: any): Promise<ConfigUpdateResponse> => {
  try {
    const requestBody: ConfigUpdateRequest = { key, value };
    const response = await fetch(ENDPOINTS.CONFIG.UPDATE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });
    const data: ConfigUpdateResponse = await response.json();
    if (!response.ok) {
      throw new Error(data.message || `HTTP error updating config: ${response.status}`);
    }
    return data;
  } catch (error) {
    console.error('Error updating backend config:', error);
    return { success: false, message: error instanceof Error ? error.message : 'Unknown error updating config' };
  }
};