import os
import re
import json
import requests
from dotenv import load_dotenv

class BeagoAI_Unofficial:
    def __init__(self) -> None:
        load_dotenv()
        self.key = os.getenv('KEY')
        self.refresh_token = os.getenv('REFRESH_TOKEN')
        self.credentials_file = 'BeagoAI.json'
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'dnt': '1',
            'origin': 'https://www.beago.ai',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        self._load_credentials()

    def _load_credentials(self):
        if not self.key or not self.refresh_token:
            raise EnvironmentError("KEY and REFRESH_TOKEN must be set in the .env file.")
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as json_file:
                    data = json.load(json_file)
                self.token = data['data']['token']
            else:
                self._handle_missing_credentials()
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self._handle_missing_credentials()

    def _handle_missing_credentials(self):
        print("Fetching new token...")
        print(self._get_token())
        self.__init__()

    def _get_token(self) -> str:
        params = {'key': self.key}
        data = {'grant_type': 'refresh_token', 'refresh_token': self.refresh_token}
        try:
            response = requests.post('https://securetoken.googleapis.com/v1/token', params=params, headers=self.headers, data=data)
            if response.status_code == 200:
                response_json_data = response.json()
                headers = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'en-US,en;q=0.9',
                    'app-name': 'beago',
                    'authorization': str(response_json_data['access_token']),
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://www.beago.ai',
                    'priority': 'u=1, i',
                    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                }
                json_data = {'authType': 'GOOGLE', 'googleToken': str(response_json_data['access_token'])}
                token_response = requests.post('https://api.beago.ai/v2/user/login', headers=headers, json=json_data)
                if token_response.status_code == 200:
                    response_json_data.update(token_response.json())
                    with open(self.credentials_file, 'w') as json_file:
                        json.dump(response_json_data, json_file, indent=4)
                    return "Token saved successfully."
            else:
                return f"Error {response.status_code}: {response.content}"
        except requests.exceptions.RequestException as e:
            return f"Request failed: {str(e)}"

    def chat(self, query: str, stream: bool = True) -> dict:
        headers = {
            'accept': 'text/event-stream',
            'accept-language': 'en-US,en;q=0.9',
            'app-name': 'beago',
            'authorization': str(self.token),
            'content-type': 'application/json',
            'dnt': '1',
            'origin': 'https://www.beago.ai',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        json_data = {
            'messages': [{'content': query.strip(), 'role': 'user'}],
            'postId': None,
            'chatType': 'SEARCH_INPUT',
        }
        try:
            response = requests.post('https://api.beago.ai/v1/chat/completions', headers=headers, json=json_data, stream=True)
            streaming_text = ""
            images = []
            quotes = []
            for value in response.iter_lines(decode_unicode=True, chunk_size=1000):
                modified_value = re.sub("data:", "", value)
                if modified_value and "[DONE]" not in modified_value:
                    try:
                        json_modified_value = json.loads(modified_value)
                        if '"finish_reason":"stop"' not in modified_value:
                            if stream:
                                print(json_modified_value['data']['choices'][0]['message']['content'], end="", flush=True)
                            streaming_text += json_modified_value['data']['choices'][0]['message']['content']
                        for image in json_modified_value['data']['dotline']['post']['images']:
                            images.append({'num': image['num'], 'url': image['url'], 'source': image['source']})
                        for quote in json_modified_value['data']['dotline']['post']['quotes']:
                            quotes.append({'num': quote['num'], 'title': quote['title'], 'website': quote['webSite']})
                    except:
                        continue
            if stream:
                print("\n")
            return {"text": streaming_text, "images": images, "quotes": quotes}
        except Exception as e:
            return {"error": str(e)}