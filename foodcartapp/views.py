from django.http import JsonResponse
from django.templatetags.static import static
from django.core.exceptions import ValidationError

from .models import Product, Order, OrderItem

from phonenumber_field.validators import validate_international_phonenumber
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


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
    errors = []
    order = request.data
    if 'products' not in order:
        errors.append('products key not presented')
    else:
        products = order['products']
        if not isinstance(products, list):
            errors.append('products are not a list')
        elif not products:
            errors.append('products are empty')

    if 'firstname' not in order:
        errors.append('firstname key not presented')
    else:
        firstname = order['firstname']
        if not isinstance(firstname, str):
            errors.append('firstname are not a string')
        elif not firstname:
            errors.append('firstname are empty')
    
    if 'lastname' not in order:
        errors.append('lastname key not presented')
    else:
        lastname = order['lastname']
        if not isinstance(lastname, str):
            errors.append('lastname are not a string')
        elif not lastname:
            errors.append('lastname are empty')

    if 'address' not in order:
        errors.append('address key not presented')
    else:
        address = order['address']
        if not isinstance(address, str):
            errors.append('address are not a string')
        elif not address:
            errors.append('address are empty')

    if 'phonenumber' not in order:
        errors.append('phonenumber key not presented')
    else:
        phone_number = order['phonenumber']
        if not phone_number:
            errors.append('phonenumber is empty')
        try:
            validate_international_phonenumber(phone_number)
        except ValidationError:
            errors.append('invalid telephone number')
     
    created_order = Order(
        firstname=firstname,
        lastname=lastname,
        phone_number=phone_number,
        address=address 
        )
    order_items = []
    for product_item in products:
        product_id = product_item['product']
        quantity = product_item['quantity']
        try:
            product = Product.objects.get(id=product_id)
            order_items.append(OrderItem(
                product=product,
                order=created_order,
                quantity=quantity
            ))
        except Product.DoesNotExist:
            errors.append(f'invalid product id {product_id}')

        
    if errors:
        return Response(
            {'errors': errors},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        ) 
    else:
        created_order.save()
        OrderItem.objects.bulk_create(order_items)

    return Response(order)
