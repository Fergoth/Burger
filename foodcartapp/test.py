import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from foodcartapp.views import OrderSerializer

class MyModelSerializerTest(APITestCase):
    fixtures = ['dummy.json']
    def serializer(self,data):
        url = reverse('foodcartapp:order')
        response = self.client.post(url,data=json.loads(data),content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_wrong_firstname(self):
        data = '{"products": [{"product": 1, "quantity": 1}], "firstname": null, "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.serializer(data)

    def test_no_keys(self):
        data = '{"products": [{"product": 1, "quantity": 1}]}'
        self.serializer(data)

    def test_product_empty(self):
        data = '{"products": [], "firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.serializer(data)

    def test_no_phone_number(self):
        data ='{"products": [{"product": 1, "quantity": 1}], "firstname": "Тимур", "lastname": "Иванов", "phonenumber": "", "address": "Москва, Новый Арбат 10"}'
        self.serializer(data)

    def test_invalid_phone_number(self):
        data ='{"products": [{"product": 1, "quantity": 1}], "firstname": "Тимур", "lastname": "Иванов", "phonenumber": "+70000000000", "address": "Москва, Новый Арбат 10"}'
        self.serializer(data)

    def test_invalid_product_id(self):
        data ='{"products": [{"product": 9999, "quantity": 1}], "firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.serializer(data)

    def test_invalid_firstname(self):
        data='{"products": [{"product": 1, "quantity": 1}], "firstname": [], "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.serializer(data)

    def test_invalid_product_type(self):
        data='{"products": "HelloWorld", "firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.serializer(data)

    def test_invalid_profuct_type_null(self):
        data='{"products": null, "firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.serializer(data)

    def test_no_product(self):
        data='{"firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.serializer(data)
