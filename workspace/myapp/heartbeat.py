import requests
import time


def callapi():
    i = 2
    while i > 0:
        time.sleep(5)
        url = "http://localhost:6005/api/call"
        data = {'status': "I am Up"}
        requests.get(url, params=data)
        i -= 1

callapi()
