import json
from decimal import Decimal
from django.test import TestCase
from webhooks import views, models
from webhooks.tests import utils


class ShopifyViewTest(TestCase):
    '''
    Parent class for Shopify webhook view tests. It provides set-up and
    tear-down code for the rest of the class.
    '''
    @classmethod
    def setUpClass(cls):
        cls.siteid = 'abcd'  # TODO: generate a random site ID

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.factory = utils.ShopifyRequestFactory()

    def _check_copy_field_validity(self, obj, data):
        '''
        Loop through all the fields listed in object.DIRECT_COPY_FIELDS and
        check if the object has these attributes and that they match the
        data contained in the `data` parameter.
         
        :param :class:`django.db.models.Model` obj: the object to check
          the DIRECT_COPY_FIELDS attributes on.
        :param dict data: a dictionary object containing the values that
          the object should have as properties.
        '''
        for fieldname in obj.DIRECT_COPY_FIELDS:
            self.assertEqual(getattr(obj, fieldname), data[fieldname],
                             'Object has an invalid %s value' % fieldname)


class TestShopifyCustomerCreate(ShopifyViewTest):
    '''
    Test that the shopify_customer_create view behaves correctly.
    '''
    def test_with_test_data(self):
        '''
        Send the same data sent by Shopify's test webhook button and
        monitor for proper behavior.
        '''
        path = '/webhooks/shopify/%s/customer_create' % self.siteid
        data = {"accepts_marketing":True,
                "created_at":None,
                "email":"bob@biller.com",
                "first_name":"Bob",
                "id":None,
                "last_name":"Biller",
                "last_order_id":None,
                "multipass_identifier":None,
                "note":"This customer loves ice cream",
                "orders_count":0,
                "state":"disabled",
                "tax_exempt":False,
                "total_spent":"0.00",
                "updated_at":None,
                "verified_email":True,
                "tags":"",
                "last_order_name":None,
                "addresses":[]
        }
        request = self.factory.customer_create(path, data)
        response = views.shopify_customer_create(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Customer.objects.count(), 0,
                         'Test requests should not be added.')

    def test_with_valid_data(self):
        '''
        Test the view with actual data to confirm that a customer
        object is created in the database. Also check that using
        a modified form of the same data results in a second, distinct
        object in the database.
        '''
        path = '/webhooks/shopify/%s/customer_create' % self.siteid
        data = {"accepts_marketing":False,
                "created_at":"2015-05-27T19:12:18+01:00",
                "email":"testme@example.com",
                "first_name":"Test",
                "id":553412611,
                "last_name":"Customer",
                "last_order_id":None,
                "multipass_identifier":None,
                "note":"",
                "orders_count":0,
                "state":"disabled",
                "tax_exempt":False,
                "total_spent":"0.00",
                "updated_at":"2015-05-27T19:12:19+01:00",
                "verified_email":True,
                "tags":"",
                "last_order_name":None,
                "default_address":{
                    "address1":"",
                    "address2":"",
                    "city":"",
                    "company":"",
                    "country":"United States",
                    "first_name":"Test",
                    "id":638359939,
                    "last_name":"Customer",
                    "phone":"",
                    "province":"Alabama",
                    "zip":"",
                    "name":"Test Customer",
                    "province_code":"AL",
                    "country_code":"US",
                    "country_name":"United States",
                    "default":True},
                "addresses":[
                    {"address1":"",
                     "address2":"",
                     "city":"",
                     "company":"",
                     "country":"United States",
                     "first_name":"Test",
                     "id":638359939,
                     "last_name":"Customer",
                     "phone":"",
                     "province":"Alabama",
                     "zip":"",
                     "name":"Test Customer",
                     "province_code":"AL",
                     "country_code":"US",
                     "country_name":"United States",
                     "default":True}
                ]
        }
        request = self.factory.customer_create(path, data)
        response = views.shopify_customer_create(request, self.siteid)
        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')

        self.assertEqual(models.Customer.objects.count(), 1,
                         'View did not create a new Customer object')

        customer = models.Customer.objects.all()[0]
        self.assertEqual(customer.shopify_id, data['id'],
                         'The created customer has an incorrect shopify_id')
        self._check_copy_field_validity(customer, data)
        self.assertEqual(customer.total_spent, Decimal(data['total_spent']),
                         'The created customer has an incorrect total_spent')

        # Modify `data` and create a second customer.
        data['first_name'] = 'Test2'
        data['email'] = 'testyou@example.com'
        data['id'] = 553412612
        data['tags'] = 'hello, world'

        request = self.factory.customer_create(path, data)
        response = views.shopify_customer_create(request, self.siteid)
        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')

        customer = models.Customer.objects.get(shopify_id=data['id'])
        self._check_copy_field_validity(customer, data)

        tags_as_str = []
        for tag in customer.tags.all():
            tags_as_str.append(tag.name)

        self.assertIn('hello', tags_as_str,
                      'The created customer is missing a tag')
        self.assertIn('world', tags_as_str,
                      'The created customer is missing a tag')

        # TODO: add tests for the address fields when address parsing is
        #   complete in the view.

    def test_customer_id_already_exists(self):
        '''
        Test what happens when this view is called twice with the same
        data.
        
        Shopify does this for customers added via their management
        interface. See issue #1 on Github.
        '''
        path = '/webhooks/shopify/%s/customer_create' % self.siteid
        data = {"accepts_marketing":False,
                "created_at":"2015-05-27T19:12:18+01:00",
                "email":"testme@example.com",
                "first_name":"Test",
                "id":553412611,
                "last_name":"Customer",
                "last_order_id":None,
                "multipass_identifier":None,
                "note":"",
                "orders_count":0,
                "state":"disabled",
                "tax_exempt":False,
                "total_spent":"0.00",
                "updated_at":"2015-05-27T19:12:19+01:00",
                "verified_email":True,
                "tags":"",
                "last_order_name":None,
                "default_address":{
                    "address1":"",
                    "address2":"",
                    "city":"",
                    "company":"",
                    "country":"United States",
                    "first_name":"Test",
                    "id":638359939,
                    "last_name":"Customer",
                    "phone":"",
                    "province":"Alabama",
                    "zip":"",
                    "name":"Test Customer",
                    "province_code":"AL",
                    "country_code":"US",
                    "country_name":"United States",
                    "default":True},
                "addresses":[
                    {"address1":"",
                     "address2":"",
                     "city":"",
                     "company":"",
                     "country":"United States",
                     "first_name":"Test",
                     "id":638359939,
                     "last_name":"Customer",
                     "phone":"",
                     "province":"Alabama",
                     "zip":"",
                     "name":"Test Customer",
                     "province_code":"AL",
                     "country_code":"US",
                     "country_name":"United States",
                     "default":True}
                ]
        }

        request = self.factory.customer_create(path, data)
        response = views.shopify_customer_create(request, self.siteid)
        self.assertEqual(response.status_code, 200,
                         'First request in pair failed')

        request = self.factory.customer_create(path, data)
        response = views.shopify_customer_create(request, self.siteid)
        self.assertEqual(response.status_code, 200,
                         'Duplicate request failed')


