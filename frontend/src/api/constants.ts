export const API_URL = import.meta.env.VITE_API_URL || '';

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsHost = window.location.hostname + (window.location.port ? `:${window.location.port}` : '');
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `${wsProtocol}//${wsHost}`;


export const ENDPOINTS = {
    HEALTH: `${API_URL}/api/health`,
    MODELS: {
        LIST: `${API_URL}/api/models/`,
        LOAD: `${API_URL}/api/models/load`,
        UNLOAD: `${API_URL}/api/models/unload`,
        CURRENT: `${API_URL}/api/models/current`,
    },
    GENERATION: {
        STREAM_WS: `${WS_BASE_URL}/api/generate/ws`,
        CACHE_SAVE: `${API_URL}/api/generate/cache/save`,
        CACHE_LOAD: `${API_URL}/api/generate/cache/load`,
        CACHE_TRIM: `${API_URL}/api/generate/cache/trim`,
    },
    PERFORMANCE: {
        STATS: `${API_URL}/api/performance/stats`,
        STREAM_WS: `${WS_BASE_URL}/api/performance/ws`,
    },
    CONFIG: {
        GET: `${API_URL}/api/config/`,
        UPDATE: `${API_URL}/api/config/`,
    }
};