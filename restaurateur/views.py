from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.conf import settings

import requests
from geopy import distance

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })

def get_distance(point1,point2):
    return distance.distance(point1,point2).km
    
def add_restoraunts_to_orders(orders):
    api_key = settings.YANDEX_GEO_API_KEY
    restaurant_menu_items = RestaurantMenuItem.objects.select_related('restaurant').filter(availability=True).values('restaurant_id','restaurant__name','product_id','restaurant__address')
    for order in orders:
        if order.status==Order.Status.ASSEMBLING:
            order.message = f'Готовит {order.restaurant.name}'
        elif order.status==Order.Status.DELIVERING:
            order.message = f'Доставляет {order.restaurant.name}'
        else:
            restaurants_for_current_order = set((item['restaurant__name'],item['restaurant__address']) for item in restaurant_menu_items)
            for order_item in order.items.all():
                restauraunts_with_product = set((item['restaurant__name'],item['restaurant__address']) for item in restaurant_menu_items if item['product_id'] == order_item.product_id)
                restaurants_for_current_order&=restauraunts_with_product
            #TODO Ошибка геокодера
            order_point = fetch_coordinates(api_key,order.address)
            if order_point is None:
                order.message ='Ошибка определения координат'
                continue
            restaurants_with_distances = []
            for restaurant in restaurants_for_current_order:
                restaurant_point = fetch_coordinates(api_key,restaurant[1])
                if order_point and restaurant_point:
                    restaurants_with_distances.append({'name':restaurant[0],'distance': get_distance(order_point,restaurant_point)})         
            order.restaurants = sorted(restaurants_with_distances,key=lambda x : x['distance'])
            order.message = 'Может быть доставлен следующими ресторанами:'
    return orders

def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon

@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.exclude(status=Order.Status.DONE).annotate_with_total_cost()
    orders = add_restoraunts_to_orders(orders)
    #TODO details in template
    
    return render(request, template_name='order_items.html', context={
        'orders':orders
    })