class TestShopifyCustomerEnable(ShopifyViewTest):
    '''
    Test that the shopify_customer_enable view behaves correctly.
    '''
    def test_with_test_data(self):
        path = '/webhooks/shopify/%s/customer_enable' % self.siteid
        data = {
            'accepts_marketing': True,
            'addresses': [],
            'created_at': None,
            'email': 'bob@biller.com',
            'first_name': 'Bob',
            'id': None,
            'last_name': 'Biller',
            'last_order_id': None,
            'last_order_name': None,
            'multipass_identifier': None,
            'note': 'This customer loves ice cream',
            'orders_count': 0,
            'state': 'disabled',
            'tags': '',
            'tax_exempt': False,
            'total_spent': '0.00',
            'updated_at': None,
            'verified_email': True
        }
        request = self.factory.customer_enable(path, data)
        response = views.shopify_customer_enable(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Customer.objects.count(), 0,
                         'Test requests should not be added')

    def test_with_disabled_customer(self):
        '''
        Test that this webhook functions properly on a disabled
        customer.
        '''
        # Create a customer
        customer = models.Customer(shopify_id=534645123, state='disabled')
        customer.save()

        # Enable the customer
        path = '/webhooks/shopify/%s/customer_enable' % self.siteid
        data = {
            'accepts_marketing': True,
            'addresses': [],
            'created_at': None,
            'email': 'bob@biller.com',
            'first_name': 'Bob',
            'id': 534645123,
            'last_name': 'Biller',
            'last_order_id': None,
            'last_order_name': None,
            'multipass_identifier': None,
            'note': 'This customer loves ice cream',
            'orders_count': 0,
            'state': 'enabled',
            'tags': '',
            'tax_exempt': False,
            'total_spent': '0.00',
            'updated_at': '2015-05-27T19:12:19+01:00',
            'verified_email': True
        }
        request = self.factory.customer_enable(path, data)
        response = views.shopify_customer_enable(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        customer = models.Customer.objects.get(shopify_id=534645123)
        self.assertEqual(customer.state, 'enabled',
                         'Customer state not changed to enabled')

    def test_with_invalid_customer(self):
        '''
        Test that this webhook creates a customer when it receives a
        request to enable a customer that does not exist.
        '''
        path = '/webhooks/shopify/%s/customer_enable' % self.siteid
        data = {
            'accepts_marketing': True,
            'addresses': [],
            'created_at': '2015-05-27T19:12:19+01:00',
            'email': 'bob@biller.com',
            'first_name': 'Bob',
            'id': 534645123,
            'last_name': 'Biller',
            'last_order_id': None,
            'last_order_name': None,
            'multipass_identifier': None,
            'note': 'This customer loves ice cream',
            'orders_count': 0,
            'state': 'enabled',
            'tags': '',
            'tax_exempt': False,
            'total_spent': '0.00',
            'updated_at': '2015-05-27T19:12:19+01:00',
            'verified_email': True
        }
        request = self.factory.customer_enable(path, data)
        response = views.shopify_customer_enable(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')

        self.assertEqual(models.Customer.objects.count(), 1,
                         'Customer object was not created')

        customer = models.Customer.objects.all()[0]
        self.assertEqual(customer.state, 'enabled',
                         'Created customer is not "enabled"')


class TestShopifyCustomerDisable(ShopifyViewTest):
    '''
    Test that the shopify_customer_disable view behaves correctly.
    '''
    def test_with_test_data(self):
        path = '/webhooks/shopify/%s/customer_disable' % self.siteid
        data = {
            'accepts_marketing': True,
            'addresses': [],
            'created_at': None,
            'email': 'bob@biller.com',
            'first_name': 'Bob',
            'id': None,
            'last_name': 'Biller',
            'last_order_id': None,
            'last_order_name': None,
            'multipass_identifier': None,
            'note': 'This customer loves ice cream',
            'orders_count': 0,
            'state': 'disabled',
            'tags': '',
            'tax_exempt': False,
            'total_spent': '0.00',
            'updated_at': None,
            'verified_email': True
        }

        request = self.factory.customer_enable(path, data)
        response = views.shopify_customer_disable(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Customer.objects.count(), 0,
                         'Test requests should not be added')

    def test_with_disabled_customer(self):
        '''
        Test that this webhook functions properly on a disabled
        customer.
        '''
        # Create a customer
        customer = models.Customer(shopify_id=534645123, state='disabled')
        customer.save()

        # Enable the customer
        path = '/webhooks/shopify/%s/customer_disable' % self.siteid
        data = {
            'accepts_marketing': True,
            'addresses': [],
            'created_at': None,
            'email': 'bob@biller.com',
            'first_name': 'Bob',
            'id': 534645123,
            'last_name': 'Biller',
            'last_order_id': None,
            'last_order_name': None,
            'multipass_identifier': None,
            'note': 'This customer loves ice cream',
            'orders_count': 0,
            'state': 'disable',
            'tags': '',
            'tax_exempt': False,
            'total_spent': '0.00',
            'updated_at': '2015-05-27T19:12:19+01:00',
            'verified_email': True
        }
        request = self.factory.customer_enable(path, data)
        response = views.shopify_customer_disable(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        customer = models.Customer.objects.get(shopify_id=534645123)
        self.assertEqual(customer.state, 'disabled',
                         'Customer state not changed to enabled')

    def test_with_invalid_customer(self):
        '''
        Test that this webhook creates a customer when it receives a
        request to enable a customer that does not exist.
        '''
        path = '/webhooks/shopify/%s/customer_disable' % self.siteid
        data = {
            'accepts_marketing': True,
            'addresses': [],
            'created_at': '2015-05-27T19:12:19+01:00',
            'email': 'bob@biller.com',
            'first_name': 'Bob',
            'id': 534645123,
            'last_name': 'Biller',
            'last_order_id': None,
            'last_order_name': None,
            'multipass_identifier': None,
            'note': 'This customer loves ice cream',
            'orders_count': 0,
            'state': 'disabled',
            'tags': '',
            'tax_exempt': False,
            'total_spent': '0.00',
            'updated_at': '2015-05-27T19:12:19+01:00',
            'verified_email': True
        }
        request = self.factory.customer_enable(path, data)
        response = views.shopify_customer_enable(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Customer.objects.count(), 1,
                         'Customer object was not created')

        customer = models.Customer.objects.all()[0]
        self.assertEqual(customer.state, 'disabled',
                         'Created customer is not "disabled"')


class TestShopifyCustomerUpdate(ShopifyViewTest):
    '''
    Test that the shopify_customer_update view behaves correctly.
    '''
    def test_with_test_data(self):
        path = '/webhooks/shopify/%s/customer_update' % self.siteid
        data = {"accepts_marketing":True,
                "created_at":None,
                "email":"bob@biller.com",
                "first_name":"Bob",
                "id":None,
                "last_name":"Biller",
                "last_order_id":None,
                "multipass_identifier":None,
                "note":"This customer loves ice cream",
                "orders_count":0,
                "state":"disabled",
                "tax_exempt":False,
                "total_spent":"0.00",
                "updated_at":None,
                "verified_email":True,
                "tags":"",
                "last_order_name":None,
                "addresses":[]
        }
        request = self.factory.customer_update(path, data)
        response = views.shopify_customer_update(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Customer.objects.count(), 0,
                         'Test requests should not be added')

    def test_shopify_customer_update(self):
        '''
        Check that this view will create a new customer object with the
        given data if a customer does not currently exist. If a
        customer with he given ID already exists, test that it is then
        updated with the modified data.
        '''
        # Test creation of unknown customers
        path = '/webhooks/shopify/%s/customer_update' % self.siteid
        data = {"accepts_marketing":False,
                "created_at":"2015-05-27T19:12:18+01:00",
                "email":"testme@example.com",
                "first_name":"Test",
                "id":553412611,
                "last_name":"Customer",
                "last_order_id":None,
                "multipass_identifier":None,
                "note":"",
                "orders_count":0,
                "state":"disabled",
                "tax_exempt":False,
                "total_spent":"0.00",
                "updated_at":"2015-05-27T21:30:34+01:00",
                "verified_email":True,
                "tags":"hello, secondtag, shorttag, world",
                "last_order_name":None,
                "default_address": {
                    "address1":"",
                    "address2":"",
                    "city":"",
                    "company":"",
                    "country":"United States",
                    "first_name":"Test",
                    "id":638359939,
                    "last_name":"Customer",
                    "phone":"",
                    "province":"Alabama",
                    "zip":"",
                    "name":"Test Customer",
                    "province_code":"AL",
                    "country_code":"US",
                    "country_name":"United States",
                    "default":True
                }, "addresses":[
                    {"address1":"",
                     "address2":"",
                     "city":"",
                     "company":"",
                     "country":"United States",
                     "first_name":"Test",
                     "id":638359939,
                     "last_name":"Customer",
                     "phone":"",
                     "province":"Alabama",
                     "zip":"",
                     "name":"Test Customer",
                     "province_code":"AL",
                     "country_code":"US",
                     "country_name":"United States",
                     "default":True
                    }
                ]
        }
        request = self.factory.customer_update(path, data)
        response = views.shopify_customer_update(request, self.siteid)
        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')

        self.assertEqual(models.Customer.objects.count(), 1,
                         'Customer update resulted in incorrect object count')

        customer = models.Customer.objects.all()[0]
        self._check_copy_field_validity(customer, data)

        tags_as_str = []
        for tag in customer.tags.all():
            tags_as_str.append(tag.name)

        self.assertIn('hello', tags_as_str,
                      'The created customer is missing a tag')
        self.assertIn('world', tags_as_str,
                      'The created customer is missing a tag')

        # Test that existing customers are properly updated.
        data['email'] = 'updatedemail@example.com'
        data['tags'] = 'tag1, tag2'

        request = self.factory.customer_update(path, data)
        response = views.shopify_customer_update(request, self.siteid)
        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')

        self.assertEqual(models.Customer.objects.count(), 1,
                         'Customer update resulted in incorrect object count')

        customer = models.Customer.objects.all()[0]
        self._check_copy_field_validity(customer, data)

        tags_as_str = []
        for tag in customer.tags.all():
            tags_as_str.append(tag.name)

        self.assertIn('tag1', tags_as_str,
                      'The created customer is missing a tag')
        self.assertIn('tag2', tags_as_str,
                      'The created customer is missing a tag')
        self.assertNotIn('hello', tags_as_str,
                         'Old tag not deleted during update')
        self.assertNotIn('world', tags_as_str,
                         'Old tag not deleted during update')


class TestShopifyCustomerDelete(ShopifyViewTest):
    '''
    Test that the shopify_customer_delete view behaves correctly.
    '''
    def test_with_test_data(self):
        '''
        Send the data from Shopify's test webhook button and monitor
        for correct behavior.
        '''
        path = '/webhooks/shoify/%s/customer_delete' % self.siteid
        data = {"id":None,
                "addresses":[]
        }
        request = self.factory.customer_delete(path, data)
        response = views.shopify_customer_delete(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')

    def test_shopify_customer_delete(self):
        '''
        Test the view with actual data to ensure proper functionality.
        This view is tested for both existing and non-existing customer
        objects.
        '''
        # Test deletion with an existing customer
        customer = models.Customer()
        customer.shopify_id = 534645123
        customer.save()

        path = '/webhooks/shopify/%s/customer_delete' % self.siteid
        data = {'id': customer.shopify_id}
        request = self.factory.customer_delete(path, data)
        response = views.shopify_customer_delete(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Customer.objects.count(), 0,
                         'Customer not correctly deleted')

        # Reply the delete to test when customer does not exist
        response = views.shopify_customer_delete(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Customer.objects.count(), 0,
                         'The last object should have been deleted')


class TestShopifyShopUpdate(ShopifyViewTest):
    '''
    Test that the shopify_shop_update view behaves correctly.
    '''
    def test_with_test_data(self):
        '''
        Send the data from the Shopify test webhook button and monitor
        for proper behavior.
        '''
        # Test shop creation
        path = '/webhooks/shopify/%s/shop_update' % self.siteid
        data = {"address1":"190 MacLaren Street",
                "city":"Houston",
                "country":"US",
                "created_at":None,
                "customer_email":None,
                "domain":None,
                "email":"super@supertoys.com",
                "id":None,
                "latitude":None,
                "longitude":None,
                "name":"Super Toys",
                "phone":"3213213210",
                "primary_locale":"en",
                "primary_location_id":None,
                "province":"Tennessee",
                "source":None,
                "zip":"37178",
                "country_code":"US",
                "country_name":"United States",
                "currency":"USD",
                "timezone":"(GMT-05:00) Eastern Time (US \u0026 Canada)",
                "iana_timezone":None,
                "shop_owner":"N\/A",
                "money_format":"$ {{amount}}",
                "money_with_currency_format":"$ {{amount}} USD",
                "province_code":"TN",
                "taxes_included":None,
                "tax_shipping":None,
                "county_taxes":None,
                "plan_display_name":None,
                "plan_name":None,
                "myshopify_domain":None,
                "google_apps_domain":None,
                "google_apps_login_enabled":None,
                "money_in_emails_format":"${{amount}}",
                "money_with_currency_in_emails_format":"${{amount}} USD",
                "eligible_for_payments":True,
                "requires_extra_payments_agreement":False,
                "password_enabled":None,
                "has_storefront":False
        }
        request = self.factory.shop_update(path, data)
        response = views.shopify_shop_update(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Shop.objects.count(), 0,
                         'The test request should not create a shop')

    def test_with_valid_data(self):
        '''
        Test that this view creates a new shop in the case that the
        shop to be updated does not exist. If the shop does exist,
        check that it is updated.
        '''
        path = '/webhooks/shopify/%s/shop_update' % self.id
        data = {"address1":"121 West Sprint Street",
                "city":"Appleton",
                "country":"US",
                "created_at":"2015-05-19T17:45:19+01:00",
                "customer_email":'sales@example.com',
                "domain":"example.myshopify.com",
                "email":"test@example.com",
                "id":8711838,
                "latitude":12.4567,
                "longitude":-80.1234,
                "name":"My First Test Store",
                "phone":"",
                "primary_locale":"en",
                "primary_location_id":None,
                "province":"Wisconsin",
                "source":"learn-more",
                "zip":"12345",
                "country_code":"US",
                "country_name":"United States",
                "currency":"USD",
                "timezone":"(GMT+00:00) London",
                "iana_timezone":"Europe\/London",
                "shop_owner":"Austin Hartzheim",
                "money_format":"$ {{amount}}",
                "money_with_currency_format":"$ {{amount}} USD",
                "province_code":"WI",
                "taxes_included":False,
                "tax_shipping":None,
                "county_taxes":None,
                "plan_display_name":"affiliate",
                "plan_name":"affiliate",
                "myshopify_domain":"example.myshopify.com",
                "google_apps_domain":None,
                "google_apps_login_enabled":None,
                "money_in_emails_format":"${{amount}}",
                "money_with_currency_in_emails_format":"${{amount}} USD",
                "eligible_for_payments":True,
                "requires_extra_payments_agreement":False,
                "password_enabled":True,
                "has_storefront":True
        }
        request = self.factory.shop_update(path, data)
        response = views.shopify_shop_update(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error')
        self.assertEqual(models.Shop.objects.count(), 1,
                         'One shop should exist')

        shop = models.Shop.objects.all()[0]
        self.assertEqual(shop.shopify_id, data['id'],
                         'Created shop has incorrect shopify_id value')
        self._check_copy_field_validity(shop, data)

        # Test shop update
        data['city'] = 'New York'
        data['shop_owner'] = 'Bob Smith'

        request = self.factory.shop_update(path, data)
        response = views.shopify_shop_update(request, self.siteid)

        self.assertEqual(response.status_code, 200,
                         'View returned an HTTP error code')
        self.assertEqual(models.Shop.objects.count(), 1,
                         'One shop should exist')

        shop = models.Shop.objects.all()[0]
        self.assertEqual(shop.shopify_id, data['id'],
                         'Created shop has an incorrect shopify_id')
        self._check_copy_field_validity(shop, data)

