from rest_framework import generics
from .models import Categories, Products
from .serializers import ProductsSerializer


class ProductsAPIList(generics.ListAPIView):
    queryset = Products.objects.all()
    serializer_class = ProductsSerializer

class ProductsAPIUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset = Products.objects.all()
    serializer_class = ProductsSerializer

class ProductsAPICreate(generics.CreateAPIView):
    queryset = Products.objects.all()
    serializer_class = ProductsSerializer
