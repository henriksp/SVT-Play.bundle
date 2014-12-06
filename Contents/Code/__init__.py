# -*- coding: utf-8 -*
import re, htmlentitydefs, datetime, time
# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION = "9"
PLUGIN_PREFIX = "/video/svt"

# URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
URL_CHANNELS = URL_SITE + "/kanaler"
URL_PROGRAMS = URL_SITE + "/ajax/sok/forslag.json"
URL_SEARCH      = URL_SITE + "/sok?q=%s"

#Öppet arkiv
URL_OA_LABEL = "oppetarkiv"
URL_OA_SITE = "http://www.%s.se" % URL_OA_LABEL
URL_OA_INDEX = "http://www.oppetarkiv.se/kategori/titel"

#Texts
TEXT_CHANNELS = u'Kanaler'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_PREFERENCES = u'Inställningar'
TEXT_TITLE = u'SVT Play'
TEXT_OA = u"Öppet arkiv"
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

sec2thumb = {u"Kategorier": "main_kategori.png", \
             u"Kanaler" : "main_kanaler.png", \
             u"Live" : "main_live.png", \
             u"Senaste program" : "main_senaste_program.png", \
             u"Rekommenderat" : "main_rekommenderat.png"
            }

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
    menu.add(DirectoryObject(key=Callback(GetIndexShows, prevTitle=TEXT_TITLE), title=TEXT_INDEX_SHOWS,thumb=R('main_index.png')))
    menu.add(DirectoryObject(key=Callback(GetChannels, prevTitle=TEXT_TITLE), title=TEXT_CHANNELS,thumb=R('main_kanaler.png')))
    menu = AddSections(menu)
    menu.add(DirectoryObject(key=Callback(GetRecommendedEpisodes, prevTitle=TEXT_TITLE), title="Rekommenderat", thumb=R('main_rekommenderat.png')))
    menu.add(DirectoryObject(key=Callback(GetAllIndex, prevTitle=TEXT_TITLE), title=TEXT_INDEX_ALL,thumb=R('icon-default.png')))
    menu.add(InputDirectoryObject(key=Callback(Search),title = TEXT_SEARCH, prompt=TEXT_SEARCH, thumb = R('search.png')))
    Log(VERSION)

    return menu

#------------ SECTIONS FUNCTIONS ---------------------

def AddSections(menu):

    try:
        pageElement = HTML.ElementFromURL(URL_SITE)
        xpath = "//section[contains(concat(' ',@class,' '),' play_js-hovered-list')]"
        index = 0
        for section in pageElement.xpath(xpath):
            title = section.xpath(".//h1[contains(concat(' ',@class,' '),' play_videolist-section-header__header')]/a/span/text()")
            if (len(title) == 0):
                title = section.xpath(".//h1[contains(concat(' ',@class,' '),' play_videolist-section-header__header')]/a/text()")
            if (len(title) == 0):
                continue;
            title = '/'.join(title)

            img = ICON
            try:
                img = sec2thumb[title]
            except:
                pass

            menu.add(DirectoryObject(key=Callback(GetSectionEpisodes, index=index, prevTitle=TEXT_TITLE, title=title), title=title, thumb=R(img)))
            index = index + 1
    except Exception as e:
        Log.Exception("AddSections failed:%s" % e)
    return menu

def GetSectionEpisodes(index, prevTitle, title):
    oc = ObjectContainer(title1=prevTitle, title2=title)

    pageElement = HTML.ElementFromURL(URL_SITE, cacheTime=0)
    xpath = "//section[contains(concat(' ',@class,' '),' play_js-hovered-list')]"
    section = pageElement.xpath(xpath)[index]
    articles = section.xpath(".//article")
    if articles[0].get("data-title"):
        oc = GetEpisodeObjects(oc, articles, showName=None)
    else:
        for article in articles:
            url = URL_SITE + article.xpath("./a/@href")[0]
            thumb = URL_SITE + article.xpath(".//img/@src")[0]
            title = article.xpath("./a/@title")[0].strip()
            # Nasty hack for OA in categories...
            if url == URL_SITE + "/%s" % URL_OA_LABEL:
                oc.add(DirectoryObject(key=Callback(GetOAIndex, prevTitle=prevTitle), title=title, thumb=thumb))
            else:
                oc.add(DirectoryObject(key=Callback(GetSectionShows, url=url, prevTitle=prevTitle, title=title), title=title, thumb=thumb))

    return oc

