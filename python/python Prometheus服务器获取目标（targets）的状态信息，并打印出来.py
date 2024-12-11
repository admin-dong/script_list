
import requests


def print_targets(targets):
    index = 1
    all = len(targets)
    for i in targets:
        scrapeUrl = i.get("scrapeUrl")
        state = i.get("health")
        labels = i.get("labels")
        lastScrape = i.get("lastScrape")
        lastScrapeDuration = i.get("lastScrapeDuration")
        lastError = i.get("lastError")
        if state=="up":
            up_type = "正常"
        else:
            up_type = "异常"
        msg = "状态:{} num:{}/{} endpoint:{} state:{} labels:{} lastScrape:{} lastScrapeDuration:{} lastError:{}".format(

            up_type,
            index,
            all,
            scrapeUrl,
            state,
            str(labels),
            lastScrape,
            lastScrapeDuration,
            lastError,

        )
        print(msg)
        index+=1

def get_targets(t):
    f_data = {}
    try:
        uri = 'http://{}/api/v1/targets'.format(t)
        res = requests.get(uri)

        data = res.json().get("data")
        activeTargets = data.get("activeTargets")
        droppedTargets = data.get("droppedTargets")

        ups = []
        downs = []
        print_targets(activeTargets)
        print_targets(droppedTargets)


    except Exception as e:
        print(e)


get_targets("prome-master01:9090")
