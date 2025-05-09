import { ENDPOINTS } from './constants';

export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(ENDPOINTS.HEALTH, {
       method: 'GET',
       headers: {
         'Accept': 'application/json',
       },
       cache: 'no-store',
    });
    if (!response.ok) {
      console.error(`Backend health check failed: Status ${response.status}`);
      return false;
    }
    const data = await response.json();
    return data?.status === 'ok';
  } catch (error) {
    console.error('Error during backend health check:', error);
    return false;
  }
};