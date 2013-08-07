# -*- coding: utf-8 -*
import re, htmlentitydefs, datetime
# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION = "7"
PLUGIN_PREFIX = "/video/svt"

# URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
URL_LIVE = URL_SITE + "/?tab=live&sida=1"
URL_LATEST_SHOWS = URL_SITE + "/?tab=episodes&sida=1"
URL_LATEST_CLIPS = URL_SITE + "/?tab=clips&sida=4"
URL_LATEST_NEWS = URL_SITE + "/?tab=news&sida=1"
URL_CHANNELS = URL_SITE + "/kanaler"
URL_PROGRAMS = URL_SITE + "/ajax/program.json"
URL_RECOMMENDED = URL_SITE + "/?tab=recommended&sida=500"

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
TEXT_LATEST_NEWS = u'Senaste nyhetsprogram'
TEXT_OA = u"Öppet arkiv"
TEXT_CATEGORIES = u"Kategorier"
TEXT_INDEX_ALL = u'Alla Program'
TEXT_SEARCH_SHOW = u"Sök Program"
TEXT_SEARCH_ONLINE = u"Sök Online"
TEXT_RECOMMENDED = u"Rekommenderat"
TEXT_SEARCH_RESULT = u"Sökresultat"
TEXT_SEARCH_RESULT_ERROR = u"Hittade inga resultat för: '%s'"
TEXT_CLIPS = u"Klipp"
TEXT_EPISODES = u"Avsnitt"

ART = 'art-default.jpg'
ICON = 'icon-default.png'

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

