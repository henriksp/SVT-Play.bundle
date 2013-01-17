# -*- coding: utf-8 -*

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
PLUGIN_PREFIX = "/video/svt"
VERSION="3.2b4"

#URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
URL_LIVE = URL_SITE + "?tab=live&sida=1"
URL_LATEST_SHOWS = URL_SITE + "?tab=episodes&sida=1"
URL_LATEST_NEWS = URL_SITE + "?tab=news&sida=1"

#Texts
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_TITLE = u'SVT Play'
TEXT_PREFERENCES = u'Inställningar'
TEXT_LATEST_SHOWS = u'Senaste program'
TEXT_LATEST_NEWS = u'Senaste nyhetsprogram'

#The page step function will only step this many pages deep. Can be changed / function call.
MAX_PAGINATE_PAGES = 5

ART = 'art-default.jpg'
THUMB = 'icon-default.png'

CACHE_TIME_SHORT = 60*10 # 10  minutes
CACHE_TIME_1DAY = 60*60*24
CACHE_TIME_SHOW = CACHE_TIME_1DAY

#Prefs settings
PREF_PAGINATE_DEPTH = 'paginate_depth'

def GetPaginateUrls(url, dataname="pr", baseurl=None):
    pageElement = HTML.ElementFromURL(url)
    xpath = "//div[@class='playBoxContainer']//a//@data-lastpage"
    urls = []
    args = "?%s=%d"

    try:
        noPages = int(pageElement.xpath(xpath)[0])
    except IndexError:
        noPages = 1
        Log("No data-lastpage found. Assuming only one page ..")

    if baseurl != None:
        url = baseurl

    for i in range(1, min(MAX_PAGINATE_PAGES, noPages + 1)):
        suburl = url + args % (dataname, i)
        urls.append(suburl)

    return urls
