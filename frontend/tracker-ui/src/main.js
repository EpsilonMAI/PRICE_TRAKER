import './style.css'
import 'flowbite';
import Alpine from 'alpinejs'
import { api } from './api.js'

// Глобальная функция для Alpine компонента
window.trackingApp = function() {
    return {
        products: [],
        loading: true,
        error: null,
        
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
        }
    }
}

window.Alpine = Alpine
Alpine.start()