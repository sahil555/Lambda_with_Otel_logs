import unittest

from .. import app


class FakeDynamoDBClient:
    def __init__(self):
        self.users = {}

    def put_item(self, TableName, Item):
        self.users[Item['userId']['S']] = Item

    def get_item(self, TableName, Key):
        item = self.users.get(Key['userId']['S'])
        return {'Item': item} if item else {}


class UserApiTests(unittest.TestCase):
    def setUp(self):
        self.dynamodb = FakeDynamoDBClient()
        app = app.create_app(
            dynamodb_client=self.dynamodb,
            config={'TESTING': True, 'USERS_TABLE': 'test-users'},
        )
        self.client = app.test_client()

    def test_create_user_returns_created_user(self):
        response = self.client.post(
            '/users', json={'userId': 'user-123', 'name': 'Ada Lovelace'}
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.get_json(), {'userId': 'user-123', 'name': 'Ada Lovelace'}
        )
        self.assertIn('user-123', self.dynamodb.users)

    def test_get_user_returns_existing_user(self):
        self.dynamodb.put_item(
            TableName='test-users',
            Item={'userId': {'S': 'user-123'}, 'name': {'S': 'Ada Lovelace'}},
        )

        response = self.client.get('/users/user-123')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), {'userId': 'user-123', 'name': 'Ada Lovelace'}
        )

    def test_get_missing_user_returns_not_found(self):
        response = self.client.get('/users/missing')

        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.get_json())

    def test_create_user_rejects_missing_fields(self):
        response = self.client.post('/users', json={'userId': 'user-123'})

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_create_user_rejects_non_object_json(self):
        response = self.client.post('/users', json=['user-123', 'Ada'])

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_create_user_rejects_malformed_json(self):
        response = self.client.post(
            '/users', data='{', content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())


if __name__ == '__main__':
    unittest.main()