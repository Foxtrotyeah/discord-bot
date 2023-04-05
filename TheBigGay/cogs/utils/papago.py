import requests
from urllib.parse import urlencode


URL = "https://papago-extension.herokuapp.com/api/v1/detect?"


def translate(text: str) -> tuple[str, str]:
    params = {
        'target': "en",
        'text': text,
        'honorific': "false"
    }
    query = urlencode(params)

    r = requests.get(URL + query)
    if r.status_code == 200:
        json = r.json()
        result = json['message']['result']

        return result['translatedText'], result['srcLangType']
    else:
        r.raise_for_status()
