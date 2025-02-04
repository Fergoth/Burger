from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class MyModelSerializerTest(APITestCase):
    fixtures = ['dummy.json']
    def bad_request(self, data):
        url = reverse('foodcartapp:order')
        response = self.client.post(
            url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def good_request(self, data):
        url = reverse('foodcartapp:order')
        response = self.client.post(
            url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_wrong_firstname(self):
        data = '{"products": [{"product": 1, "quantity": 1}], "firstname": null, "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.bad_request(data)

    def test_no_keys(self):
        data = '{"products": [{"product": 1, "quantity": 1}]}'
        self.bad_request(data)

    def test_product_empty(self):
        data = '{"products": [], "firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.bad_request(data)

    def test_no_phone_number(self):
        data = '{"products": [{"product": 1, "quantity": 1}], "firstname": "Тимур", "lastname": "Иванов", "phonenumber": "", "address": "Москва, Новый Арбат 10"}'
        self.bad_request(data)

    def test_invalid_phone_number(self):
        data = '{"products": [{"product": 1, "quantity": 1}], "firstname": "Тимур", "lastname": "Иванов", "phonenumber": "+70000000000", "address": "Москва, Новый Арбат 10"}'
        self.bad_request(data)

    def test_invalid_product_id(self):
        data = '{"products": [{"product": 9999, "quantity": 1}], "firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.bad_request(data)

    def test_invalid_firstname(self):
        data = '{"products": [{"product": 1, "quantity": 1}], "firstname": [], "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.bad_request(data)

    def test_invalid_product_type(self):
        data = '{"products": "HelloWorld", "firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.bad_request(data)

    def test_invalid_profuct_type_null(self):
        data = '{"products": null, "firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.bad_request(data)

    def test_no_product(self):
        data = '{"firstname": "Иван", "lastname": "Петров", "phonenumber": "+79291000000", "address": "Москва"}'
        self.bad_request(data)

    def test_good_data(self):
        data = '{"products": [{"product": 1, "quantity": 1}], "firstname": "Василий", "lastname": "Васильевич", "phonenumber": "+79123456789", "address": "Лондон"}'
        self.good_request(data)
