// Vite прокидывает адрес backend через env, а локальный запуск сохраняет прежний fallback.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';
let refreshRequest = null;

function clearAuthAndRedirect() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login.html';
}

async function refreshAccessToken() {
  if (refreshRequest) {
    return refreshRequest;
  }

  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) {
    clearAuthAndRedirect();
    return null;
  }

  refreshRequest = fetch(`${API_BASE_URL}/token/refresh/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh }),
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error('refresh_failed');
      }

      const payload = await response.json();
      if (!payload.access) {
        throw new Error('refresh_failed');
      }

      localStorage.setItem('access_token', payload.access);
      return payload.access;
    })
    .catch(() => {
      clearAuthAndRedirect();
      return null;
    })
    .finally(() => {
      refreshRequest = null;
    });

  return refreshRequest;
}

async function authenticatedFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = localStorage.getItem('access_token');

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status !== 401) {
    return response;
  }

  const refreshedToken = await refreshAccessToken();
  if (!refreshedToken) {
    return response;
  }

  const retryHeaders = new Headers(options.headers || {});
  retryHeaders.set('Authorization', `Bearer ${refreshedToken}`);

  response = await fetch(url, {
    ...options,
    headers: retryHeaders,
  });

  if (response.status === 401) {
    clearAuthAndRedirect();
  }

  return response;
}

export const api = {
  // Получить все продукты
  async getProducts(params = {}) {
    const query = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.set(key, value);
      }
    });

    const url = `${API_BASE_URL}/detailedprod/${query.toString() ? `?${query}` : ''}`;
    const response = await authenticatedFetch(url);
    if (response.status === 401) return [];
    if (!response.ok) throw new Error('Failed to fetch products');
    return response.json();
  },

  async getProductHistory(productId, period = '7') {
    const response = await authenticatedFetch(`${API_BASE_URL}/tracking/${productId}/history/?period=${period}`);
    if (response.status === 401) return null;
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.period || 'Не удалось загрузить историю цен');
    }
    return response.json();
  },

  async getTrackingItem(productId) {
    const response = await authenticatedFetch(`${API_BASE_URL}/tracking/${productId}/`);
    if (response.status === 401) return null;
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось загрузить карточку товара');
    }
    return response.json();
  },

  async deleteTrackingItem(productId) {
    const response = await authenticatedFetch(`${API_BASE_URL}/tracking/${productId}/`, {
      method: 'DELETE',
    });
    if (response.status === 401) return null;
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось удалить товар из отслеживания');
    }
    return true;
  },

  // Регистрация
  async register(userData) {
    const response = await fetch(`${API_BASE_URL}/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Ошибка регистрации');
    }
    return response.json();
  },

  // Логин
  async login(credentials) {
    const response = await fetch(`${API_BASE_URL}/token/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });
    if (!response.ok) {
      throw new Error('Неверное имя пользователя или пароль');
    }
    return response.json();
  },

  // Получить профиль пользователя
  async getProfile() {
    const response = await authenticatedFetch(`${API_BASE_URL}/profile/`);
    if (response.status === 401) return null;
    if (!response.ok) throw new Error('Не удалось загрузить профиль');
    return response.json();
  },

  // Добавить товар в отслеживание
  async addProduct(productData) {
    const response = await authenticatedFetch(`${API_BASE_URL}/additem/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(productData),
    });
    if (response.status === 401) return null;
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка добавления товара');
    }
    return response.json();
  },

  // Поиск и добавление товара через WB парсер
  async parseWB(query) {
    const response = await authenticatedFetch(`${API_BASE_URL}/parser/wb/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });
    if (response.status === 401) return null;
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Товар не найден на Wildberries');
    }
    return response.json();
  },

  // Добавить товар по прямой ссылке WB
  async parseWBByUrl(url) {
    const response = await authenticatedFetch(`${API_BASE_URL}/parser/wb/url/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }),
    });
    if (response.status === 401) return null;
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Не удалось получить данные о товаре');
    }
    return response.json();
  },

  // Переключить активное отслеживание товара
  async toggleProductActive(productId, isActive) {
    const response = await authenticatedFetch(`${API_BASE_URL}/tracking/${productId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ is_active: isActive }),
    });
    if (response.status === 401) return null;
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка обновления статуса');
    }
    return response.json();
  },

  async refreshProductPrice(productId) {
    const response = await authenticatedFetch(`${API_BASE_URL}/tracking/${productId}/refresh/`, {
      method: 'POST',
    });
    if (response.status === 401) return null;
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || error.detail || 'Не удалось обновить цену');
    }
    return response.json();
  },
};