def GetSectionShows(url, prevTitle, title):
    oc = ObjectContainer(title1=prevTitle, title2=title)
    page = HTML.ElementFromURL(url)
    articles = page.xpath("//div[@id='playJs-alphabetic-list']//article")
    # For 'nyheter, there is no good common limiter of the articles.
    # try another xpath
    if len(articles) == 0:
        articles = page.xpath("//div[@id='playJs-title-pages']//article")
    for article in articles:
        showUrl = URL_SITE + article.xpath("./a/@href")[0]
        name = article.get("data-title")
        oc.add(CreateShowDirObject(name, key=Callback(GetShowEpisodes, prevTitle=prevTitle, showUrl=showUrl, showName=name)))

    return oc

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
        result = ObjectContainer(title1=TEXT_TITLE, title2=TEXT_SEARCH + " '%s'" % unicode(orgQuery))
        if episodeHits > 0:
            result = ReturnSearchHits(searchUrl, episodeXpath, result, "%s(%i)" % (TEXT_EPISODES,episodeHits), typeHits > 1)
        if clipHits > 0:
            result = ReturnSearchHits(searchUrl, clipXpath, result, "%s(%i)" % (TEXT_CLIPS,clipHits), typeHits > 1)
        if oaHits > 0:
            result = ReturnSearchHits(searchUrl, oaXpath, result, "%s(%i)" % (TEXT_OA,oaHits), typeHits > 1)
        if showHits > 0:
            result = ReturnSearchShows(searchUrl, showXpath, result, showOc)
        return result

def ReturnSearchShows(url, xpath, result, showOc=[]):

    showPage = HTML.ElementFromURL(url)

    for article in showPage.xpath(xpath):
        name = article.get("data-title")
        showUrl = URL_SITE + article.xpath("./a/@href")[0]
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
        if TEXT_OA in directoryTitle:
            thumb = R(OA_ICON)
        else:
            thumb = R(ICON)
        result.add(CreateDirObject(directoryTitle, Callback(ReturnSearchHits,url=url, xpath=xpath, result=None, directoryTitle=directoryTitle), thumb))
        return result
    else:
        page = HTML.ElementFromURL(url)
        epList = ObjectContainer(title1=TEXT_TITLE, title2=TEXT_SEARCH + " - " + directoryTitle)
        return GetEpisodeObjects(epList, page.xpath(xpath), None, stripShow=False, addUrlPrefix=(not TEXT_OA in directoryTitle))

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
    return GetAllIndex(TEXT_TITLE, 
                       TEXT_SEARCH + " '%s'" % unicode(query), 
                       unicode(query)
                       )

#------------ SHOW FUNCTIONS ---------------------
def GetIndexShows(prevTitle="", title2=TEXT_INDEX_SHOWS, titleFilter=None):

    showsList = ObjectContainer(title1=prevTitle, title2=title2)
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//li[@class='play_js-filterable-item']")
    for s in CreateShowList(programLinks, title2):
        if FilterTitle(s.title, titleFilter):
            showsList.add(s)

    return showsList

