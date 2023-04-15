import requests

from models import open_ai_models

try:
    with open("open_ai_key.txt", "r") as f:
        api_key = f.read()
        HEADERS = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
except FileNotFoundError:
    print("No API key found. Please create a file called 'api_key.txt' and paste your API key in it.")
    exit()

input_message = open_ai_models.Message(content="Is Wagner a good composer?")

request = open_ai_models.Request(messages=[input_message])

api_response = requests.post("https://api.openai.com/v1/chat/completions", json=request.dict(), headers=HEADERS)

if api_response.status_code == 200:
    response = open_ai_models.Response.parse_raw(api_response.text)
    print(response.choices[0].message.content)
else:
    print(api_response.text)
