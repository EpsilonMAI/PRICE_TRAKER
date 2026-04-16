// Vite прокидывает адрес backend через env, а локальный запуск сохраняет прежний fallback.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export const api = {
  // Получить все продукты
  async getProducts() {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/detailedprod/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error('Failed to fetch products');
    return response.json();
  },

  async getProductHistory(productId, period = '30') {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/tracking/${productId}/history/?period=${period}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.period || 'Не удалось загрузить историю цен');
    }
    return response.json();
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
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/profile/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error('Не удалось загрузить профиль');
    return response.json();
  },

  // Добавить товар в отслеживание
  async addProduct(productData) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/additem/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(productData),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка добавления товара');
    }
    return response.json();
  },

  // Поиск и добавление товара через WB парсер
  async parseWB(query) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/parser/wb/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ query }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Товар не найден на Wildberries');
    }
    return response.json();
  },

  // Добавить товар по прямой ссылке WB
  async parseWBByUrl(url) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/parser/wb/url/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ url }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Не удалось получить данные о товаре');
    }
    return response.json();
  },

  // Переключить активное отслеживание товара
  async toggleProductActive(productId, isActive) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/tracking/${productId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ is_active: isActive }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Ошибка обновления статуса');
    }
    return response.json();
  },
};
