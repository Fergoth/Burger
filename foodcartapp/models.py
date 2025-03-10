from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Sum, F
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from phonenumber_field.modelfields import PhoneNumberField
 

class Restaurant(models.Model):

    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def annotate_with_total_cost(self):
        orders = self.prefetch_related('items').all()
        return orders.annotate(
            total_cost=Sum(F('items__quantity')*F('items__price'))
            )


class Order(models.Model):
    class Status(models.IntegerChoices):
        CREATED = 1, _('Создан')
        ASSEMBLING = 2, _('Собирается')
        DELIVERING = 3, _('Доставляется')
        DONE = 4, _('Завершен')

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Наличные')
        ELECTRONIC = 'ELEC', _('Электронно')

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='ресторан',
        null=True,
        blank=True
    )
    firstname = models.CharField(
        'имя',
        max_length=30,
    )
    lastname = models.CharField(
        'фамилия',
        max_length=30,
        blank=True
    )
    phonenumber = PhoneNumberField(
        'номер телефона'
    )
    address = models.CharField(
        'адрес',
        max_length=100,
    )
    status = models.IntegerField(
        'статус',
        choices=Status.choices,
        default=Status.CREATED,
        db_index=True
    )
    comment = models.TextField(
        'коментарий',
        max_length=200,
        blank=True,
    )

    created_at = models.DateTimeField(
        'время регистрации заказа',
        default=timezone.now,
        db_index=True
    )
    called_at = models.DateTimeField(
        'время звонка',
        null=True,
        blank=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'время доставки закза',
        null=True,
        blank=True,
        db_index=True
    )
    payment_method = models.CharField(
        'способ оплаты',
        max_length=4,
        choices=PaymentMethod.choices,
        db_index=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname} {self.address}. {self.get_status_display()}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='заказ',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='продукт',
    )
    quantity = models.PositiveIntegerField(
        'количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'цена позиции',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def __str__(self):
        return f"{self.product} {self.order}"