cat2url= {u'Barn':'/ajax/program?category=kids', \
             u'Dokumentär':'/ajax/program?category=documentary', \
             u'Film & Drama':'/ajax/program?category=filmAndDrama', \
             u'Kultur & Nöje':'/ajax/program?category=cultureAndEntertainment', \
             u'Nyheter':'/ajax/program?category=news', \
             u'Regionala':'/ajax/program?category=regionalNews', \
             u'Samhälle & Fakta':'/ajax/program?category=societyAndFacts', \
             u'Sport':'/ajax/program?category=sport'}

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
    menu.add(DirectoryObject(key=Callback(GetOAIndex, prevTitle=TEXT_TITLE), title=TEXT_OA, thumb=R('category_oppet_arkiv.png')))
    menu.add(DirectoryObject(key=Callback(GetAllIndex, prevTitle=TEXT_TITLE), title=TEXT_INDEX_ALL, thumb=R('icon-default.png')))
    menu.add(DirectoryObject(key=Callback(GetLatestNews, prevTitle=TEXT_TITLE), title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png')))
    menu.add(DirectoryObject(key=Callback(GetLatestShows, prevTitle=TEXT_TITLE), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    menu.add(DirectoryObject(key=Callback(GetRecommendedEpisodes, prevTitle=TEXT_TITLE), title=TEXT_RECOMMENDED, thumb=R('main_rekommenderat.png')))
    menu.add(InputDirectoryObject(key=Callback(SearchShow),title = TEXT_SEARCH_SHOW, prompt=TEXT_SEARCH_SHOW, thumb = R('search.png')))
    menu.add(InputDirectoryObject(key=Callback(SearchOnline),title = TEXT_SEARCH_ONLINE, prompt=TEXT_SEARCH_ONLINE, thumb = R('search.png')))

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
    pageElement = HTML.ElementFromURL(URL_INDEX)
    xpath = "//li[@data-category='%s']//a[@class='playAlphabeticLetterLink']" % categories[key]
    programLinks = pageElement.xpath(xpath)
    showsList = ObjectContainer(title1=prevTitle, title2=key)
    for s in CreateShowList(programLinks, key):
        showsList.add(s)

    return showsList

#------------ SHOW FUNCTIONS ---------------------
def GetAllIndex(prevTitle):

    showsList = ObjectContainer(title1 = prevTitle, title2=TEXT_INDEX_ALL)
    indexPageElement = HTML.ElementFromURL(URL_INDEX)
    indexProgramLinks = indexPageElement.xpath("//a[@class='playAlphabeticLetterLink']")
    for s in CreateShowList(indexProgramLinks, TEXT_INDEX_ALL):
        showsList.add(s)

    oaPageElement = HTML.ElementFromURL(URL_OA_INDEX)
    oaProgramLinks = oaPageElement.xpath("//a[@class='svt-text-default']")
    for p in CreateOAShowList(oaProgramLinks, TEXT_INDEX_ALL):
        showsList.add(p)
    showsList.objects.sort(key=lambda obj: obj.title)
    return showsList

#------------ SEARCH ---------------------
def SearchOnline (query):
    query = String.Quote(query.replace(' ', '+'))

    showQuery    = "http://www.svtplay.se/ajax/sok/program?q="+query+"&antal=500"
    episodeQuery = "http://www.svtplay.se/ajax/sok/avsnitt?q="+query+"&antal=500"
    clipQuery    = "http://www.svtplay.se/ajax/sok/klipp?q="+query+"&antal=500"
    oaQuery      = "http://www.oppetarkiv.se/sok/?q="+query+"&embed=true"
    showHits     = GetNumberOfEpisodes(showQuery)
    episodeHits  = GetNumberOfEpisodes(episodeQuery)
    clipHits     = GetNumberOfEpisodes(clipQuery)
    oaHits       = len(HTML.ElementFromURL(oaQuery).xpath("//figure[@class='svtMediaBlockFig-M']"))
    typeHits     = 0
    if showHits > 0:
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
            TEXT_SEARCH_RESULT_ERROR % query
            )
    else:
        result = ObjectContainer(title1=TEXT_TITLE, title2=TEXT_SEARCH_ONLINE)
        if episodeHits > 0:
            result = ReturnSearchHits(episodeQuery, result, TEXT_EPISODES, typeHits > 1)
        if clipHits > 0:
            result = ReturnSearchHits(clipQuery, result, TEXT_CLIPS, typeHits > 1)
        if oaHits > 0:
            result = ReturnSearchOaHits(oaQuery, result, TEXT_OA, typeHits > 1)
        if showHits > 0:
            result = ReturnSearchShows(showQuery, result)
        return result

def ReturnSearchShows(url, result):
    showHits  = GetNumberOfEpisodes(url)
    showPage  = HTML.ElementFromURL(url)
    urls      = showPage.xpath("//div[@class='playDisplayTable']/a/@href")
    titles    = showPage.xpath("//article[contains(concat(' ',@class,' '),' svtUnit ')]/@data-title")
    i=0
    while (i < showHits):
        name = titles[i]
        key = Callback(GetShowEpisodes, prevTitle=TEXT_TITLE, showUrl=URL_SITE+urls[i*2], showName=name)
        result.add(CreateShowDirObject(name, key))
        i = i+1
    return result

def ReturnSearchHits(url, result, directoryTitle, createDirectory=False):
    if createDirectory:
        result.add(CreateDirObject(directoryTitle, Callback(ReturnSearchHits,url=url, result=None, directoryTitle=directoryTitle)))
        return result
    else:
        epList = MakeShowContainer(url, TEXT_TITLE, TEXT_SEARCH_ONLINE + " - " + directoryTitle, True)
        sortOnAirData(epList)
        epList.objects.sort(key=lambda obj: obj.show)
        return epList

def ReturnSearchOaHits(url, result, directoryTitle, createDirectory=False):
    if createDirectory:
        result.add(CreateDirObject(directoryTitle, Callback(ReturnSearchOaHits,url=url, result=None, directoryTitle=directoryTitle)))
        return result
    else:
        oaList = ObjectContainer(title1=TEXT_TITLE, title2=TEXT_SEARCH_ONLINE + " - " + directoryTitle)
        i = 1
        morePages = True
        while morePages:
            page = HTML.ElementFromURL(url + ("&sida=%d" % i))
            oaList = CreateOaSearchHitObjects(oaList, page)
            nextPage = page.xpath("//a[@data-target='.svtoa-js-searchlist']")
            i = i + 1
            if len(nextPage) == 0:
                morePages = False
        return oaList

def CreateOaSearchHitObjects(resultList, page):

    numberOfHits = len(page.xpath("//figure[@class='svtMediaBlockFig-M']"))
    urls   = page.xpath("//figure[@class='svtMediaBlockFig-M']/a/@href")
    titles = page.xpath("//figure[@class='svtMediaBlockFig-M']/..//h2//a/text()")
    thumbs = page.xpath("//figure[@class='svtMediaBlockFig-M']//img/@src")
    air_summarys = page.xpath("//figure[@class='svtMediaBlockFig-M']/..//p/@class/../text()")
    i = 0
    while (i < numberOfHits):
        show = None
        if ' - ' in titles[i]:
            (show, dummy) = titles[i].split(' - ', 1)
        try:
            air_date = airDate2date(air_summarys[(i*2)+1])
        except:
            air_date = None
        thumb = thumbs[i].replace('/small/', '/large/')
        resultList.add(EpisodeObject(url     = urls[i],
                                     show    = show,
                                     title   = titles[i],
                                     summary = String.DecodeHTMLEntities(air_summarys[i*2]),
                                     art     = thumb,
                                     thumb   = thumb,
                                     originally_available_at = air_date))
        i = i + 1
    return resultList

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

def SearchShow (query):
    query = unicode(query)
    oc = ObjectContainer(title1=TEXT_TITLE, title2='Search Show Results')
    for video in GetAllIndex('Searching').objects:
        if len(query) == 1 and query.lower() == video.title[0].lower():
            # In case of single character - only compare initial character.
            oc.add(video)
        elif len(query) > 1 and query.lower() in video.title.lower():
            oc.add(video)

    if len(oc) == 0:
        return MessageContainer(
            TEXT_SEARCH_RESULT,
            TEXT_SEARCH_RESULT_ERROR % query
            )
    else:
        return oc

#------------ SHOW FUNCTIONS ---------------------
def GetIndexShows(prevTitle="", query=None):

    showsList = ObjectContainer(title1=prevTitle, title2=TEXT_INDEX_SHOWS)
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//a[@class='playAlphabeticLetterLink']")
    for s in CreateShowList(programLinks, TEXT_INDEX_SHOWS):
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
    programLinks = pageElement.xpath("//a[@class='playAlphabeticLetterLink']")
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
            sum = pageElement.xpath("//div[@class='playBoxConnectedToVideoAside playJsShowMoreSubContainer']/p/text()")
            summary = ""
            if (len(sum) > 0):
                summary = unicode(sum[0].strip())

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

def MakeShowContainer(showUrl, title1="", title2="", sort=False):
    epList = ObjectContainer(title1=title1, title2=title2)
    (epsUrl, clipsUrl, epUrls, clipUrls) = GetShowUrls(showUrl)

    if clipsUrl:
        clips = DirectoryObject(key=Callback(GetAjaxClipsContainer, clipUrl=clipsUrl, title1=title2, title2=TEXT_CLIPS), title=TEXT_CLIPS)
        epList.add(clips)
    else:
        clips = DirectoryObject(key=Callback(GetClipsContainer, clipUrls=clipUrls, title1=title2, title2=TEXT_CLIPS), title=TEXT_CLIPS)
        epList.add(clips)

    if epsUrl:
        for epObj in GetEpisodeObjects(epsUrl, title2):
            epList.add(epObj)
    else:
        for url in epUrls:
            epObj = GetEpisodeObject(url)
            epList.add(epObj)

    return epList

def GetAjaxClipsContainer(clipUrl, title1, title2, sort=False):
    clipList = ObjectContainer(title1=title1, title2=title2)
    for clipObj in GetEpisodeObjects(clipUrl, title1):
        clipList.add(clipObj)

    return clipList

def GetClipsContainer(clipUrls, title1, title2):
    clipList = ObjectContainer(title1=title1, title2=title2)
    for url in clipUrls:
        clipObj = GetEpisodeObject(url)
        clipList.add(clipObj)
    return clipList

def GetShowUrls(showUrl=None, maxEp=500):
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

def GetNumberOfEpisodes(url):
    epPage = HTML.ElementFromURL(url)
    return len(epPage.xpath("//article[contains(concat(' ',@class,' '),' svtUnit ')]"))

def GetRecommendedEpisodes(prevTitle=None):
    return MakeShowContainer(URL_RECOMMENDED, prevTitle, TEXT_RECOMMENDED)

def GetShowEpisodes(prevTitle=None, showUrl=None, showName=""):
    return MakeShowContainer(showUrl, prevTitle, showName)

def GetLatestNews(prevTitle):
    return MakeShowContainer(URL_LATEST_NEWS, prevTitle, TEXT_LATEST_NEWS)

def GetLatestShows(prevTitle):
    return MakeShowContainer(URL_LATEST_SHOWS, prevTitle, TEXT_LATEST_SHOWS)

def GetChannels(prevTitle):
    page = HTML.ElementFromURL(URL_CHANNELS, cacheTime = 0)
    shows = page.xpath("//div[contains(concat(' ',@class,' '),' playJsSchedule-SelectedEntry ')]")
    thumbBase = "/public/images/channels/backgrounds/%s-background.jpg"
    channelsList = ObjectContainer(title1=prevTitle, title2=TEXT_CHANNELS)

    for show in shows:
        channel = show.get("data-channel")
        if channel == None:
            continue
        url = URL_CHANNELS + '/' + channel
        desc = show.get("data-description")
        thumb = show.get("data-titlepage-poster")
        if thumb == None:
            thumb = URL_SITE + thumbBase % channel

        title = show.get("data-title")
        airing = show.xpath(".//time/text()")[0]

        if 'svt' in channel:
            channel = channel.upper()
        else:
            channel = channel.capitalize()

        show = EpisodeObject(
                url = url,
                title = channel + " - " + title + ' (' + airing + ')',
                summary = desc,
                thumb = thumb)
        channelsList.add(show)
    return channelsList

def GetLiveShows(prevTitle):
    page = HTML.ElementFromURL(URL_LIVE, cacheTime=0)
    liveshows = page.xpath("//img[@class='playBroadcastLiveIcon']//../..")
    showsList = ObjectContainer(title1=prevTitle, title2=TEXT_LIVE_SHOWS)

    for a in liveshows:
        url = a.get("href")
        url = URL_SITE + url
        showsList.add(GetLiveEpisodeObject(url))

    return showsList

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
def GetEpisodeObjects(epsUrl, showName):
    resultList = []
    page = HTML.ElementFromURL(epsUrl)
    articles = page.xpath("//article")

    for article in articles:
        url = article.xpath("./div[@class='playDisplayTable']/a[contains(concat(' ', @class, ' '), 'playBoxWithClickArea')]/@href")[0]
        url = URL_SITE + url
        show = showName
        title = article.get("data-title")
        summary = article.get("data-description")
        duration = dataLength2millisec(article.get("data-length"))
        thumb = article.xpath(".//img/@data-imagename")[0]
        art = thumb

        try:
           air_date = article.xpath(".//time/@datetime")[0]
           air_date = air_date.split('+')[0] #cut off timezone info as python can't parse this
           air_date = Datetime.ParseDate(air_date)
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
def GetOAIndex(prevTitle):
    showsList = ObjectContainer(title1 = prevTitle, title2=TEXT_OA)
    pageElement = HTML.ElementFromURL(URL_OA_INDEX)
    programLinks = pageElement.xpath("//a[@class='svt-text-default']")
    for s in CreateOAShowList(programLinks, TEXT_OA):
        showsList.add(s)
    return showsList

def CreateOAShowList(programLinks, parentTitle=None):
    showsList = []
    for l in programLinks:
        try:
            showUrl = l.get("href")
            Log("ÖA: showUrl: " + showUrl)
            showName = (l.xpath("text()")[0]).strip()
            Log("ÖA: showName: " + showName)
            show = DirectoryObject()
            show.title = showName
            show.key = Callback(GetOAShowEpisodes, prevTitle=parentTitle, showUrl=showUrl, showName=showName)
            showsList.append(show)
        except:
            Log(VERSION)
            pass

    return showsList

def GetOAShowEpisodes(prevTitle, showUrl, showName):
    episodes = ObjectContainer()
    suffix = "?sida=%d&sort=tid_fallande&embed=true"
    i = 1
    morePages = True
    while morePages:
        pageElement = HTML.ElementFromURL(showUrl + (suffix % i))
        epUrls = pageElement.xpath("//div[@class='svt-display-table-xs']//h3/a/@href")
        for url in epUrls:
            eo = GetOAEpisodeObject(url)
            if eo != None:
                episodes.add(eo)
        nextPage = pageElement.xpath("//a[@data-target='.svtoa-js-searchlist']")
        i = i + 1
        if len(nextPage) == 0:
            morePages = False
    sortOnAirData(episodes)
    return episodes

def GetOAEpisodeObject(url):
    try:
        page= HTML.ElementFromURL(url)

        show = None
        title = page.xpath('//meta[@property="og:title"]/@content')[0].split(' | ')[0].replace('&amp;', '&')
        title = String.DecodeHTMLEntities(title)

        if ' - ' in title:
            (show, title) = title.split(' - ', 1)

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
                originally_available_at = air_date)

    except:
        Log(VERSION)
        Log("Exception occurred parsing url " + url)

def airDate2date(dateString):
    Log("JTDEBUG dateString %s" % dateString)
    year  = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day   = datetime.datetime.now().day
    dateString = re.sub("[^0-9]*([0-9]+.+)", "\\1", dateString).split(' ')
    Log("JTDEBUG dateString %s" % dateString)
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
