import './style.css'
import 'flowbite';
import ApexCharts from 'apexcharts';
import Alpine from 'alpinejs'
import { api } from './api.js'

const sparklineSize = {
    width: 160,
    height: 72,
    padding: { top: 6, right: 2, bottom: 6, left: 2 },
};

function normalizeHistoryPoints(points = []) {
    return points
        .map((point) => ({
            price: Number(point.price),
            collected_at: point.collected_at,
            in_stock: point.in_stock,
        }))
        .filter((point) => Number.isFinite(point.price) && point.collected_at);
}

function buildCoordinates(points, width, height, padding) {
    if (!points.length) {
        return [];
    }

    const pad = typeof padding === 'number'
        ? { top: padding, right: padding, bottom: padding, left: padding }
        : padding;

    const minPrice = Math.min(...points.map((point) => point.price));
    const maxPrice = Math.max(...points.map((point) => point.price));
    const priceRange = maxPrice - minPrice || 1;
    const availableWidth = Math.max(width - pad.left - pad.right, 1);
    const availableHeight = Math.max(height - pad.top - pad.bottom, 1);

    return points.map((point, index) => {
        const x = pad.left + (
            points.length === 1 ? availableWidth / 2 : (availableWidth * index) / (points.length - 1)
        );
        const ratio = (point.price - minPrice) / priceRange;
        const y = pad.top + availableHeight - (ratio * availableHeight);

        return { x, y, ...point };
    });
}

function buildLinePath(points, width, height, padding) {
    const coordinates = buildCoordinates(points, width, height, padding);
    if (!coordinates.length) {
        return '';
    }

    return coordinates.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
}

function buildAreaPath(points, width, height, padding) {
    const coordinates = buildCoordinates(points, width, height, padding);
    if (!coordinates.length) {
        return '';
    }

    const pad = typeof padding === 'number'
        ? { top: padding, right: padding, bottom: padding, left: padding }
        : padding;
    const baseline = height - pad.bottom;
    const line = coordinates.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
    const last = coordinates[coordinates.length - 1];
    const first = coordinates[0];

    return `${line} L ${last.x} ${baseline} L ${first.x} ${baseline} Z`;
}

function getTrendColors(points) {
    if (points.length < 2) {
        return {
            stroke: '#94a3b8',
            fill: 'rgba(148, 163, 184, 0.16)',
            badge: 'bg-slate-100 text-slate-600',
        };
    }

    const first = points[0].price;
    const last = points[points.length - 1].price;

    if (last < first) {
        return {
            stroke: '#059669',
            fill: 'rgba(5, 150, 105, 0.16)',
            badge: 'bg-emerald-100 text-emerald-700',
        };
    }

    if (last > first) {
        return {
            stroke: '#dc2626',
            fill: 'rgba(220, 38, 38, 0.14)',
            badge: 'bg-rose-100 text-rose-700',
        };
    }

    return {
        stroke: '#2563eb',
        fill: 'rgba(37, 99, 235, 0.16)',
        badge: 'bg-blue-100 text-blue-700',
    };
}

