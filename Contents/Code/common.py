# -*- coding: utf-8 -*

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="3.2b2"
PLUGIN_PREFIX	= "/video/svt"

#URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
#URL_INDEX_THUMB_PAGINATE = "?am,,%d,thumbs"
#URL_INDEX_THUMB = URL_INDEX + URL_INDEX_THUMB_PAGINATE
#URL_PLEX_PLAYER = "http://www.plexapp.com/player/player.php?&url="
URL_LIVE = URL_SITE + "/?live=1"
#URL_RECOMMENDED_SHOWS = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1364142,1,f,"
#URL_LATEST_CLIPS = "http://svtplay.se/?cb,a1364145,1,f,/pb,a1364142,1,f,-1"
URL_LATEST_SHOWS = URL_SITE + "/?ep=1"
URL_LATEST_NEWS = URL_SITE + "/?en=1"
#URL_MOST_VIEWED = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1364144,1,f,"
#URL_CATEGORIES = "http://svtplay.se/kategorier"
#URL_CAT_CHILD = "http://svtplay.se/c/96251/barn"
#URL_CAT_MOVIE_DRAMA = "http://svtplay.se/c/96257/film_och_drama"
#URL_CAT_CULTURE = "http://svtplay.se/c/96256/kultur_och_noje"
#URL_CAT_FACT = "http://svtplay.se/c/96254/samhalle_och_fakta"
#URL_CAT_NEWS = "http://svtplay.se/c/96255/nyheter"
#URL_CAT_SPORT = "http://svtplay.se/c/96253/sport"

#Texts
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_TITLE = u'SVT Play'
#TEXT_NO_INFO = u'Ingen information hittades'
TEXT_PREFERENCES = u'Inställningar'
#TEXT_RECOMMENDED_SHOWS = u'Rekommenderat'
#TEXT_LATEST_CLIPS = u'Senaste klipp'
TEXT_LATEST_SHOWS = u'Senaste program'
TEXT_LATEST_NEWS = u'Senaste nyhetsprogram'
#TEXT_MOST_VIEWED = u'Mest sedda'
#TEXT_CATEGORIES = u'Kategorier'
#TEXT_CAT_CHILD = u'Barn'
#TEXT_CAT_MOVIE_DRAMA = u'Film & Drama'
#TEXT_CAT_CULTURE = u'Kultur & Nöje'
#TEXT_CAT_FACT = u'Samhälle & Fakta'
#TEXT_CAT_NEWS = u'Nyheter'
#TEXT_CAT_SPORT = u'Sport'

#TEXT_LIVE = u'LIVE: '
#TEXT_LIVE_CURRENT = u'JUST NU: '

#The page step function will only step this many pages deep. Can be changed / function call.
MAX_PAGINATE_PAGES = 5

ART = "art-default.jpg"
THUMB = 'icon-default.png'

#CACHE_TIME_LONG    = 60*60*24*30 # Thirty days
CACHE_TIME_SHORT   = 60*10    # 10  minutes
#CACHE_TIME_1DAY    = 60*60*24
#CACHE_TIME_SHOW = CACHE_TIME_1DAY
#CACHE_TIME_EPISODE = CACHE_TIME_LONG

#Prefs settings
PREF_PAGINATE_DEPTH = 'paginate_depth'

def GetPaginateUrls(url, dataname="pr", baseurl=None):
    pageElement = HTML.ElementFromURL(url)
    xpath = "//div[@class='svtXClearFix']//ul[@data-name='%s']//@data-lastpage" % dataname
    urls = []

    try:
        noPages = int(pageElement.xpath(xpath)[0])
    except IndexError:
        return urls

    args = "?%s=%d"
    if(baseurl != None):
        url = baseurl
    for i in range(1, min(MAX_PAGINATE_PAGES, noPages + 1)):
        suburl = url + args % (dataname, i)
        urls.append(suburl)
        Log(suburl)

    return urls

def PlayVideo():
    return None
