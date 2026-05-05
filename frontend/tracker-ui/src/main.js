import './style.css'
import 'flowbite';
import ApexCharts from 'apexcharts';
import Alpine from 'alpinejs'
import { api } from './api.js'

window.addEventListener('load', () => {
    document.body?.setAttribute('data-app-ready', 'true');
});

const sparklineSize = {
    width: 320,
    height: 88,
    padding: { top: 6, right: 0, bottom: 6, left: 0 },
};

const historyPeriodOptions = ['1', '7', '30', 'all'];
const latestFeedVisibleCount = 3;
const storeThemes = {
    wildberries: {
        badgeClass: 'border-fuchsia-200 bg-fuchsia-50 text-fuchsia-700',
        sourceCardClass: 'border-fuchsia-200 bg-fuchsia-50 text-fuchsia-700 hover:border-fuchsia-300 hover:text-fuchsia-800',
        sourceLabelClass: 'text-fuchsia-400',
    },
    ozon: {
        badgeClass: 'border-sky-200 bg-sky-50 text-sky-700',
        sourceCardClass: 'border-sky-200 bg-sky-50 text-sky-700 hover:border-sky-300 hover:text-sky-800',
        sourceLabelClass: 'text-sky-400',
    },
    'яндекс маркет': {
        badgeClass: 'border-amber-200 bg-amber-50 text-amber-700',
        sourceCardClass: 'border-amber-200 bg-amber-50 text-amber-700 hover:border-amber-300 hover:text-amber-800',
        sourceLabelClass: 'text-amber-500',
    },
    'yandex market': {
        badgeClass: 'border-amber-200 bg-amber-50 text-amber-700',
        sourceCardClass: 'border-amber-200 bg-amber-50 text-amber-700 hover:border-amber-300 hover:text-amber-800',
        sourceLabelClass: 'text-amber-500',
    },
    default: {
        badgeClass: 'border-slate-200 bg-white text-slate-500',
        sourceCardClass: 'border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:text-blue-700',
        sourceLabelClass: 'text-slate-400',
    },
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

    if (coordinates.length === 1) {
        const pad = typeof padding === 'number'
            ? { top: padding, right: padding, bottom: padding, left: padding }
            : padding;
        const y = coordinates[0].y;
        return `M ${pad.left} ${y} L ${width - pad.right} ${y}`;
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

    if (coordinates.length === 1) {
        const y = coordinates[0].y;
        return `M ${pad.left} ${y} L ${width - pad.right} ${y} L ${width - pad.right} ${baseline} L ${pad.left} ${baseline} Z`;
    }

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

function aggregateHistoryPoints(points, bucketType) {
    if (bucketType === 'raw') {
        return points;
    }

    const buckets = new Map();

    for (const point of points) {
        const date = new Date(point.collected_at);
        const key = bucketType === 'day'
            ? `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`
            : `${date.getFullYear()}-${date.getMonth()}-${Math.floor(date.getDate() / 7)}`;

        const bucket = buckets.get(key) || {
            prices: [],
            in_stock: point.in_stock,
            collected_at: point.collected_at,
        };

        bucket.prices.push(point.price);
        bucket.in_stock = point.in_stock;
        bucket.collected_at = point.collected_at;
        buckets.set(key, bucket);
    }

    return [...buckets.values()].map((bucket) => ({
        price: bucket.prices.reduce((sum, price) => sum + price, 0) / bucket.prices.length,
        in_stock: bucket.in_stock,
        collected_at: bucket.collected_at,
    }));
}

function getDistinctDayCount(points) {
    return new Set(
        points.map((point) => {
            const date = new Date(point.collected_at);
            return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
        })
    ).size;
}

const trackingStatusMeta = {
    success: {
        label: 'Цена получена',
        className: 'bg-emerald-100 text-emerald-700',
    },
    parser_error: {
        label: 'Ошибка парсинга',
        className: 'bg-rose-100 text-rose-700',
    },
    not_found: {
        label: 'Товар не найден',
        className: 'bg-amber-100 text-amber-700',
    },
    unsupported_store: {
        label: 'Магазин не поддержан',
        className: 'bg-slate-100 text-slate-600',
    },
    store_inactive: {
        label: 'Магазин выключен',
        className: 'bg-slate-100 text-slate-600',
    },
    parser_disabled: {
        label: 'Парсер выключен',
        className: 'bg-slate-100 text-slate-600',
    },
    store_missing: {
        label: 'Магазин не указан',
        className: 'bg-slate-100 text-slate-600',
    },
};

// Компонент списка товаров
window.trackingApp = function() {
    return {
        products: [],
        filters: {
            store: '',
            isActive: 'all',
            search: '',
            ordering: '-price_updated_at',
        },
        availableStores: [],
        listRequestKey: 0,
        loading: true,
        showLoader: false,
        loadingTimer: null,
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
        deleteModalOpen: false,
        deleteLoading: false,
        deleteError: null,
        productPendingDelete: null,
        
        init() {
            // Проверить авторизацию
            if (!localStorage.getItem('access_token')) {
                window.location.href = '/login.html';
                return;
            }
        },

        resetAddModalState() {
            this.newProduct = { productName: '', storeName: '', price: '', customName: '' };
            this.addLoading = false;
            this.addError = null;
            this.wbUrl = '';
            this.wbLoading = false;
            this.wbResult = null;
            this.wbError = null;
            this.addTab = 'manual';
        },

        openAddModal() {
            this.resetAddModalState();
            this.showAddModal = true;
        },

        getProductLink(productId) {
            return `/product.html?id=${productId}`;
        },

        getProductTitle(product) {
            return product?.custom_name || product?.product_name || 'товар';
        },

        openProductCard(productId) {
            window.location.href = this.getProductLink(productId);
        },

        getStoreTheme(storeName) {
            const normalizedStoreName = (storeName || '').trim().toLowerCase();
            return storeThemes[normalizedStoreName] || storeThemes.default;
        },

        getStoreBadgeClass(product) {
            return this.getStoreTheme(product?.store_name).badgeClass;
        },

        getProductQueryParams() {
            const params = {
                ordering: this.filters.ordering,
            };

            if (this.filters.store) {
                params.store = this.filters.store;
            }

            if (this.filters.isActive !== 'all') {
                params.is_active = this.filters.isActive === 'active' ? 'true' : 'false';
            }

            const search = this.filters.search.trim();
            if (search) {
                params.search = search;
            }

            return params;
        },

        syncStoreOptions(products = []) {
            const storeNames = new Set(this.availableStores);

            products.forEach((product) => {
                if (product.store_name) {
                    storeNames.add(product.store_name);
                }
            });

            this.availableStores = [...storeNames].sort((a, b) => a.localeCompare(b, 'ru'));
        },

        hasActiveFilters() {
            return Boolean(
                this.filters.store ||
                this.filters.search.trim() ||
                this.filters.isActive !== 'all'
            );
        },

        resetProductFilters() {
            this.filters = {
                store: '',
                isActive: 'all',
                search: '',
                ordering: '-price_updated_at',
            };
            this.loadProducts();
        },

        getProductListSummary() {
            const count = this.products.length;
            const productWord = this.getProductCountWord(count);

            if (this.hasActiveFilters()) {
                return `Найдено ${count} ${productWord}`;
            }

            return `${count} ${productWord} в отслеживании`;
        },

        getProductCountWord(count) {
            const absCount = Math.abs(count) % 100;
            const lastDigit = absCount % 10;

            if (absCount > 10 && absCount < 20) {
                return 'товаров';
            }

            if (lastDigit === 1) {
                return 'товар';
            }

            if (lastDigit >= 2 && lastDigit <= 4) {
                return 'товара';
            }

            return 'товаров';
        },

        closeAddModal() {
            this.showAddModal = false;
            this.resetAddModalState();
        },

        openDeleteConfirm(product) {
            this.productPendingDelete = product;
            this.deleteError = null;
            this.deleteModalOpen = true;
        },

        closeDeleteConfirm() {
            if (this.deleteLoading) {
                return;
            }

            this.deleteModalOpen = false;
            this.deleteError = null;
            this.productPendingDelete = null;
        },

        startPageLoading() {
            this.loading = true;
            this.showLoader = false;
            clearTimeout(this.loadingTimer);
            this.loadingTimer = setTimeout(() => {
                if (this.loading) {
                    this.showLoader = true;
                }
            }, 450);
        },

        stopPageLoading() {
            this.loading = false;
            this.showLoader = false;
            clearTimeout(this.loadingTimer);
            this.loadingTimer = null;
        },
        
        async loadProducts() {
            const requestKey = ++this.listRequestKey;

            try {
                this.startPageLoading();
                this.error = null;
                const products = await api.getProducts(this.getProductQueryParams());

                if (requestKey !== this.listRequestKey) {
                    return;
                }

                this.products = products;
                this.syncStoreOptions(products);
                console.log('Загружено товаров:', this.products);
            } catch (err) {
                if (requestKey !== this.listRequestKey) {
                    return;
                }
                this.error = err.message;
                console.error('Ошибка:', err);
            } finally {
                if (requestKey === this.listRequestKey) {
                    this.stopPageLoading();
                }
            }
        },
        
        async addProduct() {
            this.addError = null;
            this.addLoading = true;
            
            try {
                await api.addProduct(this.newProduct);
                
                // Закрываем модальное окно и сбрасываем форму
                this.closeAddModal();
                
                // Перезагружаем список товаров
                await this.loadProducts();
            } catch (err) {
                this.addError = err.message;
            } finally {
                this.addLoading = false;
            }
        },
        
        async toggleActive(product) {
            const previousValue = product.is_active;
            const nextValue = !previousValue;
            product.is_active = nextValue;

            try {
                const updated = await api.toggleProductActive(product.id, nextValue);
                product.is_active = updated.is_active;

                if (
                    (this.filters.isActive === 'active' && !updated.is_active) ||
                    (this.filters.isActive === 'paused' && updated.is_active)
                ) {
                    this.products = this.products.filter((item) => item.id !== product.id);
                }
            } catch (error) {
                console.error('Failed to toggle active status:', error);
                product.is_active = previousValue;
                this.error = 'Не удалось обновить статус отслеживания';
            }
        },

        async deleteProduct() {
            if (!this.productPendingDelete || this.deleteLoading) {
                return;
            }

            const deletedProductId = this.productPendingDelete.id;
            this.deleteLoading = true;
            this.deleteError = null;

            try {
                await api.deleteTrackingItem(deletedProductId);
                this.products = this.products.filter((product) => product.id !== deletedProductId);
                this.syncStoreOptions(this.products);

                if (this.selectedProduct?.id === deletedProductId) {
                    this.closeHistory();
                }

                this.deleteModalOpen = false;
                this.productPendingDelete = null;
            } catch (error) {
                this.deleteError = error.message;
            } finally {
                this.deleteLoading = false;
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
            return this.getSparklinePoints(product).length >= 1;
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

        formatCardDateTime(dateString) {
            if (!dateString) return '';
            return new Date(dateString).toLocaleString('ru-RU', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
            }).replace('.', '');
        },

        async addByUrl() {
            if (!this.wbUrl) return;
            this.wbLoading = true;
            this.wbResult = null;
            this.wbError = null;
            try {
                await api.parseWBByUrl(this.wbUrl);
                this.closeAddModal();
                await this.loadProducts();
            } catch (err) {
                this.wbError = err.message || 'Не удалось получить данные о товаре';
            } finally {
                this.wbLoading = false;
            }
        }
    }
}

window.productCardApp = function() {
    return {
        itemId: null,
        item: null,
        history: null,
        historyPeriodOptions,
        loading: true,
        showLoader: false,
        loadingTimer: null,
        error: null,
        historyLoading: false,
        historyError: null,
        historyPeriod: '7',
        historyChart: null,
        refreshing: false,
        chartRenderFrame: null,
        itemRequestKey: 0,
        historyRequestKey: 0,

        async init() {
            if (!localStorage.getItem('access_token')) {
                window.location.href = '/login.html';
                return;
            }

            const id = new URLSearchParams(window.location.search).get('id');
            if (!id) {
                window.location.href = '/index.html';
                return;
            }

            this.itemId = id;
            await this.loadItem();
        },

        startPageLoading() {
            this.loading = true;
            this.showLoader = false;
            clearTimeout(this.loadingTimer);
            this.loadingTimer = setTimeout(() => {
                if (this.loading) {
                    this.showLoader = true;
                }
            }, 450);
        },

        stopPageLoading() {
            this.loading = false;
            this.showLoader = false;
            clearTimeout(this.loadingTimer);
            this.loadingTimer = null;
        },

        async loadItem() {
            const requestKey = ++this.itemRequestKey;
            const period = this.historyPeriod;

            try {
                this.startPageLoading();
                this.error = null;
                this.historyError = null;

                const [item, history] = await Promise.all([
                    api.getTrackingItem(this.itemId),
                    api.getProductHistory(this.itemId, period),
                ]);

                if (requestKey !== this.itemRequestKey) {
                    return;
                }

                this.item = item;
                this.history = history;
            } catch (error) {
                if (requestKey !== this.itemRequestKey) {
                    return;
                }
                this.error = error.message;
            } finally {
                if (requestKey === this.itemRequestKey) {
                    this.stopPageLoading();
                }
            }

            if (requestKey === this.itemRequestKey) {
                this.scheduleHistoryChartRender();
            }
        },

        async changeHistoryPeriod(period) {
            if (this.historyPeriod === period) {
                return;
            }

            this.historyPeriod = period;
            this.historyError = null;
            this.destroyHistoryChart();
            await this.loadHistory(period);
        },

        async loadHistory(period = this.historyPeriod) {
            const requestKey = ++this.historyRequestKey;

            try {
                this.historyLoading = true;
                this.historyError = null;
                const history = await api.getProductHistory(this.itemId, period);

                if (requestKey !== this.historyRequestKey || period !== this.historyPeriod) {
                    return;
                }

                this.history = history;
            } catch (error) {
                if (requestKey !== this.historyRequestKey || period !== this.historyPeriod) {
                    return;
                }
                this.historyError = error.message;
                this.destroyHistoryChart();
            } finally {
                if (requestKey === this.historyRequestKey && period === this.historyPeriod) {
                    this.historyLoading = false;
                }
            }

            if (requestKey === this.historyRequestKey && period === this.historyPeriod) {
                this.scheduleHistoryChartRender();
            }
        },

        async refreshProduct() {
            if (this.refreshing) {
                return;
            }

            try {
                this.refreshing = true;
                this.error = null;
                await api.refreshProductPrice(this.itemId);
                await this.loadItem();
            } catch (error) {
                this.error = error.message;
            } finally {
                this.refreshing = false;
            }
        },

        async toggleActive() {
            if (!this.item) {
                return;
            }

            const nextValue = !this.item.is_active;
            this.item.is_active = nextValue;

            try {
                await api.toggleProductActive(this.item.id, nextValue);
            } catch (error) {
                this.item.is_active = !nextValue;
                this.error = error.message;
            }
        },

        getTitle() {
            return this.item?.custom_name || this.item?.product_name || 'Карточка товара';
        },

        getSubtitle() {
            if (!this.item?.custom_name || !this.item?.product_name) {
                return '';
            }

            return this.item.product_name;
        },

        getStatusMeta() {
            return trackingStatusMeta[this.item?.last_status] || {
                label: this.item?.last_status ? this.item.last_status : 'Статус неизвестен',
                className: 'bg-slate-100 text-slate-600',
            };
        },

        getStoreTheme() {
            const storeName = (this.item?.store_name || '').trim().toLowerCase();
            return storeThemes[storeName] || storeThemes.default;
        },

        getSavingsAmount() {
            if (!this.item?.current_price || !this.item?.wb_wallet_price) {
                return null;
            }

            return Number(this.item.current_price) - Number(this.item.wb_wallet_price);
        },

        hasWalletPrice() {
            if (!this.item?.wb_wallet_price || !this.item?.current_price) {
                return false;
            }

            return Number(this.item.wb_wallet_price) < Number(this.item.current_price);
        },

        getHistoryPoints() {
            const points = this.getRawHistoryPoints();

            if (this.historyPeriod === '1') {
                return aggregateHistoryPoints(points, 'raw');
            }

            if (this.historyPeriod === '7' || this.historyPeriod === '30') {
                return aggregateHistoryPoints(points, 'day');
            }

            const dayPoints = aggregateHistoryPoints(points, 'day');
            return dayPoints.length >= 2 ? dayPoints : points;
        },

        getRawHistoryPoints() {
            return normalizeHistoryPoints(this.history?.history_points);
        },

        hasHistory() {
            return this.getHistoryPoints().length >= 2;
        },

        getHistorySeries() {
            return this.getHistoryPoints().map((point) => point.price);
        },

        getTrendMeta() {
            return getTrendColors(this.getHistoryPoints());
        },

        getRecentHistoryPoints() {
            return [...this.getRawHistoryPoints()].reverse();
        },

        destroyHistoryChart() {
            if (this.chartRenderFrame) {
                cancelAnimationFrame(this.chartRenderFrame);
                this.chartRenderFrame = null;
            }
            if (this.historyChart) {
                this.historyChart.destroy();
                this.historyChart = null;
            }
        },

        scheduleHistoryChartRender() {
            this.$nextTick(() => {
                if (this.chartRenderFrame) {
                    cancelAnimationFrame(this.chartRenderFrame);
                }

                this.chartRenderFrame = requestAnimationFrame(() => {
                    this.chartRenderFrame = requestAnimationFrame(() => {
                        this.renderHistoryChart();
                    });
                });
            });
        },

        formatHistoryAxisDate(timestamp) {
            const date = new Date(timestamp);
            if (this.historyPeriod === '1') {
                return new Intl.DateTimeFormat('ru-RU', {
                    hour: '2-digit',
                    minute: '2-digit',
                }).format(date);
            }

            return new Intl.DateTimeFormat('ru-RU', {
                day: '2-digit',
                month: 'short',
            }).format(date);
        },

        getHistoryLabelStep(pointCount) {
            if (pointCount <= 2) {
                return 1;
            }

            if (this.historyPeriod === '1') {
                return 2;
            }

            if (this.historyPeriod === '7') {
                return Math.max(1, Math.ceil(pointCount / 5));
            }

            return Math.max(1, Math.ceil(pointCount / 6));
        },

        getHistoryPeriodLabel(period) {
            if (period === '1') return '1 дн.';
            if (period === '7') return '7 дн.';
            if (period === '30') return '30 дн.';
            return 'Все';
        },

        getHistoryAggregationHint() {
            if (this.historyPeriod === '1') {
                return 'Показываются отдельные замеры внутри последних суток.';
            }

            if (this.historyPeriod === '7' || this.historyPeriod === '30') {
                return 'Каждая точка показывает среднюю цену за день.';
            }

            return 'Для полного периода график агрегируется по дням.';
        },

        getHistoryChartHeight() {
            return 560;
        },

        getLatestFeedMaxHeight() {
            return 318;
        },

        getLatestFeedBadge() {
            return `${Math.min(this.getRecentHistoryPoints().length, latestFeedVisibleCount)} из ${this.getRecentHistoryPoints().length}`;
        },

        getLatestFeedViewportClass() {
            return 'max-h-[318px]';
        },

        renderHistoryChart() {
            this.destroyHistoryChart();

            if (!this.hasHistory() || !this.$refs.productHistoryChart) {
                return;
            }

            const historyPoints = this.getHistoryPoints();
            const trendColors = this.getTrendMeta();
            const prices = historyPoints.map((point) => point.price);
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            const hasRange = maxPrice !== minPrice;
            const pricePadding = hasRange
                ? Math.max((maxPrice - minPrice) * 0.12, 35)
                : Math.max(maxPrice * 0.02, 20);
            const series = this.getHistorySeries();
            const labelStep = this.getHistoryLabelStep(historyPoints.length);
            const categories = historyPoints.map((point, index) => {
                const isEdgePoint = index === 0 || index === historyPoints.length - 1;
                const shouldShowLabel = isEdgePoint || index % labelStep === 0;
                return shouldShowLabel ? this.formatHistoryAxisDate(point.collected_at) : '';
            });

            this.historyChart = new ApexCharts(this.$refs.productHistoryChart, {
                chart: {
                    type: 'area',
                    height: this.getHistoryChartHeight(),
                    toolbar: { show: false },
                    zoom: { enabled: false },
                    animations: { easing: 'easeinout', speed: 380 },
                    fontFamily: 'inherit',
                    parentHeightOffset: 0,
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
                        left: 4,
                        right: 6,
                        top: 0,
                        bottom: -6,
                    },
                },
                xaxis: {
                    type: 'category',
                    categories,
                    labels: {
                        rotate: 0,
                        hideOverlappingLabels: false,
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
                    min: Math.max(0, Math.floor(minPrice - pricePadding)),
                    max: Math.ceil(maxPrice + pricePadding),
                    tickAmount: 4,
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
                            if (!point) {
                                return '';
                            }

                            if (this.historyPeriod === '1') {
                                return this.formatDateTime(point.collected_at);
                            }

                            return new Intl.DateTimeFormat('ru-RU', {
                                day: '2-digit',
                                month: 'long',
                            }).format(new Date(point.collected_at));
                        },
                    },
                    y: {
                        formatter: (value) => `${this.formatPrice(value)} ₽`,
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
            if (!dateString) return '—';
            return new Date(dateString).toLocaleString('ru-RU', {
                day: '2-digit',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit',
            });
        },

        formatCompactDateTime(dateString) {
            if (!dateString) return '—';
            return new Date(dateString).toLocaleString('ru-RU', {
                day: '2-digit',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit',
            }).replace('.', '');
        },

        getSourceHostname() {
            if (!this.item?.source_url) {
                return 'Ссылка не указана';
            }

            try {
                return new URL(this.item.source_url).hostname.replace('www.', '');
            } catch {
                return this.item.source_url;
            }
        },

        getTrackingStateLabel() {
            return this.item?.is_active ? 'Автообновление включено' : 'Автообновление на паузе';
        },

        getTrackingStateDescription() {
            return this.item?.is_active
                ? 'Товар участвует в плановых проверках цены.'
                : 'Фоновые проверки остановлены, но ручное обновление доступно.';
        },
    };
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
                window.location.href = '/index.html';
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
                
                // После регистрации отправляем сразу в каталог товаров
                setTimeout(() => {
                    window.location.href = '/index.html';
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
                window.location.href = '/index.html';
            }
        },
        
        async login() {
            this.error = null;
            this.loading = true;
            
            try {
                const response = await api.login(this.formData);
                localStorage.setItem('access_token', response.access);
                localStorage.setItem('refresh_token', response.refresh);
                window.location.href = '/index.html';
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
        notifications: {
            notify_price_drop: true,
            notify_back_in_stock: true,
            notify_weekly_summary: false,
        },
        notifSaving: false,
        notifSaved: false,
        notifError: null,
        testSending: false,
        testSent: false,
        testError: null,
        editingEmail: false,
        emailInput: '',
        emailSaving: false,
        emailSaved: false,
        emailError: null,

        async loadProfile() {
            if (!localStorage.getItem('access_token')) {
                window.location.href = '/login.html';
                return;
            }

            try {
                this.loading = true;
                this.user = await api.getProfile();
                this.stats = {
                    tracking_count: this.user.tracking_count || 0,
                    active_count: this.user.active_count || 0,
                    total_saved: 0,
                };
                // Загрузить текущие настройки уведомлений
                this.notifications = {
                    notify_price_drop: this.user.notify_price_drop ?? true,
                    notify_back_in_stock: this.user.notify_back_in_stock ?? true,
                    notify_weekly_summary: this.user.notify_weekly_summary ?? false,
                };
            } catch (err) {
                this.error = err.message;
                if (err.message.includes('профиль')) {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login.html';
                }
            } finally {
                this.loading = false;
            }
        },

        async saveNotifications() {
            this.notifSaving = true;
            this.notifSaved = false;
            this.notifError = null;
            try {
                await api.updateNotificationSettings(this.notifications);
                this.notifSaved = true;
                setTimeout(() => { this.notifSaved = false; }, 3000);
            } catch (err) {
                this.notifError = err.message;
            } finally {
                this.notifSaving = false;
            }
        },

        async sendTestNotification() {
            this.testSending = true;
            this.testSent = false;
            this.testError = null;
            this.notifError = null;
            try {
                const result = await api.sendTestNotification();
                this.testSent = true;
                setTimeout(() => { this.testSent = false; }, 4000);
            } catch (err) {
                this.testError = err.message;
            } finally {
                this.testSending = false;
            }
        },

        async saveEmail() {
            this.emailSaving = true;
            this.emailSaved = false;
            this.emailError = null;
            try {
                const result = await api.updateEmail(this.emailInput);
                this.user.email = result.email;
                this.editingEmail = false;
                this.emailSaved = true;
                setTimeout(() => { this.emailSaved = false; }, 3000);
            } catch (err) {
                this.emailError = err.message;
            } finally {
                this.emailSaving = false;
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
                day: 'numeric',
            });
        },
    }
}

window.Alpine = Alpine
Alpine.start()
