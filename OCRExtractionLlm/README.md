# OCRExtractionLlm API

A Flask user API backed by DynamoDB and deployable to AWS Lambda with the Serverless Framework.

## API

`POST /users` creates a user. Send a JSON object with non-empty string values for `userId` and `name`:

```sh
curl -i -X POST http://localhost:3000/users \
  -H 'Content-Type: application/json' \
  -d '{"userId":"user-123","name":"Ada Lovelace"}'
```

Successful creation returns `201 Created`:

```json
{"userId":"user-123","name":"Ada Lovelace"}
```

`GET /users/{userId}` returns a stored user with `200 OK`, or `404 Not Found` if the user does not exist. Invalid or malformed JSON passed to `POST /users` returns `400 Bad Request`.

## Tests

The tests use Flask's test client and an in-memory DynamoDB fake, so they do not require AWS credentials or a running database.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Local API

The Flask development server listens on `127.0.0.1:3000`. To use DynamoDB Local, start an emulator in Docker:

```sh
docker run --rm -p 8000:8000 amazon/dynamodb-local:latest \
  -jar DynamoDBLocal.jar -sharedDb
```

In another terminal, create the table and launch the app. These local credentials are only placeholders for DynamoDB Local:

```sh
AWS_ACCESS_KEY_ID=local AWS_SECRET_ACCESS_KEY=local aws dynamodb create-table \
  --table-name users-table-dev \
  --attribute-definitions AttributeName=userId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
  --endpoint-url http://localhost:8000 --region us-east-1

IS_OFFLINE=true USERS_TABLE=users-table-dev python app.py
```

`DYNAMODB_ENDPOINT` can override the default local DynamoDB endpoint (`http://localhost:8000`).

## AWS deployment

Install the Node.js dependencies, then deploy from this directory:

```sh
npm ci
npx serverless deploy
```

The service uses the configured AWS credentials and deploys a Python 3.12 Lambda plus a stage-specific DynamoDB table. Python requirements are bundled by Serverless; `dockerizePip` requires Docker to be available during packaging. Use `npx serverless info` to print the deployed endpoint URLs.