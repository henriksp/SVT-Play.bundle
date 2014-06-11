# -*- coding: utf-8 -*
import re, htmlentitydefs, datetime, time
# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION = "7"
PLUGIN_PREFIX = "/video/svt"

# URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
URL_LIVE = URL_SITE
URL_LATEST_CLIPS = URL_SITE + "/?tab=senasteklipp&sida=4"
URL_CHANNELS = URL_SITE + "/kanaler"
URL_PROGRAMS = URL_SITE + "/ajax/sok/forslag.json"
URL_RECOMMENDED = URL_SITE + "/?tab=rekommenderat&sida=3"
URL_SEARCH      = URL_SITE + "/sok?q=%s"

#Öppet arkiv
URL_OA_SITE = "http://www.oppetarkiv.se"
URL_OA_INDEX = "http://www.oppetarkiv.se/kategori/titel"

#Texts
TEXT_CHANNELS = u'Kanaler'
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_PREFERENCES = u'Inställningar'
TEXT_TITLE = u'SVT Play'
TEXT_LATEST_SHOWS = u'Senaste program'
TEXT_OA = u"Öppet arkiv"
TEXT_CATEGORIES = u"Kategorier"
TEXT_INDEX_ALL = u'Alla Program'
TEXT_SEARCH = u"Sök"
TEXT_RECOMMENDED = u"Rekommenderat"
TEXT_SEARCH_RESULT = u"Sökresultat"
TEXT_SEARCH_RESULT_ERROR = u"Hittade inga resultat för: '%s'"
TEXT_CLIPS = u"Klipp"
TEXT_EPISODES = u"Avsnitt"
TEXT_SEASON = u"Säsong %s"

ART = 'art-default.jpg'
ICON = 'icon-default.png'
OA_ICON = 'category_oppet_arkiv.png'

CACHE_1H = 60 * 60
CACHE_1DAY = CACHE_1H * 24
CACHE_30DAYS = CACHE_1DAY * 30

SHOW_SUM = "showsum"
DICT_V = 1

categories = {u'Barn':'barn', u'Dokumentär':'dokumentar', u'Film & Drama':'filmochdrama', \
              u'Kultur & Nöje':'kulturochnoje', u'Nyheter':'nyheter', \
              u'Samhälle & Fakta':'samhalleochfakta', u'Sport':'sport'}

cat2thumb = {u'Barn':'category_barn.png', \
             u'Dokumentär':'icon-default.png', \
             u'Film & Drama':'category_film_och_drama.png', \
             u'Kultur & Nöje':'category_kultur_och_noje.png', \
             u'Nyheter':'category_nyheter.png', \
             u'Samhälle & Fakta':'category_samhalle_och_fakta.png', \
             u'Sport':'category_sport.png'}

