# import requests
#
# url = 'http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token'
# headers = {'Metadata-Flavor': 'Google'}
# def handler(event, context):
#     resp = requests.get(url, headers=headers)
#     return {
#         'statusCode': 200,
#         'headers': {
#             'Content-Type': 'text/plain'
#         },
#         'isBase64Encoded': False,
#         'body': resp.content.decode('UTF-8')
#     }

# def main(event, context):
#     token = context.get('token')  # Используем метод get для безопасного доступа к ключу 'token'
#     if token:
#         return {
#             'statusCode': 200,
#             'headers': {
#                 'Content-Type': 'text/plain'
#             },
#             'isBase64Encoded': False,
#             'body': token
#         }
#     else:
#         return {
#             'statusCode': 400,
#             'headers': {
#                 'Content-Type': 'text/plain'
#             },
#             'isBase64Encoded': False,
#             'body': 'Token not found in context'
#         }
#
# # Локальный тест
# if __name__ == "__main__":
#     event = {}
#     context = {'token': 'example_token'}
#     result = main(event, context)
#     print(result)
#     print(f"Body: {result['body']}")  # Выводим содержимое body
#     # Извлекаем токен из результата
#     token = result['body']
#     print(f"Extracted Token: {token}")

import requests

url = 'http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token'
headers = {'Metadata-Flavor': 'Google'}

def main(event, context):
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        token = resp.json().get('access_token')
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/plain'
            },
            'isBase64Encoded': False,
            'body': token
        }
    else:
        return {
            'statusCode': resp.status_code,
            'headers': {
                'Content-Type': 'text/plain'
            },
            'isBase64Encoded': False,
            'body': 'Failed to get IAM token'
        }

# Локальный тест
if __name__ == "__main__":
    event = {}
    context = {}
    result = main(event, context)
    print(result)