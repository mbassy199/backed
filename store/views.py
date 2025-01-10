# Django Packages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.db import transaction
from django.urls import reverse
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string

from rest_framework.pagination import PageNumberPagination

class ProductPagination(PageNumberPagination):
    page_size = 10  # The default number of items per page
    page_size_query_param = 'page_size'  # Allow the user to specify a different page size via query parameters
    max_page_size = 100  # Maximum number of items per page to avoid performance issues


# Restframework Packages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework import status

# Serializers
from userauths.serializer import MyTokenObtainPairSerializer, RegisterSerializer
from store.serializers import CancelledOrderSerializer, CartSerializer, CartOrderItemSerializer, ProductSerializer, TagSerializer ,CategorySerializer, DeliveryCouriersSerializer, CartOrderSerializer, GallerySerializer, BrandSerializer, ProductFaqSerializer, ReviewSerializer,  SpecificationSerializer, ColorSerializer, SizeSerializer, AddressSerializer, WishlistSerializer, ConfigSettingsSerializer

# Models
from userauths.models import User
from store.models import CancelledOrder, CartOrderItem, Cart, Notification, Product, Tag ,Category, DeliveryCouriers, CartOrder, Gallery, Brand, ProductFaq, Review,  Specification, Color, Size, Address, Wishlist
from addon.models import ConfigSettings, Tax
from vendor.models import Vendor

# Others Packages
import json
from decimal import Decimal
import requests



def send_notification(user=None, vendor=None, order=None, order_item=None):
    Notification.objects.create(
        user=user,
        vendor=vendor,
        order=order,
        order_item=order_item,
    )

class ConfigSettingsDetailView(generics.RetrieveAPIView):
    serializer_class = ConfigSettingsSerializer

    def get_object(self):
        # Use the get method to retrieve the first ConfigSettings object
        return ConfigSettings.objects.first()

    permission_classes = (AllowAny,)

class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(active=True)
    permission_classes = (AllowAny,)


class BrandListView(generics.ListAPIView):
    serializer_class = BrandSerializer
    queryset = Brand.objects.filter(active=True)
    permission_classes = (AllowAny,)

class FeaturedProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(status="published", featured=True)[:3]
    permission_classes = (AllowAny,)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)
    pagination_class = ProductPagination  # Apply pagination

    def get_queryset(self):
        # Default query to get all published products
        queryset = Product.objects.filter(status="published")

        # Get the category slug from the query parameters (e.g., ?category=mens-perfume-87gx)
        category_slug = self.request.query_params.get('category', None)

        # If category slug is provided, filter products by that category's slug
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(status="published")
    permission_classes = (AllowAny,)


class ProductPagination(PageNumberPagination):
    page_size = 10  # You can adjust the number of items per page as needed
    page_size_query_param = 'page_size'
    max_page_size = 100    

class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer

    def get_object(self):
        # Retrieve the product using the provided slug from the URL
        slug = self.kwargs.get('slug')
        return Product.objects.get(slug=slug)
    
