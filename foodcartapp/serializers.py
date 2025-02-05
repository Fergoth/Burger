from django.core.exceptions import ValidationError

from .models import Product, Order, OrderItem

from rest_framework.serializers import ModelSerializer, IntegerField


class OrderItemSerializer(ModelSerializer):
    product = IntegerField(source='product.id')

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity']
        read_only_fields = ['id']

    def validate_product(self, value):
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
        fields = [
            'id',
            'products',
            'firstname',
            'lastname',
            'address',
            'phonenumber'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        product_items = validated_data.pop('items')
        order_items = []
        order = Order.objects.create(**validated_data)
        for order_item in product_items:
            product = Product.objects.get(id=order_item['product']['id'])
            order_items.append(OrderItem(
                product=product,
                order=order,
                quantity=order_item['quantity'],
                price=product.price
            ))
        OrderItem.objects.bulk_create(order_items)
        return order
