import os

import boto3
from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, request

load_dotenv()


def create_app(dynamodb_client=None, config=None):
    app = Flask(__name__)
    app.config['USERS_TABLE'] = os.environ.get('USERS_TABLE')
    if config:
        app.config.update(config)

    if dynamodb_client is not None:
        app.extensions['dynamodb_client'] = dynamodb_client

    def get_dynamodb_client():
        client = app.extensions.get('dynamodb_client')
        if client is None:
            client_options = {}
            if os.environ.get('IS_OFFLINE'):
                client_options.update(
                    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
                    endpoint_url=os.environ.get(
                        'DYNAMODB_ENDPOINT', 'http://localhost:8000'
                    ),
                )
            client = boto3.client('dynamodb', **client_options)
            app.extensions['dynamodb_client'] = client
        return client

    def get_users_table():
        return app.config['USERS_TABLE']

    @app.route('/users/<string:user_id>')
    def get_user(user_id):
        result = get_dynamodb_client().get_item(
            TableName=get_users_table(), Key={'userId': {'S': user_id}}
        )
        item = result.get('Item')
        if not item:
            return (
                jsonify({'error': 'Could not find user with provided "userId"'}),
                404,
            )

        return jsonify(
            {
                'userId': item.get('userId', {}).get('S'),
                'name': item.get('name', {}).get('S'),
            }
        )

    @app.route('/users', methods=['POST'])
    def create_user():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400

        user_id = payload.get('userId')
        name = payload.get('name')
        if (
            not isinstance(user_id, str)
            or not user_id.strip()
            or not isinstance(name, str)
            or not name.strip()
        ):
            return jsonify({'error': 'Please provide both "userId" and "name"'}), 400

        get_dynamodb_client().put_item(
            TableName=get_users_table(),
            Item={'userId': {'S': user_id}, 'name': {'S': name}},
        )
        return jsonify({'userId': user_id, 'name': name}), 201

    @app.errorhandler(404)
    def resource_not_found(error):
        return make_response(jsonify(error='Not found here'), 404)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000)