// Компонент списка товаров
window.trackingApp = function() {
    return {
        products: [],
        loading: true,
        error: null,
        showAddModal: false,
        addTab: 'manual',
        newProduct: {
            productName: '',
            storeName: '',
            price: '',
            customName: ''
        },
        addLoading: false,
        addError: null,
        historyModalOpen: false,
        historyLoading: false,
        historyError: null,
        historyPeriod: '30',
        selectedProduct: null,
        selectedHistory: null,
        historyChart: null,
        wbUrl: '',
        wbLoading: false,
        wbResult: null,
        wbError: null,
        
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
                this.wbUrl = '';
                this.wbResult = null;
                this.wbError = null;
                this.addTab = 'manual';
                
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
                product.is_active = !product.is_active;
                this.error = 'Не удалось обновить статус отслеживания';
            }
        },

        async openHistory(product) {
            this.historyModalOpen = true;
            this.historyLoading = true;
            this.historyError = null;
            this.historyPeriod = '30';
            this.selectedProduct = product;
            this.selectedHistory = null;
            this.destroyHistoryChart();

            await this.loadHistory(product.id, this.historyPeriod);
        },

        closeHistory() {
            this.destroyHistoryChart();
            this.historyModalOpen = false;
            this.historyLoading = false;
            this.historyError = null;
            this.selectedProduct = null;
            this.selectedHistory = null;
        },

        async changeHistoryPeriod(period) {
            if (!this.selectedProduct || this.historyPeriod === period) {
                return;
            }

            this.historyPeriod = period;
            await this.loadHistory(this.selectedProduct.id, period);
        },

        async loadHistory(productId, period) {
            try {
                this.historyLoading = true;
                this.historyError = null;
                this.selectedHistory = await api.getProductHistory(productId, period);
            } catch (error) {
                this.historyError = error.message;
                this.destroyHistoryChart();
            } finally {
                this.historyLoading = false;
            }

            this.$nextTick(() => {
                this.renderHistoryChart();
            });
        },

        getSparklinePoints(product) {
            return normalizeHistoryPoints(product.sparkline_points);
        },

        hasSparkline(product) {
            return this.getSparklinePoints(product).length >= 2;
        },

        getSparklineStroke(product) {
            return getTrendColors(this.getSparklinePoints(product)).stroke;
        },

        getSparklineFill(product) {
            return getTrendColors(this.getSparklinePoints(product)).fill;
        },

        getSparklineBadgeClass(product) {
            return getTrendColors(this.getSparklinePoints(product)).badge;
        },

        buildSparklinePath(product) {
            return buildLinePath(this.getSparklinePoints(product), sparklineSize.width, sparklineSize.height, sparklineSize.padding);
        },

        buildSparklineAreaPath(product) {
            return buildAreaPath(this.getSparklinePoints(product), sparklineSize.width, sparklineSize.height, sparklineSize.padding);
        },

        getDetailedHistoryPoints() {
            return normalizeHistoryPoints(this.selectedHistory?.history_points);
        },

        hasDetailedHistory() {
            return this.getDetailedHistoryPoints().length >= 2;
        },

        getDetailedStroke() {
            return getTrendColors(this.getDetailedHistoryPoints()).stroke;
        },

        getDetailedFill() {
            return getTrendColors(this.getDetailedHistoryPoints()).fill;
        },

        getDetailedBadgeClass() {
            return getTrendColors(this.getDetailedHistoryPoints()).badge;
        },

        getRecentHistoryPoints() {
            return [...this.getDetailedHistoryPoints()].slice(-5).reverse();
        },

        destroyHistoryChart() {
            if (this.historyChart) {
                this.historyChart.destroy();
                this.historyChart = null;
            }
        },

        renderHistoryChart() {
            this.destroyHistoryChart();

            if (!this.hasDetailedHistory() || !this.$refs.historyChart) {
                return;
            }

            const historyPoints = this.getDetailedHistoryPoints();
            const trendColors = getTrendColors(historyPoints);
            const prices = historyPoints.map((point) => point.price);
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            const pricePadding = Math.max((maxPrice - minPrice) * 0.06, 120);
            const categories = historyPoints.map((point) => this.formatShortDate(point.collected_at));
            const series = historyPoints.map((point) => point.price);

            this.historyChart = new ApexCharts(this.$refs.historyChart, {
                chart: {
                    type: 'area',
                    height: 420,
                    toolbar: { show: false },
                    zoom: { enabled: false },
                    animations: { easing: 'easeinout', speed: 380 },
                    fontFamily: 'inherit',
                    parentHeightOffset: 0,
                    offsetY: 0,
                },
                series: [{
                    name: 'Цена',
                    data: series,
                }],
                colors: [trendColors.stroke],
                stroke: {
                    curve: 'straight',
                    width: 3,
                },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.24,
                        opacityTo: 0.04,
                        stops: [0, 95, 100],
                    },
                },
                markers: {
                    size: 4,
                    strokeWidth: 3,
                    strokeColors: '#ffffff',
                    hover: {
                        size: 6,
                    },
                },
                dataLabels: {
                    enabled: false,
                },
                grid: {
                    borderColor: '#dbeafe',
                    strokeDashArray: 5,
                    padding: {
                        left: 10,
                        right: 12,
                        top: 4,
                        bottom: -10,
                    },
                },
                xaxis: {
                    type: 'category',
                    categories,
                    tickPlacement: 'on',
                    labels: {
                        rotate: 0,
                        hideOverlappingLabels: false,
                        minHeight: 42,
                        maxHeight: 42,
                        style: {
                            colors: '#94a3b8',
                            fontSize: '12px',
                        },
                    },
                    axisBorder: {
                        show: false,
                    },
                    axisTicks: {
                        show: false,
                    },
                    tooltip: {
                        enabled: false,
                    },
                },
                yaxis: {
                    opposite: true,
                    min: Math.max(0, Math.floor((minPrice - pricePadding) / 100) * 100),
                    max: Math.ceil((maxPrice + pricePadding) / 100) * 100,
                    tickAmount: 3,
                    forceNiceScale: false,
                    labels: {
                        style: {
                            colors: '#94a3b8',
                            fontSize: '12px',
                        },
                        formatter: (value) => `${this.formatPrice(value)} ₽`,
                    },
                },
                tooltip: {
                    shared: false,
                    intersect: true,
                    x: {
                        formatter: (_value, { dataPointIndex }) => {
                            const point = historyPoints[dataPointIndex];
                            return point ? this.formatDateTime(point.collected_at) : '';
                        },
                    },
                    y: {
                        formatter: (value) => `${this.formatPrice(value)} ₽`,
                    },
                },
                noData: {
                    text: 'Недостаточно данных',
                    align: 'center',
                    verticalAlign: 'middle',
                    style: {
                        color: '#94a3b8',
                    },
                },
            });

            this.historyChart.render();
        },

        formatPrice(value) {
            if (value === null || value === undefined || value === '') {
                return '—';
            }

            return new Intl.NumberFormat('ru-RU', {
                maximumFractionDigits: 2,
            }).format(Number(value));
        },

        formatShortDate(dateString) {
            if (!dateString) return '';
            return new Date(dateString).toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: 'short',
            });
        },

        formatDateTime(dateString) {
            if (!dateString) return '';
            return new Date(dateString).toLocaleString('ru-RU', {
                day: '2-digit',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit',
            });
        },

        async addByUrl() {
            if (!this.wbUrl) return;
            this.wbLoading = true;
            this.wbResult = null;
            this.wbError = null;
            try {
                this.wbResult = await api.parseWBByUrl(this.wbUrl);
                await this.loadProducts();
            } catch (err) {
                this.wbError = err.message || 'Не удалось получить данные о товаре';
            } finally {
                this.wbLoading = false;
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
