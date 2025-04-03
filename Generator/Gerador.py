import random
import time
import requests

def generateTcpData():
  websites = [
      "https://www.google.com/",
      "https://www.youtube.com/",
      "https://www.facebook.com/",
      "https://twitter.com/",
      "https://www.instagram.com/",
      "https://en.wikipedia.org/wiki/Main_Page",
      "https://www.amazon.com/",
      "https://www.reddit.com/",
      "https://www.netflix.com/",
      "https://www.linkedin.com/"
  ]

  while True:
    website = random.choice(websites)
    try:
       response = requests.get(website)
       print(response, flush=True)
    except Exception as e:
        print("error:" + str(e))
    time.sleep(random.uniform(1,3))

generateTcpData()   
