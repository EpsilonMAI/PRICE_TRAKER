"""
URL configuration for price_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from items.views import ProductsAPIList, ProductsAPIUpdate, ProductsAPICreate
from tracking.views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from users.views import UserRegistration, GetProfile
from stores.views import WBParserView, WBParserByURLView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/products/', ProductsAPIList.as_view()),
    path('api/products/<int:pk>/', ProductsAPIUpdate.as_view()),
    path('api/products/create/', ProductsAPICreate.as_view()),
    path('api/detailedprod/', TrackingItemsAPIList.as_view()),
    # JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/register/', UserRegistration.as_view()),
    path('api/profile/', GetProfile.as_view()),
    path('api/additem/', AddItemToTrackAPIView.as_view()),
    path('api/tracking/<int:pk>/history/', TrackingItemHistoryAPIView.as_view()),
    path('api/tracking/<int:pk>/refresh/', RefreshTrackingItemAPIView.as_view()),
    path('api/tracking/<int:pk>/', UpdateTrackingItemAPIView.as_view()),
    path('api/parser/wb/', WBParserView.as_view(), name='parser_wb'),
    path('api/parser/wb/url/', WBParserByURLView.as_view(), name='parser_wb_url'),
]
