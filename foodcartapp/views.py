from django.http import JsonResponse
from django.templatetags.static import static
from django.core.exceptions import ValidationError

from .models import Product, Order, OrderItem

from phonenumber_field.validators import validate_international_phonenumber
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ListField, ModelSerializer, IntegerField,ValidationError

class OrderItemSerializer(ModelSerializer):
    product = IntegerField(source='product.id')
    class Meta:
        model = OrderItem
        fields = ['id','product','quantity']
        read_only_fields = ['id']

    def validate_product(self,value):
        try:
            Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise ValidationError(f'invalid product id {value}')
        print(value)
        return value 

class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(
        many=True,
        allow_empty=False,
        source='items'     
    )
    class Meta:
        model = Order
        fields = ['id','products','firstname', 'lastname', 'address', 'phonenumber']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        products = validated_data.pop('items')
        order_items = []
        order = Order.objects.create(**validated_data)
        for order_item in products:
            product = Product.objects.get(id=order_item['product']['id'])
            order_items.append(OrderItem(
                product=product,
                order=order,
                quantity=order_item['quantity']
            ))
        OrderItem.objects.bulk_create(order_items)
        return order
            




def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = serializer.save()
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
