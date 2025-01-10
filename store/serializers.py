from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from store.models import CancelledOrder, Cart, CartOrderItem, Notification, Product, Tag ,Category, DeliveryCouriers, CartOrder, Gallery, Brand, ProductFaq, Review,  Specification, Color, Size, Address, Wishlist, Vendor
from addon.models import ConfigSettings
from store.models import Gallery
from userauths.serializer import ProfileSerializer, UserSerializer

class ConfigSettingsSerializer(serializers.ModelSerializer):

    class Meta:
            model = ConfigSettings
            fields = '__all__'


# Define a serializer for the Category model
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

# Define a serializer for the Tag model
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

# Define a serializer for the Brand model
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'


        # Define a serializer for the Gallery model
class GallerySerializer(serializers.ModelSerializer):
    # Serialize the related Product model

    class Meta:
        model = Gallery
        fields = '__all__'

# Define a serializer for the Specification model
class SpecificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Specification
        fields = '__all__'

# Define a serializer for the Size model
class SizeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Size
        fields = '__all__'

# Define a serializer for the Color model
class ColorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Color
        fields = '__all__'


# Define a serializer for the Product model
class ProductSerializer(serializers.ModelSerializer):
    gallery = GallerySerializer(many=True, read_only=True)
    color = ColorSerializer(many=True, read_only=True)
    size = SizeSerializer(many=True, read_only=True)
    specification = SpecificationSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "title", "image", "description", "category", "tags", "brand",
            "price", "old_price", "shipping_amount", "stock_qty", "in_stock",
            "status", "type", "featured", "hot_deal", "special_offer", "digital",
            "views", "orders", "saved", "vendor", "sku", "pid", "slug", "date",
            "gallery", "specification", "size", "color", "product_rating", 
            "rating_count", "order_count",
        ]

    def create(self, validated_data):
        gallery_data = validated_data.pop('gallery', [])
        color_data = validated_data.pop('color', [])
        size_data = validated_data.pop('size', [])
        specification_data = validated_data.pop('specification', [])

        # Create the product first
        product = Product.objects.create(**validated_data)

        # Handle the nested serializers
        for gallery_item in gallery_data:
            Gallery.objects.create(product=product, **gallery_item)
        for color_item in color_data:
            Color.objects.create(product=product, **color_item)
        for size_item in size_data:
            Size.objects.create(product=product, **size_item)
        for specification_item in specification_data:
            Specification.objects.create(product=product, **specification_item)

        return product

    def update(self, instance, validated_data):
        gallery_data = validated_data.pop('gallery', [])
        color_data = validated_data.pop('color', [])
        size_data = validated_data.pop('size', [])
        specification_data = validated_data.pop('specification', [])

        # Update the product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update the nested fields (this will depend on your relationships)
        for gallery_item in gallery_data:
            Gallery.objects.create(product=instance, **gallery_item)
        for color_item in color_data:
            Color.objects.create(product=instance, **color_item)
        for size_item in size_data:
            Size.objects.create(product=instance, **size_item)
        for specification_item in specification_data:
            Specification.objects.create(product=instance, **specification_item)

        return instance




# Define a serializer for the ProductFaq model
class ProductFaqSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    product = ProductSerializer()

    class Meta:
        model = ProductFaq
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ProductFaqSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new product FAQ, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3

# Define a serializer for the CartOrderItem model
from rest_framework import serializers
from .models import Cart, Product  # Import the models
from .serializers import ProductSerializer  # Import the ProductSerializer

class CartSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    product = ProductSerializer()

    class Meta:
        model = Cart
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super(CartSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order item, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3

    def create(self, validated_data):
        # Extract the nested product data
        product_data = validated_data.pop('product')

        # Create or get the Product instance
        product, _ = Product.objects.get_or_create(**product_data)

        # Create the Cart instance and associate the product
        cart = Cart.objects.create(product=product, **validated_data)
        return cart


# Define a serializer for the CartOrderItem model
class CartOrderItemSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    # product = ProductSerializer()  

    class Meta:
        model = CartOrderItem
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super(CartOrderItemSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order item, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3

# Define a serializer for the CartOrder model
class CartOrderSerializer(serializers.ModelSerializer):
    # Serialize related CartOrderItem models
    orderitem = CartOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = CartOrder
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CartOrderSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3


class VendorSerializer(serializers.ModelSerializer):
    # Serialize related CartOrderItem models
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(VendorSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cart order, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3

# Define a serializer for the Review model
class ReviewSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    product = ProductSerializer()
    profile = ProfileSerializer()
    
    class Meta:
        model = Review
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ReviewSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new review, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3

# Define a serializer for the Wishlist model
class WishlistSerializer(serializers.ModelSerializer):
    # Serialize the related Product model
    product = ProductSerializer()

    class Meta:
        model = Wishlist
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(WishlistSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new wishlist item, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3

# Define a serializer for the Address model
class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AddressSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new address, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3

# Define a serializer for the CancelledOrder model
class CancelledOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = CancelledOrder
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CancelledOrderSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new cancelled order, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3




# Define a serializer for the DeliveryCouriers model
class DeliveryCouriersSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryCouriers
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(NotificationSerializer, self).__init__(*args, **kwargs)
        # Customize serialization depth based on the request method.
        request = self.context.get('request')
        if request and request.method == 'POST':
            # When creating a new coupon user, set serialization depth to 0.
            self.Meta.depth = 0
        else:
            # For other methods, set serialization depth to 3.
            self.Meta.depth = 3


class SummarySerializer(serializers.Serializer):
    products = serializers.IntegerField()
    orders = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)

class EarningSummarySerializer(serializers.Serializer):
    monthly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)




class NotificationSummarySerializer(serializers.Serializer):
    un_read_noti = serializers.IntegerField(default=0)
    read_noti = serializers.IntegerField(default=0)
    all_noti = serializers.IntegerField(default=0)