cat2url= {u'Barn':'/barn', \
             u'Dokumentär':'/dokumentar', \
             u'Film & Drama':'/filmochdrama', \
             u'Kultur & Nöje':'/kulturochnoje', \
             u'Nyheter':'/nyheter', \
             u'Samhälle & Fakta':'/samhalleochfakta', \
             u'Sport':'/sport'}

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def Start():

    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)

    HTTP.CacheTime = 600

    if not "version" in Dict:
        Log("No version number in dict, resetting")
        Dict.Reset()
        Dict["version"] = DICT_V
        Dict.Save()

    if Dict["version"] != DICT_V:
        Log("Wrong version number in dict, resetting")
        Dict.Reset()
        Dict["version"] = DICT_V
        Dict.Save()

    if not SHOW_SUM in Dict:
        Log("No summary dictionary, creating")
        Dict[SHOW_SUM] = {}
        Dict.Save()

    Thread.Create(HarvestShowData)

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@handler('/video/svt', TEXT_TITLE, thumb=ICON, art=ART)
def MainMenu():

    menu = ObjectContainer(title1=TEXT_TITLE)
    menu.add(DirectoryObject(key=Callback(GetIndexShows, prevTitle=TEXT_TITLE), title=TEXT_INDEX_SHOWS, thumb=R('main_index.png')))
    menu.add(DirectoryObject(key=Callback(GetCategories, prevTitle=TEXT_TITLE), title=TEXT_CATEGORIES, thumb=R('main_kategori.png')))
    menu.add(DirectoryObject(key=Callback(GetChannels, prevTitle=TEXT_TITLE), title=TEXT_CHANNELS, thumb=R('main_kanaler.png')))
    menu.add(DirectoryObject(key=Callback(GetLiveShows, prevTitle=TEXT_TITLE), title=TEXT_LIVE_SHOWS, thumb=R('main_live.png')))
    menu.add(DirectoryObject(key=Callback(GetOAIndex, prevTitle=TEXT_TITLE), title=TEXT_OA, thumb=R(OA_ICON)))
    menu.add(DirectoryObject(key=Callback(GetAllIndex, prevTitle=TEXT_TITLE), title=TEXT_INDEX_ALL, thumb=R('icon-default.png')))
    menu.add(DirectoryObject(key=Callback(GetLatestShows, prevTitle=TEXT_TITLE), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    menu.add(DirectoryObject(key=Callback(GetRecommendedEpisodes, prevTitle=TEXT_TITLE), title=TEXT_RECOMMENDED, thumb=R('main_rekommenderat.png')))
    menu.add(InputDirectoryObject(key=Callback(Search),title = TEXT_SEARCH, prompt=TEXT_SEARCH, thumb = R('search.png')))
    Log(VERSION)

    return menu


#------------ CATEGORY FUNCTIONS ---------------------

def GetCategories(prevTitle):
    catList = ObjectContainer(title1=prevTitle, title2=TEXT_CATEGORIES)
    keys = categories.keys()
    keys.sort()
    for key in keys:
        d = DirectoryObject(key=Callback(GetCategoryShows, key=key, prevTitle=TEXT_CATEGORIES), \
                title=key, thumb=R(cat2thumb[key]))
        catList.add(d)

    return catList

def GetCategoryShows(prevTitle, key):
    showsList = ObjectContainer(title1=prevTitle, title2=key)

    pageElement = HTML.ElementFromURL(URL_SITE + cat2url[key])
    xpath = "//div[@id='playJs-alphabetic-list']//article/a"
    programLinks = pageElement.xpath(xpath)

# For 'nyheter, there is no good common limiter of the articles.
# try another xpath
    if len(programLinks) == 0:
        xpath = "//div[@id='playJs-title-pages']//article/a"
        programLinks = pageElement.xpath(xpath)

    Log(len(programLinks))
    l = []

    for programLink in programLinks:
        name = programLink.xpath(".//span[@class='play-link-sub']/text()")[0].strip()
        url = URL_SITE + programLink.xpath("./@href")[0]
        showkey = Callback(GetShowEpisodes, prevTitle=key, showUrl=url, showName=name)
        l.append(CreateShowDirObject(name, showkey))
        Log(name)

    for s in l:
        showsList.add(s)
    return showsList

#------------ SHOW FUNCTIONS ---------------------
def GetAllIndex(prevTitle, title2=TEXT_INDEX_ALL, titleFilter=None):
    showsList = GetIndexShows(prevTitle, title2, titleFilter)
    for p in GetOAIndex(prevTitle, titleFilter).objects:
        showsList.add(p)
    showsList.objects.sort(key=lambda obj: obj.title)
    return showsList

#------------ SEARCH ---------------------
def Search (query):
    if len(query) == 1:
        oc = SearchShowTitle(query)
        if len(oc) > 0:
            return oc
        else:
            return MessageContainer(
                TEXT_SEARCH_RESULT,
                TEXT_SEARCH_RESULT_ERROR % query
                )

    orgQuery = query
    query = String.Quote(query.replace(' ', '+'))

    showXpath    = "//div[@id='search-titles']/div/div/article"
    episodeXpath = "//div[@id='search-episodes']/div/div/article"
    clipXpath    = "//div[@id='search-clips']/div/div/article"
    oaXpath      = "//div[@id='search-oppetarkiv']/div/div/article"
    searchUrl    = URL_SEARCH % query
    showOc       = SearchShowTitle(orgQuery)

    searchElement = HTML.ElementFromURL(searchUrl)
    showHits      = len(searchElement.xpath(showXpath)) + len(showOc)
    episodeHits   = len(searchElement.xpath(episodeXpath))
    clipHits      = len(searchElement.xpath(clipXpath))
    oaHits        = len(searchElement.xpath(oaXpath))

    typeHits     = 0
    if showHits  > 0:
        typeHits = typeHits+1
    if episodeHits > 0:
        typeHits = typeHits+1
    if clipHits > 0:
        typeHits = typeHits+1
    if oaHits > 0:
        typeHits = typeHits+1

    if typeHits == 0:
        return MessageContainer(
            TEXT_SEARCH_RESULT,
            TEXT_SEARCH_RESULT_ERROR % orgQuery
            )
    else:
        result = ObjectContainer(title1=TEXT_TITLE, title2=TEXT_SEARCH)
        if episodeHits > 0:
            result = ReturnSearchHits(searchUrl, episodeXpath, result, TEXT_EPISODES, typeHits > 1)
        if clipHits > 0:
            result = ReturnSearchHits(searchUrl, clipXpath, result, TEXT_CLIPS, typeHits > 1)
        if oaHits > 0:
            result = ReturnSearchHits(searchUrl, oaXpath, result, TEXT_OA, typeHits > 1)
        if showHits > 0:
            result = ReturnSearchShows(searchUrl, showXpath, result, showOc)
        return result

def ReturnSearchShows(url, xpath, result, showOc=[]):

    showPage = HTML.ElementFromURL(url)

    for article in showPage.xpath(xpath):
        name = article.get("data-title")
        showUrl = URL_SITE + article.xpath("./div/a/@href")[0]
        key = Callback(GetShowEpisodes, prevTitle=TEXT_TITLE, showUrl=showUrl, showName=name)
        showOc.add(CreateShowDirObject(name, key))

    showOc.objects.sort(key=lambda obj: obj.title)
    # Add unique Shows to result
    previousTitle = None
    for show in showOc.objects:
        if show.title != previousTitle:
            previousTitle = show.title
            result.add(show)
        elif "GetOAShowEpisodes" in show.key:
            # Currently SVT doesn't search OA for show name. So always add them
            result.add(show)
    return result

def ReturnSearchHits(url, xpath, result, directoryTitle, createDirectory=False):
    if createDirectory:
        if directoryTitle == TEXT_OA:
            thumb = R(OA_ICON)
        else:
            thumb = R(ICON)
        result.add(CreateDirObject(directoryTitle, Callback(ReturnSearchHits,url=url, xpath=xpath, result=None, directoryTitle=directoryTitle), thumb))
        return result
    else:
        page = HTML.ElementFromURL(url)
        epList = ObjectContainer(title1=TEXT_TITLE, title2=TEXT_SEARCH + " - " + directoryTitle)
        for clipObj in GetEpisodeObjects(page.xpath(xpath), None, stripShow=False, addUrlPrefix=(directoryTitle!=TEXT_OA)):
            epList.add(clipObj)

        return epList

def CreateDirObject(name, key, thumb=R(ICON), summary=None):
    myDir         = DirectoryObject()
    myDir.title   = name
    myDir.key     = key
    myDir.summary = summary
    myDir.thumb   = thumb
    myDir.art     = R(ART)
    return myDir

def CreateShowDirObject(name, key):
    return CreateDirObject(name, key, GetShowImgUrl(name), GetShowSummary(name))

def SearchShowTitle (query):
    return GetAllIndex(TEXT_TITLE, TEXT_SEARCH, unicode(query))

#------------ SHOW FUNCTIONS ---------------------
def GetIndexShows(prevTitle="", title2=TEXT_INDEX_SHOWS, titleFilter=None):

    showsList = ObjectContainer(title1=prevTitle, title2=title2)
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//a[@class='play_alphabetic-link play_h4']")
    for s in CreateShowList(programLinks, title2):
        if FilterTitle(s.title, titleFilter):
            showsList.add(s)

    return showsList

# This function wants a <a>..</a> tag list
def CreateShowList(programLinks, parentTitle=None):

    showsList = []

    for programLink in programLinks:
        try:
            url = URL_SITE + programLink.get("href")
            name = programLink.xpath("./text()")[0].strip()
            key = Callback(GetShowEpisodes, prevTitle=parentTitle, showUrl=url, showName=name)
            showsList.append(CreateShowDirObject(name, key))
        except:
            Log("Error creating show: "+programLink.get("href"))
            pass

    return showsList

def GetShowSummary(showName):
    d = Dict[SHOW_SUM]
    showName = unicode(showName)
    if showName in d:
        return d[showName][1]
    return ""

def GetShowImgUrl(showName):
    d = Dict[SHOW_SUM]
    showName = unicode(showName)
    if showName in d:
        return d[showName][3]
    return None

def HarvestShowData():
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//a[@class='play_alphabetic-link play_h4']")
    json_obj = JSON.ObjectFromURL(URL_PROGRAMS)

    for programLink in programLinks:
        try:
            showURL = URL_SITE + programLink.get("href")
            showName = unicode(programLink.xpath("./text()")[0].strip())

            d = Dict[SHOW_SUM]
            if showName in d:
                td = Datetime.Now() - d[showName][2]
                if td.days < 30:
                    Log("Got cached data for %s" % showName)
                    continue
            else:
                Log("no hit for %s" % showName)

            pageElement = HTML.ElementFromURL(showURL)

            #Find the summary for the show
            sum = unescapeHTML(pageElement.xpath('//meta[@property="og:description"]/@content')[0])
            summary = ""
            if (len(sum) > 0):
                summary = unicode(sum.strip())

            imgUrl = ""
            try:
                print json_obj
                for show in json_obj:
                    if showName == show['title']:
                        # I need to unicode it to save it in the Dict
                        imgUrl = unicode(show['thumbnail'])
            except:
                Log("Error looking for image for show %s" % showName)
                pass

            t = Datetime.TimestampFromDatetime(Datetime.Now())
            d[showName] = (showName, summary, Datetime.Now(), imgUrl)

            #To prevent this thread from stealing too much network time
            #we force it to sleep for every new page it loads
            Dict[SHOW_SUM] = d
            Dict.Save()
            Thread.Sleep(1)
        except:
            Log("Error harvesting show data: " + programLink.get('href'))
            pass

def MakeShowContainer(showUrl, title1="", title2="", sort=False, addClips=True, maxEps=500):
    epList = ObjectContainer(title1=title1, title2=title2)
    resultList = ObjectContainer(title1=title1, title2=title2)

    page = HTML.ElementFromURL(showUrl)
    articles = page.xpath("//div[@id='playJs-more-episodes']/div/article[contains(concat(' ',@class,' '),' playJsInfo-Core ')]")

    for epObj in GetEpisodeObjects(articles, title2, stripShow=sort):
        epList.add(epObj)

    if addClips:
        page = HTML.ElementFromURL(showUrl)
        if len(page.xpath("//div[@id='playJs-more-clips']/div/article[contains(concat(' ',@class,' '),' playJsInfo-Core ')]")) > 0:
            clips = DirectoryObject(key=Callback(GetAjaxClipsContainer, clipUrl=showUrl, title1=title2, title2=TEXT_CLIPS, sort=sort), title=TEXT_CLIPS)
            resultList.add(clips)
        for ep in epList.objects:
            resultList.add(ep)
        return resultList
    else:
        return epList

def GetAjaxClipsContainer(clipUrl, title1, title2, sort=False):
    clipList = ObjectContainer(title1=title1, title2=title2)

    page = HTML.ElementFromURL(clipUrl)
    articles = page.xpath("//div[@id='playJs-more-clips']/div/article[contains(concat(' ',@class,' '),' playJsInfo-Core ')]")

    for clipObj in GetEpisodeObjects(articles, title1, stripShow=sort):
        clipList.add(clipObj)

    return clipList

def GetClipsContainer(clipUrls, title1, title2):
    clipList = ObjectContainer(title1=title1, title2=title2)
    for url in clipUrls:
        clipObj = GetEpisodeObject(url)
        clipList.add(clipObj)
    return clipList

def GetShowUrls(showUrl=None, maxEp=100):
    suffix        = "sida=1&antal=%d" % maxEp
    page          = HTML.ElementFromURL(showUrl)
    ajaxLinks     = page.xpath("//div[@class='playBoxContainer']//a/@data-baseurl")
    links         = page.xpath("//div[@class='playDisplayTable']/a/@href")
    epAjaxUrl = None
    clipAjaxUrl = None
    epUrls = []
    clipUrls = []

    for link in ajaxLinks:
        if "/videos?" in link:
            epAjaxUrl = URL_SITE + link + suffix

        elif "/klipp?" in link:
            clipAjaxUrl = URL_SITE + link + suffix

        elif "/live" in link:
            Log("No handling for live links here at the moment")

    for link in links:
        if "/video" in link:
            epUrls.append(URL_SITE + link)
        elif "/klipp" in link:
            clipUrls.append(URL_SITE + link)

    return (epAjaxUrl, clipAjaxUrl, epUrls, clipUrls)

@route('/video/svt/episodes/{prevTitle}', 'GET')
def GetShowEpisodes(prevTitle=None, showUrl=None, showName=""):
    return MakeShowContainer(showUrl, prevTitle, showName)

def MakeGroupContainer(articleList, prevTitle, title):
    channelsList = ObjectContainer(title1=prevTitle, title2=title)
    for article in articleList:
        url = URL_SITE + article.xpath("./a/@href")[0]
        title = article.get("data-title")
        desc = article.get("data-description")
        thumb = article.xpath(".//img/@src")[0]
        Log(thumb)

        show = EpisodeObject(
                url = url,
                title = title,
                summary = desc,
                thumb = thumb)
        channelsList.add(show)

    return channelsList

def GetLatestShows(prevTitle):
    page = HTML.ElementFromURL(URL_SITE, cacheTime = 0)
    articles = page.xpath("//div[@id='playJs-latest-videos']//article")
    return MakeGroupContainer(articles, prevTitle, TEXT_LATEST_SHOWS)

def GetRecommendedEpisodes(prevTitle=None):
    page = HTML.ElementFromURL(URL_SITE, cacheTime = 0)
    articles = page.xpath("//div[@id='playJs-popular-videos']//article")
    return MakeGroupContainer(articles, prevTitle, TEXT_RECOMMENDED)

def GetChannels(prevTitle):
    page = HTML.ElementFromURL(URL_CHANNELS, cacheTime = 0)
    shows = page.xpath("//div[contains(concat(' ',@class,' '),' play_zapper')]//a")
    thumbBase = "/public/images/channels/backgrounds/%s-background.jpg"
    channelsList = ObjectContainer(title1=prevTitle, title2=TEXT_CHANNELS)

    for show in shows:
        channel = show.get("data-channel")
        if channel == None:
            continue
        url = URL_CHANNELS + '/' + channel
        desc = None
        thumb = None

        if thumb == None:
            thumb = URL_SITE + thumbBase % channel

        title = show.xpath(".//span[@class='play_zapper__menu__item-title']/text()")[0]

        timestring = ""
# Try to convert the time values to something readable
        try:
            timeDiv = show.xpath(".//div[@class='play_progressbar__value playJsSchedule-Progress']")[0]
            starttime = timeDiv.get("data-starttime")
            endtime = timeDiv.get("data-endtime")
            s = int(starttime)/1000
            e = int(endtime)/1000
            ss = time.strftime('%H:%M', time.localtime(s))
            es = time.strftime('%H:%M', time.localtime(e))
            timestring = " - (%s - %s)" % (ss, es)
        except:
            pass

        if 'svt' in channel:
            channel = channel.upper()
        else:
            channel = channel.capitalize()

        show = EpisodeObject(
                url = url,
                title = channel + " - " + title + timestring,
                summary = desc,
                thumb = thumb)
        channelsList.add(show)
    return channelsList

def GetLiveShows(prevTitle):
    page = HTML.ElementFromURL(URL_LIVE, cacheTime=0)
    showsList = ObjectContainer(title1=prevTitle, title2=TEXT_LIVE_SHOWS)
    liveshows = page.xpath("//div[@id='playJs-live-channels']//a")

    for a in liveshows[0:3]:
        url = a.get("href")
        url = URL_SITE + url
        showsList.add(GetLiveEpisodeObject(url, GetLiveShowTitle(a)))

    return showsList

def GetLiveShowTitle(a):
    times = a.xpath(".//time/text()")
    timeText = " - ".join(times)
    showName = a.xpath(".//span[@class='play-link-sub']/text()")[0]
    showName = trimShowName(showName)
    return timeText + " " + showName

def GetLiveEpisodeObject(url, title):
    page = HTML.ElementFromURL(url, cacheTime=0)
    show = page.xpath("//h1[@class='play_h2 playx_color-white']/text()")[0]
    description = unescapeHTML(page.xpath('//meta[@property="og:description"]/@content')[0])
    duration = 0
    thumb =  page.xpath("//div[@class='playVideoBox']//a[@id='player']//img/@src")[0]

    try:
        air_date = page.xpath("//div[@class='playBoxConnectedToVideoMain']//time")[0].get("datetime")
        air_date = air_date.split('+')[0] #cut off timezone info as python can't parse this
        air_date = Datetime.ParseDate(air_date)
    except:
        Log.Exception("Error converting airdate")
        air_date = None

    return EpisodeObject(
           url = url,
           show = show,
           title = title,
           summary = description,
           duration = duration,
           thumb = thumb,
           art = thumb,
           originally_available_at = air_date
           )

def GetEpisodeObject(url):
    try:
       page = HTML.ElementFromURL(url)

       show = page.xpath("//h1[@class='playVideoBoxHeadline-Inner']/text()")[0]
       title = unescapeHTML(page.xpath('//meta[@property="og:title"]/@content')[0].split(' | ')[0])
       description = unescapeHTML(page.xpath('//meta[@property="og:description"]/@content')[0])

       try:
           air_date = page.xpath("//div[@class='playBoxConnectedToVideoMain']//time")[0].get("datetime")
           air_date = air_date.split('+')[0] #cut off timezone info as python can't parse this
           air_date = Datetime.ParseDate(air_date)
       except:
           Log.Exception("Error converting airdate")
           air_date = None

       try:
           duration = page.xpath("//div[@class='playVideoInfo']//span//strong/../text()")[3].split()[0]
           duration = int(duration) * 60 * 1000 #millisecs
       except:
           duration = None

       thumb =  page.xpath("//div[@class='playVideoBox']//a[@id='player']//img/@src")[0]

       return EpisodeObject(
               url = url,
               show = show,
               title = title,
               summary = description,
               duration = duration,
               thumb = thumb,
               art = thumb,
               originally_available_at = air_date
             )

    except:
        Log.Exception("An error occurred while attempting to retrieve the required meta data.")

#------------ EPISODE FUNCTIONS ---------------------
# Excpects a list of arcticle tags
def GetEpisodeObjects(articles, showName, stripShow=False, addUrlPrefix=True):
    resultList = []

    for article in articles:
        url = article.xpath("./a/@href")[0]
        if addUrlPrefix:
            url = URL_SITE + url
        show = showName
        title = article.get("data-title")
        summary = unescapeHTML(article.get("data-description"))
        duration = dataLength2millisec(article.get("data-length"))
        thumb = article.xpath(".//img/@data-imagename")[0]
        art = thumb

        try:
           air_date = article.get("data-broadcasted")
           if len(air_date) == 0:
               air_date = article.get("data-published")
           air_date = airDate2date(air_date)
        except:
           Log.Exception("Error converting airdate")
           air_date = None

        resultList.append(EpisodeObject(
            url = url,
            show = show,
            title = title,
            summary = summary,
            duration = duration,
            thumb = thumb,
            art = art,
            originally_available_at = air_date))

    return resultList

def dataLength2millisec(dataLength):
    durationList = dataLength.split()
    i = 0
    sec = 0
    if len(durationList) > 1:
        while (i < len(durationList)):
            if durationList[i+1] == "h":
                sec = sec + (int(durationList[i]) * 3600)
            elif durationList[i+1] == "min":
                sec = sec + (int(durationList[i]) * 60)
            elif durationList[i+1] == "sek":
                sec = sec + int(durationList[i])
            i = i + 2
        return int(sec) * 1000
    elif durationList == []:
        return None
    else:
        return int(durationList[0]) * 1000

#------------OPEN ARCHIVE FUNCTIONS ---------------------
def GetOAIndex(prevTitle, titleFilter=None):
    showsList = ObjectContainer(title1 = prevTitle, title2=TEXT_OA)
    pageElement = HTML.ElementFromURL(URL_OA_INDEX)
    programLinks = pageElement.xpath("//a[@class='svt-text-default']")
    for s in CreateOAShowList(programLinks, TEXT_OA):
        if FilterTitle(s.title, titleFilter):
            showsList.add(s)
    return showsList

def CreateOAShowList(programLinks, parentTitle=None):
    showsList = []
    for l in programLinks:
        try:
            showUrl = l.get("href")
            # Log("ÖA: showUrl: " + showUrl)
            showName = (l.xpath("text()")[0]).strip()
            # Log("ÖA: showName: " + showName)
            show = DirectoryObject(thumb=R(OA_ICON))
            show.title = showName
            show.key = Callback(GetOAShowEpisodes, prevTitle=parentTitle, showUrl=showUrl, showName=showName)
            showsList.append(show)
        except:
            Log(VERSION)
            pass

    return showsList

def GetOAShowEpisodes(prevTitle=None, showUrl=None, showName=""):
    episodes = ObjectContainer()
    suffix = "?sida=%d&sort=tid_fallande&embed=true"
    i = 1
    morePages = True
    seasons = []
    # index 0 contains Season number - the rest of the indices contains urls to episodes of that season.
    seasons_episodes = []
    while morePages:
        pageElement = HTML.ElementFromURL(showUrl + (suffix % i))
        epUrls = pageElement.xpath("//div[@class='svt-display-table-xs']//h3/a/@href")
        for url in epUrls:
            if "-sasong-" in url:
                index = re.sub(".*-sasong-([0-9]+).*", "\\1", url)
                if not index in seasons:
                    # New Season - add it
                    seasons.append(index)
                    seasons_episodes.append([index])
                    ep_index = len(seasons_episodes)-1
                else:
                    # Find index handling current season
                    ep_index = 0
                    for ix in seasons_episodes:
                        if ix[0] == index:
                            break
                        ep_index += 1
                seasons_episodes[ep_index].append(url)
                continue
            else:
                eo = GetOAEpisodeObject(url)
                if eo != None:
                    episodes.add(eo)
        nextPage = pageElement.xpath("//a[@data-target='.svtoa-js-searchlist']")
        i = i + 1
        if len(nextPage) == 0:
            morePages = False
    sortOnAirData(episodes)

    if len(seasons) > 0:
        newOc = ObjectContainer(title1=prevTitle, title2=showName)
        seasons_len = len(seasons)
        seasons.sort(key=lambda obj: int(obj))
        seasons_episodes.sort(key=lambda obj: int(obj[0]))
        while seasons_len > 0:
            newOc.add(DirectoryObject(key=Callback(GetOASeasonEpisode, urlList=seasons_episodes[seasons_len-1], prevTitle=prevTitle, showName=showName), title = TEXT_SEASON % str(seasons[seasons_len-1]), thumb=R(ICON)))
            seasons_len = seasons_len - 1
        for ep in episodes.objects:
            newOc.add(ep)
        return newOc

    return episodes

# @route(PLUGIN_PREFIX + '/GetOASeasonEpisode', 'GET')
def GetOASeasonEpisode(urlList=[], prevTitle="", showName=""):
    episodes = ObjectContainer(title1=prevTitle, title2=showName+" - "+TEXT_SEASON % urlList[0])
    skip=True
    for url in urlList:
        if skip:
            skip = False
            # First index contains season number
            continue
        eo = GetOAEpisodeObject(url, stripTitlePrefix=True)
        if eo != None:
            episodes.add(eo)
    # sortOnAirData(episodes) - seems "offical" plugin don't want this...
    return episodes

def GetOAEpisodeObject(url, stripTitlePrefix=False):
    try:
        page= HTML.ElementFromURL(url)

        show = None
        title = page.xpath('//meta[@property="og:title"]/@content')[0].split(' | ')[0].replace('&amp;', '&')
        title = String.DecodeHTMLEntities(title)

        if ' - ' in title:
            (show, title) = title.split(' - ', 1)

        if "-sasong-" in url:
            season = int(re.sub(".+-sasong-([0-9]+).+", "\\1", url))
        else:
            season = None

        if "-avsnitt-" in url:
            episode = int(re.sub(".+-avsnitt-([0-9]+).+", "\\1", url))
        else:
            episode = None

        if stripTitlePrefix and "Avsnitt" in title:
            title = re.sub(".*(Avsnitt.+)", "\\1", title)

        summary = page.xpath('//meta[@property="og:description"]/@content')[0].replace('&amp;', '&')
        summary = String.DecodeHTMLEntities(summary)
        thumb = page.xpath('//meta[@property="og:image"]/@content')[0].replace('/small/', '/large/')

        try:
            air_date = page.xpath("//span[@class='svt-video-meta']//time/@datetime")[0].split('T')[0]
            air_date = Datetime.ParseDate(air_date).date()
        except:
            air_date = None
        try:
            duration = page.xpath("//a[@id='player']/@data-length")
            duration = int(duration[0]) * 1000
        except:
            duration = None
            pass
        return EpisodeObject(
                url = url,
                show = show,
                title = title,
                summary = summary,
                art = thumb,
                thumb = thumb,
                duration = duration,
                season = season,
                index = episode,
                originally_available_at = air_date)

    except:
        Log(VERSION)
        Log("Exception occurred parsing url " + url)

def airDate2date(dateString):
    if len(dateString) == 0:
        return None

    year  = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day   = datetime.datetime.now().day
    dateString = re.sub("[^0-9]*([0-9]+.+)", "\\1", dateString).split(' ')
    if len(dateString) == 3:
        (year, month, day) = convertFullAirDate(dateString)
    elif len(dateString) == 2:
        (month, day) = convertMonthAirDate(dateString)
    return datetime.date(year, month, day)

def convertFullAirDate(date):
    (month, day) = convertMonthAirDate([date[0], date[1]])
    return (int(date[2]), month, day)

def convertMonthAirDate(date):
    return (month2int(unicode(date[1]).lower()), int(date[0]))

def month2int(month):

    if month == "jan" or month == "januari":
        return 1
    elif month == "feb" or month == "februari":
        return 2
    elif month == "mar" or month == "mars":
        return 3
    elif month == "apr" or month == "april":
        return 4
    elif month == "maj" or month == "maj":
        return 5
    elif month == "jun" or month == "juni":
        return 6
    elif month == "jul" or month == "juli":
        return 7
    elif month == "aug" or month == "augusti":
        return 8
    elif month == "sep" or month == "september":
        return 9
    elif month == "okt" or month == "oktober":
        return 10
    elif month == "nov" or month == "november":
        return 11
    elif month == "dec" or month == "december":
        return 12

#------------MISC FUNCTIONS ---------------------
def FilterTitle(title, titleFilter):
    if not titleFilter:
        return True

    if len(titleFilter) == 1:
        # In case of single character - only compare initial character.
        return titleFilter.lower() == title[0].lower()
    elif len(titleFilter) > 1:
        return titleFilter.lower() in title.lower()

def unescapeHTML(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

def sortOnAirData(Objects):
    for obj in Objects.objects:
        if obj.originally_available_at == None:
            return Objects.objects.reverse()
    return Objects.objects.sort(key=lambda obj: (obj.originally_available_at,obj.title))

def trimShowName(showName):
    showName = showName.strip().split()
    for i in showName:
        i.strip()
    showName = " ".join(showName)
    return showName