class CartApiView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Extract payload from request
        payload = request.data

        try:
            # Fetch the product instance
            product = Product.objects.get(id=payload.get('product_id'))

            # Handle optional user association
            user_id = payload.get('user_id')
            user = User.objects.get(id=user_id) if user_id and user_id != 'undefined' else None

            # Prepare data for Cart creation
            cart_data = {
                'product': product.id,
                'quantity': payload.get('qty'),
                'price': payload.get('price'),
                'shipping_amount': payload.get('shipping_amount'),
                'country': payload.get('country'),
                'size': payload.get('size'),  # Fixed key from 'color' to 'size'
                'cart_id': payload.get('cart_id'),
                'user': user.id if user else None
            }

            # Validate and save using the serializer
            serializer = self.get_serializer(data=cart_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except KeyError as e:
            return Response({"error": f"Missing field: {e.args[0]}"}, status=status.HTTP_400_BAD_REQUEST)

   

class CartListView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        user_id = self.kwargs.get('user_id')  # Use get() method to handle the case where user_id is not present

        
        if user_id is not None:
            user = User.objects.get(id=user_id)
            queryset = Cart.objects.filter(Q(user=user, cart_id=cart_id) | Q(user=user))
        else:
            queryset = Cart.objects.filter(cart_id=cart_id)
        
        return queryset
    

class CartTotalView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        user_id = self.kwargs.get('user_id')  # Use get() method to handle the case where user_id is not present

        
        if user_id is not None:
            user = User.objects.get(id=user_id)
            queryset = Cart.objects.filter(cart_id=cart_id, user=user)
        else:
            queryset = Cart.objects.filter(cart_id=cart_id)
        
        return queryset
    

class CartDetailView(generics.RetrieveAPIView):
    # Define the serializer class for the view
    serializer_class = CartSerializer
    # Specify the lookup field for retrieving objects using 'cart_id'
    lookup_field = 'cart_id'

    # Add a permission class for the view
    permission_classes = (AllowAny,)


    def get_queryset(self):
        # Get 'cart_id' and 'user_id' from the URL kwargs
        cart_id = self.kwargs['cart_id']
        user_id = self.kwargs.get('user_id')  # Use get() to handle cases where 'user_id' is not present

        if user_id is not None:
            # If 'user_id' is provided, filter the queryset by both 'cart_id' and 'user_id'
            user = User.objects.get(id=user_id)
            queryset = Cart.objects.filter(cart_id=cart_id, user=user)
        else:
            # If 'user_id' is not provided, filter the queryset by 'cart_id' only
            queryset = Cart.objects.filter(cart_id=cart_id)

        return queryset

    def get(self, request, *args, **kwargs):
        # Get the queryset of cart items based on 'cart_id' and 'user_id' (if provided)
        queryset = self.get_queryset()

        # Initialize sums for various cart item attributes
        total_shipping = 0.0
        total_tax = 0.0
        total_service_fee = 0.0
        total_sub_total = 0.0
        total_total = 0.0

        # Iterate over the queryset of cart items to calculate cumulative sums
        for cart_item in queryset:
            # Calculate the cumulative shipping, tax, service_fee, and total values
            total_shipping += float(self.calculate_shipping(cart_item))
            total_tax += float(self.calculate_tax(cart_item))
            total_service_fee += float(self.calculate_service_fee(cart_item))
            total_sub_total += float(self.calculate_sub_total(cart_item))
            total_total += round(float(self.calculate_total(cart_item)), 2)

        # Create a data dictionary to store the cumulative values
        data = {
            'shipping': round(total_shipping, 2),
            'tax': total_tax,
            'service_fee': total_service_fee,
            'sub_total': total_sub_total,
            'total': total_total,
        }

        # Return the data in the response
        return Response(data)

    def calculate_shipping(self, cart_item):
        # Implement your shipping calculation logic here for a single cart item
        # Example: Calculate based on weight, destination, etc.
        return cart_item.shipping_amount

    def calculate_tax(self, cart_item):
        # Implement your tax calculation logic here for a single cart item
        # Example: Calculate based on tax rate, product type, etc.
        return cart_item.tax_fee

    def calculate_service_fee(self, cart_item):
        # Implement your service fee calculation logic here for a single cart item
        # Example: Calculate based on service type, cart total, etc.
        return cart_item.service_fee

    def calculate_sub_total(self, cart_item):
        # Implement your service fee calculation logic here for a single cart item
        # Example: Calculate based on service type, cart total, etc.
        return cart_item.sub_total

    def calculate_total(self, cart_item):
        # Implement your total calculation logic here for a single cart item
        # Example: Sum of sub_total, shipping, tax, and service_fee
        return cart_item.total
    


class CartItemDeleteView(generics.DestroyAPIView):
    serializer_class = CartSerializer
    lookup_field = 'cart_id'  

    def get_object(self):
        cart_id = self.kwargs['cart_id']
        item_id = self.kwargs['item_id']
        user_id = self.kwargs.get('user_id')

        if user_id is not None:
            user = get_object_or_404(User, id=user_id)
            cart = get_object_or_404(Cart, cart_id=cart_id, id=item_id, user=user)
        else:
            cart = get_object_or_404(Cart, cart_id=cart_id, id=item_id)

        return cart
    

class CreateOrderView(generics.CreateAPIView):
    serializer_class = CartOrderSerializer
    queryset = CartOrder.objects.all()
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        payload = request.data

        full_name = payload['full_name']
        email = payload['email']
        mobile = payload['mobile']
        address = payload['address']
        city = payload['city']
        state = payload['state']
        country = payload['country']
        cart_id = payload['cart_id']
        user_id = payload['user_id']

        print("user_id ===============", user_id)

        if user_id != 0:
            user = User.objects.filter(id=user_id).first()
        else:
            user = None

        cart_items = Cart.objects.filter(cart_id=cart_id)

        total_shipping = Decimal(0.0)
        total_tax = Decimal(0.0)
        total_service_fee = Decimal(0.0)
        total_sub_total = Decimal(0.0)
        total_initial_total = Decimal(0.0)
        total_total = Decimal(0.0)

        with transaction.atomic():

            order = CartOrder.objects.create(
                # sub_total=total_sub_total,
                # shipping_amount=total_shipping,
                # tax_fee=total_tax,
                # service_fee=total_service_fee,
                buyer=user,
                payment_status="processing",
                full_name=full_name,
                email=email,
                mobile=mobile,
                address=address,
                city=city,
                state=state,
                country=country
            )

            for c in cart_items:
                CartOrderItem.objects.create(
                    order=order,
                    product=c.product,
                    qty=c.qty,
                    color=c.color,
                    size=c.size,
                    price=c.price,
                    sub_total=c.sub_total,
                    shipping_amount=c.shipping_amount,
                    tax_fee=c.tax_fee,
                    service_fee=c.service_fee,
                    total=c.total,
                    initial_total=c.total,
                    vendor=c.product.vendor
                )

                total_shipping += Decimal(c.shipping_amount)
                total_tax += Decimal(c.tax_fee)
                total_service_fee += Decimal(c.service_fee)
                total_sub_total += Decimal(c.sub_total)
                total_initial_total += Decimal(c.total)
                total_total += Decimal(c.total)

                order.vendor.add(c.product.vendor)

                

            order.sub_total=total_sub_total
            order.shipping_amount=total_shipping
            order.tax_fee=total_tax
            order.service_fee=total_service_fee
            order.initial_total=total_initial_total
            order.total=total_total

            
            order.save()

        return Response( {"message": "Order Created Successfully", 'order_oid':order.oid}, status=status.HTTP_201_CREATED)




class CheckoutView(generics.RetrieveAPIView):
    serializer_class = CartOrderSerializer
    lookup_field = 'order_oid'  

    def get_object(self):
        order_oid = self.kwargs['order_oid']
        cart = get_object_or_404(CartOrder, oid=order_oid)
        return cart
    
 





def get_access_token(client_id, secret_key):
    # Function to get access token from PayPal API
    token_url = 'https://api.sandbox.paypal.com/v1/oauth2/token'
    data = {'grant_type': 'client_credentials'}
    auth = (client_id, secret_key)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        print("access_token ====", response.json()['access_token'])
        return response.json()['access_token']
    else:
        raise Exception(f'Failed to get access token from PayPal. Status code: {response.status_code}') 

    
class PaymentSuccessView(generics.CreateAPIView):
    serializer_class = CartOrderSerializer
    queryset = CartOrder.objects.all()
    
    
    def create(self, request, *args, **kwargs):
        payload = request.data
        
        order_oid = payload['order_oid']
        session_id = payload['session_id']
        payapl_order_id = payload['payapl_order_id']

        order = CartOrder.objects.get(oid=order_oid)
        order_items = CartOrderItem.objects.filter(order=order)

        if payapl_order_id != "null":
            paypal_api_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{payapl_order_id}'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {get_access_token(PAYPAL_CLIENT_ID, PAYPAL_SECRET_ID)}',
            }
            response = requests.get(paypal_api_url, headers=headers)

            if response.status_code == 200:
                paypal_order_data = response.json()
                paypal_payment_status = paypal_order_data['status']
                if paypal_payment_status == 'COMPLETED':
                    if order.payment_status == "processing":
                        order.payment_status = "paid"
                        order.save()
                        if order.buyer != None:
                            send_notification(user=order.buyer, order=order)

                        merge_data = {
                            'order': order, 
                            'order_items': order_items, 
                        }
                        subject = f"Order Placed Successfully"
                        text_body = render_to_string("email/customer_order_confirmation.txt", merge_data)
                        html_body = render_to_string("email/customer_order_confirmation.html", merge_data)
                        
                        msg = EmailMultiAlternatives(
                            subject=subject, from_email=settings.FROM_EMAIL,
                            to=[order.email], body=text_body
                        )
                        msg.attach_alternative(html_body, "text/html")
                        msg.send()

                        for o in order_items:
                            send_notification(vendor=o.vendor, order=order, order_item=o)
                            
                            merge_data = {
                                'order': order, 
                                'order_items': order_items, 
                            }
                            subject = f"New Sale!"
                            text_body = render_to_string("email/vendor_order_sale.txt", merge_data)
                            html_body = render_to_string("email/vendor_order_sale.html", merge_data)
                            
                            msg = EmailMultiAlternatives(
                                subject=subject, from_email=settings.FROM_EMAIL,
                                to=[o.vendor.email], body=text_body
                            )
                            msg.attach_alternative(html_body, "text/html")
                            msg.send()

                        return Response( {"message": "Payment Successfull"}, status=status.HTTP_201_CREATED)
                    else:
                        
                        return Response( {"message": "Already Paid"}, status=status.HTTP_201_CREATED)
            

        
       


class ReviewRatingAPIView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    queryset = Review.objects.all()
    permission_classes = (AllowAny, )

    def create(self, request, *args, **kwargs):
        payload = request.data

        user_id = payload['user_id']
        product_id = payload['product_id']
        rating = payload['rating']
        review = payload['review']

        user = User.objects.get(id=user_id)
        product = Product.objects.get(id=product_id)

        Review.objects.create(user=user, product=product, rating=rating, review=review)
    
        return Response( {"message": "Review Created Successfully."}, status=status.HTTP_201_CREATED)



class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = (AllowAny, )

    def get_queryset(self):
        product_id = self.kwargs['product_id']

        product = Product.objects.get(id=product_id)
        reviews = Review.objects.filter(product=product)
        return reviews
    
class SearchProductsAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        query = self.request.GET.get('query')
        print("query =======", query)

        products = Product.objects.filter(status="published", title__icontains=query)
        return products
       