// API конфигурация для подключения к Django backend
const API_BASE_URL = 'http://127.0.0.1:8000/api/products/';

export const api = {
  // Получить все продукты
  async getProducts() {
    const response = await fetch(`${API_BASE_URL}/products/`);
    if (!response.ok) throw new Error('Failed to fetch products');
    return response.json();
  },
  

//   // Получить один продукт
//   async getProduct(id) {
//     const response = await fetch(`${API_BASE_URL}/products/${id}/`);
//     if (!response.ok) throw new Error('Failed to fetch product');
//     return response.json();
//   },

  // Создать продукт
  async createProduct(data) {
    const response = await fetch(`${API_BASE_URL}/products/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create product');
    return response.json();
  },

//   // Регистрация
//   async register(userData) {
//     const response = await fetch(`${API_BASE_URL}/auth/register/`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(userData),
//     });
//     if (!response.ok) throw new Error('Registration failed');
//     return response.json();
//   },

//   // Логин
//   async login(credentials) {
//     const response = await fetch(`${API_BASE_URL}/auth/login/`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify(credentials),
//     });
//     if (!response.ok) throw new Error('Login failed');
//     return response.json();
//   },
// };
}