# This function wants a <a>..</a> tag list
def CreateShowList(programLinks, parentTitle=None):

    showsList = []

    for programLink in programLinks:
        try:
            url = URL_SITE + programLink.xpath("./a/@href")[0]
            name = programLink.xpath("./a/text()")[0].strip()
            key = Callback(GetShowEpisodes, prevTitle=parentTitle, showUrl=url, showName=name)
            showsList.append(CreateShowDirObject(name, key))
        except Exception as e:
            Log("Error creating show: %s %s" % (programLink.xpath("./a/@href")[0],e))
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
    programLinks = pageElement.xpath("//li[@class='play_js-filterable-item']")
    json_obj = JSON.ObjectFromURL(URL_PROGRAMS)

    for programLink in programLinks:
        try:
            showURL = URL_SITE + programLink.xpath("./a/@href")[0]
            showName = unicode(programLink.xpath("./a/text()")[0].strip())

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
            sum = pageElement.xpath("//div[@id='video-info-panel-1']/p/text()")
            summary = ""
            if (len(sum) > 0 and len(sum[0]) > 0):
                summary = unicode(unescapeHTML(sum[0].strip()))
            imgUrl = ""
            try:
                print json_obj
                for show in json_obj:
                    if showName == show['title']:
                        # I need to unicode it to save it in the Dict
                        imgUrl = unicode(show['thumbnail'])
            except Exception as e:
                Log("Error looking for image for show %s %s" % (showName, e))
                pass

            d[showName] = (showName, summary, Datetime.Now(), imgUrl)

            #To prevent this thread from stealing too much network time
            #we force it to sleep for every new page it loads
            Dict[SHOW_SUM] = d
            Dict.Save()
            Thread.Sleep(1)
        except Exception as e:
            Log("Error harvesting show data: %s %s" % (programLink.get('href'), e))
            pass

def MakeShowContainer(showUrl, title1="", title2="", sort=False, addClips=True, maxEps=500):
    title2 = unicode(title2)
    epList = ObjectContainer(title1=title1, title2=title2)
    resultList = ObjectContainer(title1=title1, title2=title2)

    page = HTML.ElementFromURL(showUrl)
    articles = page.xpath("//div[@id='playJs-more-episodes']/div/article[contains(concat(' ',@class,' '),' playJsInfo-Core ')]")

    epList = GetEpisodeObjects(epList, articles, title2, stripShow=sort)

    if addClips:
        page = HTML.ElementFromURL(showUrl)
        if len(page.xpath("//div[@id='playJs-more-clips']/div/article[contains(concat(' ',@class,' '),' playJsInfo-Core ')]")) > 0:
            clips = DirectoryObject(key=Callback(GetClipsContainer, clipUrl=showUrl, title1=title2, title2=TEXT_CLIPS, sort=sort), title=TEXT_CLIPS)
            resultList.add(clips)
        for ep in epList.objects:
            resultList.add(ep)
        return resultList
    else:
        return epList

def GetClipsContainer(clipUrl, title1, title2, sort=False):
    clipList = ObjectContainer(title1=title1, title2=unicode(title2))

    page = HTML.ElementFromURL(clipUrl)
    articles = page.xpath("//div[@id='playJs-more-clips']/div/article[contains(concat(' ',@class,' '),' playJsInfo-Core ')]")

    clipList = GetEpisodeObjects(clipList, articles, title1, stripShow=sort)

    if sort:
        sortOnAirData(clipList)

    return clipList

def GetRecommendedEpisodes(prevTitle=None):

    oc = ObjectContainer(title1=prevTitle, title2=TEXT_RECOMMENDED)

    page = HTML.ElementFromURL(URL_SITE)
    articles = page.xpath("//section[@id='recommended-videos']//article")
    for article in articles:
        url = article.xpath("./a/@href")[0]
        show = None
        title = GetFirstNonEmptyString(article.xpath(".//span[@class='play_carousel-caption__title-inner']/text()"))
        summary = GetFirstNonEmptyString(article.xpath("./a/span/span[2]/text()"))
        if summary: summary = unescapeHTML(summary)
        thumb = article.xpath(".//img/@data-imagename")[0]
        art = thumb

        tmp = title.split(" - ", 1)
        if len(tmp) > 1:
            show = tmp[0]

        if not "http" in url:
            oc.add(EpisodeObject(
                    url = URL_SITE + url,
                    show = show,
                    title = title,
                    summary = summary,
                    thumb = thumb,
                    art = art))
        else:
            # Assume Show
            oc.add(CreateShowDirObject(title, key=Callback(GetShowEpisodes, prevTitle=prevTitle, showUrl=url, showName=title)))

    return oc

def GetFirstNonEmptyString(stringList):
    string = None
    index = 0
    while index < len(stringList):
        string = stringList[index].strip()
        if len(string) > 0:
            break
        else:
            string = None
            index = index + 1
    return string

