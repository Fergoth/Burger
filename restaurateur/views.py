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
from collections import namedtuple

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from place_coords.models import Location


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
        availability = {item.restaurant_id: item.availability
                        for item in product.menu_items.all()
                        }
        ordered_availability = [availability.get(restaurant.id, False)
                                for restaurant in restaurants]

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


def get_distance(point1, point2):
    return distance.distance(point1, point2).km


def fetch_coordinates_api(apikey, address):
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


def find_restaurants_for_order(order, restaurant_menu_items):
    Restaurant_tuple = namedtuple('Restaurant_tuple', ['name', 'address'])
    restaurants_for_current_order = set(
        Restaurant_tuple(item['restaurant__name'], item['restaurant__address'])
        for item in restaurant_menu_items
    )
    for order_item in order.items.all():
        restauraunts_with_product = set(
            Restaurant_tuple(
                item['restaurant__name'],
                item['restaurant__address']
                )
            for item in restaurant_menu_items
            if item['product_id'] == order_item.product_id
            )
        restaurants_for_current_order &= restauraunts_with_product
    return restaurants_for_current_order


def fetch_coords(locations, address, api_key):
    if address in locations:
        if locations[address]['correct_address']:
            lat = locations[address]['latitude']
            lon = locations[address]['longitude']
            return lat, lon
        else:
            return None
    else:
        try:
            coords = fetch_coordinates_api(api_key, address)
        except requests.RequestException:
            return None
        if coords is None:
            Location.objects.get_or_create(
                correct_address=False,
                defaults={'address': address}
            )
            return None
        lat, lon = coords
        Location.objects.get_or_create(
            latitude=lat,
            longitude=lon,
            defaults={'address': address}
        )
        return lat, lon


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    api_key = settings.YANDEX_GEO_API_KEY
    orders = Order.objects.exclude(status=Order.Status.DONE).\
        annotate_with_total_cost()
    restaurant_menu_items = RestaurantMenuItem.objects.\
        select_related('restaurant').\
        filter(availability=True).\
        values('restaurant_id',
               'restaurant__name',
               'product_id',
               'restaurant__address'
               )

    orders_addresses = set(order.address for order in orders)
    restaurants_addresses = set(restaurant['restaurant__address']
                                for restaurant in restaurant_menu_items)
    locations = Location.objects.\
        filter(address__in=orders_addresses | restaurants_addresses).\
        values()
    locations = {location['address']: location for location in locations}

    for order in orders:
        if order.status == Order.Status.ASSEMBLING:
            order.message = f'Готовит {order.restaurant.name}'
        elif order.status == Order.Status.DELIVERING:
            order.message = f'Доставляет {order.restaurant.name}'
        else:
            restaurants_for_current_order = find_restaurants_for_order(
                order,
                restaurant_menu_items
                )
            if restaurants_for_current_order:
                order_point = fetch_coords(locations, order.address, api_key)
                if order_point is None:
                    order.message = 'Ошибка определения координат'
                    continue
                restaurants_with_distances = []
                for restaurant in restaurants_for_current_order:
                    restaurant_point = fetch_coords(
                        locations,
                        restaurant.address,
                        api_key
                        )
                    if restaurant_point is None:
                        restaurants_with_distances.append(
                            {
                                'name': restaurant.name,
                                'distance': 'Ошибка в адресе ресторана'
                            }
                        )
                    else:
                        restaurants_with_distances.append(
                            {
                                'name': restaurant.name,
                                'distance': get_distance(
                                    order_point,
                                    restaurant_point
                                    )
                            }
                        )   
                order.restaurants = sorted(
                    restaurants_with_distances,
                    key=lambda x: x['distance'])
                order.message = 'Может быть доставлен следующими ресторанами:'
            else:
                order.message = 'Ни один ресторан не может выполнить заказ'
    return render(
        request,
        template_name='order_items.html',
        context={
            'orders': orders
        }
    )
