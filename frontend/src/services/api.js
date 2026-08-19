// src/services/api.js
//
// Centralized API client. All backend calls go through here (spec section 51)
// instead of scattered fetch() calls in components. Handles:
//  - attaching the access token to every authenticated request
//  - transparently refreshing an expired access token once and retrying
//  - normalizing the backend's { error: { code, message } } shape into a JS Error
//
// The backend URL is read from an env var (spec section 52), never hard-coded.
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

const ACCESS_TOKEN_KEY = 'crux_access_token';
const REFRESH_TOKEN_KEY = 'crux_refresh_token';

// --- Token storage -----------------------------------------------------

export function getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens({ access_token, refresh_token }) {
    if (access_token) localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    if (refresh_token) localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
}

export function clearTokens() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// --- Core request helper ------------------------------------------------

class ApiError extends Error {
    constructor(code, message, status) {
        super(message);
        this.code = code;
        this.status = status;
    }
}

async function parseErrorResponse(response) {
    try {
        const body = await response.json();
        if (body?.error?.code) {
            return new ApiError(body.error.code, body.error.message || 'Something went wrong.', response.status);
        }
        return new ApiError('UNKNOWN_ERROR', body?.detail || 'Something went wrong.', response.status);
    } catch {
        return new ApiError('UNKNOWN_ERROR', 'Something went wrong.', response.status);
    }
}

let refreshPromise = null;

async function refreshAccessToken() {
    // Coalesce concurrent 401s into a single refresh call.
    if (!refreshPromise) {
        refreshPromise = (async () => {
            const refresh_token = getRefreshToken();
            if (!refresh_token) throw new ApiError('UNAUTHORIZED', 'No refresh token available.', 401);

            const response = await fetch(`${API_BASE}/api/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token }),
            });

            if (!response.ok) {
                clearTokens();
                throw await parseErrorResponse(response);
            }

            const tokens = await response.json();
            setTokens(tokens);
            return tokens.access_token;
        })().finally(() => {
            refreshPromise = null;
        });
    }
    return refreshPromise;
}

/**
 * @param {string} path - e.g. '/api/chat'
 * @param {object} options - fetch options; body may be a plain object (auto JSON-encoded) or FormData
 * @param {boolean} auth - attach Authorization header (default true)
 */
async function request(path, options = {}, auth = true) {
    const { body, headers = {}, ...rest } = options;
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

    const finalHeaders = { ...headers };
    if (!isFormData && body !== undefined) {
        finalHeaders['Content-Type'] = 'application/json';
    }
    if (auth) {
        const token = getAccessToken();
        if (token) finalHeaders['Authorization'] = `Bearer ${token}`;
    }

    const doFetch = async () =>
        fetch(`${API_BASE}${path}`, {
            ...rest,
            headers: finalHeaders,
            body: isFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
        });

    let response = await doFetch();

    // One transparent retry after refreshing an expired access token.
    if (response.status === 401 && auth && getRefreshToken()) {
        try {
            const newToken = await refreshAccessToken();
            finalHeaders['Authorization'] = `Bearer ${newToken}`;
            response = await fetch(`${API_BASE}${path}`, {
                ...rest,
                headers: finalHeaders,
                body: isFormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
            });
        } catch {
            // fall through - the original 401 response will be reported below
        }
    }

    if (!response.ok) {
        throw await parseErrorResponse(response);
    }
    if (response.status === 204) return null;
    return response.json();
}

// --- Auth ----------------------------------------------------------------

export async function register(payload) {
    const tokens = await request('/api/auth/register', { method: 'POST', body: payload }, false);
    setTokens(tokens);
    return tokens;
}

export async function login({ email, password }) {
    const tokens = await request('/api/auth/login', { method: 'POST', body: { email, password } }, false);
    setTokens(tokens);
    return tokens;
}

export async function logout() {
    try {
        await request('/api/auth/logout', { method: 'POST' });
    } catch {
        // ignore - we clear local tokens regardless
    } finally {
        clearTokens();
    }
}

export async function getCurrentUser() {
    return request('/api/auth/me', { method: 'GET' });
}

export async function updateProfile(profile) {
    return request('/api/users/me', { method: 'PATCH', body: profile });
}

// --- Documents -------------------------------------------------------------

export async function uploadDocument(file, conversationId) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('conversation_id', conversationId);
    return request('/api/documents/upload', { method: 'POST', body: formData });
}

export async function getDocuments() {
    return request('/api/documents', { method: 'GET' });
}

export async function getDocument(documentId) {
    return request(`/api/documents/${documentId}`, { method: 'GET' });
}

export async function deleteDocument(documentId) {
    return request(`/api/documents/${documentId}`, { method: 'DELETE' });
}

export async function getStorageUsage(conversationId) {
    const query = conversationId ? `?conversation_id=${encodeURIComponent(conversationId)}` : '';
    return request(`/api/documents/storage${query}`, { method: 'GET' });
}

// --- Chat / Conversations ---------------------------------------------------

export async function sendMessage({ message, conversationId, documentIds = [], action = 'general' }) {
    return request('/api/chat', {
        method: 'POST',
        body: { message, conversation_id: conversationId ?? null, document_ids: documentIds, action },
    });
}

export async function createConversation(title = null) {
    return request('/api/conversations', {
        method: 'POST',
        body: title === null ? {} : { title },
    });
}

export async function getConversations() {
    return request('/api/conversations', { method: 'GET' });
}

export async function getConversation(conversationId) {
    return request(`/api/conversations/${conversationId}`, { method: 'GET' });
}

export async function deleteConversation(conversationId) {
    return request(`/api/conversations/${conversationId}`, { method: 'DELETE' });
}

// --- Feedback / Suggestions ---------------------------------------------------

export async function submitFeedback(messageId, feedback, reason) {
    return request(`/api/messages/${messageId}/feedback`, { method: 'POST', body: { feedback, reason } });
}

export async function submitSuggestion({ email, organization, contact, suggestion }) {
    // Works whether or not the user is logged in - request() attaches the
    // token automatically if one exists, and the backend prefers account
    // details over form fields for authenticated submissions.
    return request('/api/suggestions', { method: 'POST', body: { email, organization, contact, suggestion } });
}

// --- Admin ---------------------------------------------------------------

export async function getAdminStats() {
    return request('/api/admin/stats', { method: 'GET' });
}

export { ApiError };