@route('/video/svt/episodes/{prevTitle}', 'GET')
def GetShowEpisodes(prevTitle=None, showUrl=None, showName=""):
    return MakeShowContainer(showUrl, prevTitle, showName)

def GetChannels(prevTitle):
    page = HTML.ElementFromURL(URL_CHANNELS, cacheTime = 0)
    shows = page.xpath("//div[contains(concat(' ',@class,' '),'play_channels__active-video-info')]")
    thumbBase = "/public/images/channels/backgrounds/%s-background.jpg"
    channelsList = ObjectContainer(title1=prevTitle, title2=TEXT_CHANNELS)

    for show in shows:
        channel = show.get("data-channel")
        if channel == None:
            continue
        url = URL_CHANNELS + '/' + channel
        desc = None
        thumb = None
        duration = None

        if thumb == None:
            thumb = URL_SITE + thumbBase % channel

        title = show.xpath(".//h1/text()")[0]

        timestring = ""
# Try to convert the time values to something readable
        try:
            timeDiv = show.xpath(".//div[@class='play_progressbar__value--alt play_js-schedule__progressbar__progress playJsSchedule-Progress']")[0]
            starttime = timeDiv.get("data-starttime")
            endtime = timeDiv.get("data-endtime")
            s = int(starttime)/1000
            e = int(endtime)/1000
            ss = time.strftime('%H:%M', time.localtime(s))
            es = time.strftime('%H:%M', time.localtime(e))
            timestring = " - (%s - %s)" % (ss, es)
        except:
            pass

        try:
            desc = show.xpath(".//p[contains(concat(' ',@class,' '),'-show-description')]/text()")[0].strip()
            desc = unescapeHTML(desc)
        except:
            pass

        try:
            duration = dataLength2millisec(show.xpath(".//span[contains(concat(' ',@class,' '),'-show-duration')]/text()")[0].strip())
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
                duration = duration,
                thumb = thumb)
        channelsList.add(show)
    return channelsList

def GetLiveShowTitle(a):
    times = a.xpath(".//time/text()") # obsolete xpath?
    timeText = " - ".join(times)
    showName = a.xpath(".//span[@class='play_videolist-element__title-text']/text()")[0]
    showName = trimShowName(showName)
    return (timeText + " " + showName).strip()

#------------ EPISODE FUNCTIONS ---------------------
# Excpects a list of arcticle tags
def GetEpisodeObjects(oc, articles, showName, stripShow=False, addUrlPrefix=True):

    for article in articles:
        url = article.xpath("./a/@href")[0]
        if addUrlPrefix:
            url = URL_SITE + url
        show = showName
        if IsLive(article):
            title = GetLiveShowTitle(article)
        else:
            title = article.get("data-title")
        summary = unescapeHTML(article.get("data-description"))
        availability = unescapeHTML(article.get("data-available"))
        if len(availability) > 0:
            summary = u'Tillgänglig: ' + availability + ". \n" + summary
        duration = dataLength2millisec(article.get("data-length"))
        thumb = article.xpath(".//img/@src")[0]
        art = thumb

        if showName and stripShow and showName in title:
            title = re.sub(showName+"[ 	-]*(:[ 	-]*)*(.+)", "\\2", title)
        elif not showName:
            tmp = title.split(" - ", 1)
            if len(tmp) > 1:
                show = tmp[0]
                if stripShow:
                    title = tmp[1]

        try:
           air_date = article.get("data-broadcasted")
           if len(air_date) == 0:
               air_date = article.get("data-published")
           air_date = airDate2date(air_date)
        except Exception as e:
           Log.Exception("Error converting airdate:%s" % e)
           air_date = None

        oc.add(EpisodeObject(
                url = url,
                show = show,
                title = title,
                summary = summary,
                duration = duration,
                thumb = thumb,
                art = art,
                originally_available_at = air_date))

    return oc

def IsLive(article):
    text = article.xpath(".//span[@class='play_visually-hidden']/text()")
    return (text and "Live" in text[0])

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
        except Exception as e:
            Log(VERSION + "%s" % e)
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

    except Exception as e:
        Log(VERSION)
        Log("Exception occurred parsing %s: %s " % (url, e))

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
