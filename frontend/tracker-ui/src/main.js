import './style.css'
import 'flowbite';
import Alpine from 'alpinejs'
import { api } from './api.js'

// Компонент списка товаров
window.trackingApp = function() {
    return {
        products: [],
        loading: true,
        error: null,
        showAddModal: false,
        newProduct: {
            productName: '',
            storeName: '',
            price: '',
            customName: ''
        },
        addLoading: false,
        addError: null,
        
        init() {
            // Проверить авторизацию
            if (!localStorage.getItem('access_token')) {
                window.location.href = '/login.html';
                return;
            }
        },
        
        async loadProducts() {
            try {
                this.loading = true;
                this.products = await api.getProducts();
                console.log('Загружено товаров:', this.products);
            } catch (err) {
                this.error = err.message;
                console.error('Ошибка:', err);
            } finally {
                this.loading = false;
            }
        },
        
        async addProduct() {
            this.addError = null;
            this.addLoading = true;
            
            try {
                await api.addProduct(this.newProduct);
                
                // Закрываем модальное окно и сбрасываем форму
                this.showAddModal = false;
                this.newProduct = { productName: '', storeName: '', price: '', customName: '' };
                
                // Перезагружаем список товаров
                await this.loadProducts();
            } catch (err) {
                this.addError = err.message;
            } finally {
                this.addLoading = false;
            }
        },
        
        async toggleActive(product) {
            try {
                const updated = await api.toggleProductActive(product.id, !product.is_active);
                product.is_active = updated.is_active;
            } catch (error) {
                console.error('Failed to toggle active status:', error);
                // Откатываем чекбокс назад при ошибке
                product.is_active = !product.is_active;
                this.error = 'Не удалось обновить статус отслеживания';
            }
        }
    }
}

// Компонент регистрации
window.registerApp = function() {
    return {
        formData: {
            username: '',
            email: '',
            password: ''
        },
        loading: false,
        error: null,
        success: false,
        
        init() {
            // Перенаправить если уже залогинен
            if (localStorage.getItem('access_token')) {
                window.location.href = '/profile.html';
            }
        },
        
        async register() {
            this.error = null;
            this.loading = true;
            
            try {
                const response = await api.register(this.formData);
                this.success = true;
                
                // Сохраняем токены из ответа регистрации
                localStorage.setItem('access_token', response.tokens.access);
                localStorage.setItem('refresh_token', response.tokens.refresh);
                
                // Перенаправляем в профиль
                setTimeout(() => {
                    window.location.href = '/profile.html';
                }, 1500);
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        }
    }
}

// Компонент входа
window.loginApp = function() {
    return {
        formData: {
            username: '',
            password: ''
        },
        loading: false,
        error: null,
        
        init() {
            // Перенаправить если уже залогинен
            if (localStorage.getItem('access_token')) {
                window.location.href = '/profile.html';
            }
        },
        
        async login() {
            this.error = null;
            this.loading = true;
            
            try {
                const response = await api.login(this.formData);
                localStorage.setItem('access_token', response.access);
                localStorage.setItem('refresh_token', response.refresh);
                window.location.href = '/profile.html';
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        }
    }
}

// Компонент профиля
window.profileApp = function() {
    return {
        user: {},
        stats: {},
        loading: true,
        error: null,
        
        async loadProfile() {
            // Проверить авторизацию
            if (!localStorage.getItem('access_token')) {
                window.location.href = '/login.html';
                return;
            }
            
            try {
                this.loading = true;
                this.user = await api.getProfile();
                // Статистика приходит с бэкенда
                this.stats = {
                    tracking_count: this.user.tracking_count || 0,
                    active_count: this.user.active_count || 0,
                    total_saved: 0  // Это поле можно будет добавить позже
                };
            } catch (err) {
                this.error = err.message;
                if (err.message.includes('профиль')) {
                    // Токен истёк, перенаправить на логин
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login.html';
                }
            } finally {
                this.loading = false;
            }
        },
        
        logout() {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login.html';
        },
        
        formatDate(dateString) {
            if (!dateString) return '';
            return new Date(dateString).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }
    }
}

window.Alpine = Alpine
Alpine.start()