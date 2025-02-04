from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Order
from .models import OrderItem
from .models import Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html(
            '<img src="{url}" style="max-height: 200px;"/>',
            url=obj.image.url
            )
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html(
            '<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>',
            edit_url=edit_url, src=obj.image.url
            )
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]

    readonly_fields = ('created_at',)

    def response_post_save_change(self, request, obj):
        res = super().response_post_save_change(request, obj)
        if 'next' in request.GET and \
            url_has_allowed_host_and_scheme(
                request.GET['next'],
                settings.ALLOWED_HOSTS,):
            return HttpResponseRedirect(reverse('restaurateur:view_orders'))
        else:
            return res

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "restaurant":
            restaurant_menu_items = RestaurantMenuItem.objects.\
                select_related('restaurant').\
                filter(availability=True).\
                values('restaurant_id', 'restaurant__name', 'product_id')
            order_id = request.resolver_match.kwargs['object_id']
            order = Order.objects.prefetch_related('items').get(pk=order_id)
            restaurants_for_current_order = set(
                item['restaurant_id']
                for item in restaurant_menu_items
                )
            for order_item in order.items.all():
                restauraunts_with_product = set(
                    item['restaurant_id']
                    for item in restaurant_menu_items
                    if item['product_id'] == order_item.product_id
                    )
                restaurants_for_current_order &= restauraunts_with_product
            kwargs["queryset"] = Restaurant.objects.\
                filter(id__in=restaurants_for_current_order)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
