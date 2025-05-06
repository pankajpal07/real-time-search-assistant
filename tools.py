import requests
import os
from tavily import TavilyClient

GREY = '\033[90m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
NORMAL = '\033[0m'

def search_internet(query: str):
    print(f'{GREY}SEARCHING: {query}{NORMAL}')

    client = TavilyClient(os.getenv('TAVILY_API_KEY'))
    response = client.search(
        query=query,
        include_raw_content=True
    )
    print(response)
    return response


    # response = requests.get(f"https://api.search.brave.com/res/v1/web/search?q={query}&count=10", headers={ 'X-Subscription-Token': os.getenv('BRAVE_API_KEY') })
    # if response.status_code == 200:
    #     # print(response.json())
    #     return response.json()
    # else:
    #     print(f"{RED}Error: {response.status_code}{NORMAL}")
    #     return None