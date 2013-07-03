# -*- coding: utf-8 -*
import re, htmlentitydefs

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="7"
PLUGIN_PREFIX	= "/video/svt"

# URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
URL_LIVE = URL_SITE + "/?tab=live&sida=1"
URL_LATEST_SHOWS = URL_SITE + "/?tab=episodes&sida=1"
URL_LATEST_NEWS = URL_SITE + "/?tab=news&sida=1"
URL_CHANNELS = URL_SITE + "/kanaler"
URL_PROGRAMS = URL_SITE + "/ajax/program.json"
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

ART = 'art-default.jpg'
ICON = 'icon-default.png'

CACHE_1H = 60 * 60
CACHE_1DAY = CACHE_1H * 24
CACHE_30DAYS = CACHE_1DAY * 30

SHOW_SUM = "showsum"
DICT_V = 1

categories = {u'Barn':'barn', u'Dokumentär':'dokumentar', u'Film & Drama':'filmochdrama', \
              u'Kultur & Nöje':'kulturochnoje', u'Nyheter':'nyheter', \
              u'Samhälle & Fakta':'samhalleochfakta', u'Sport':'sport' }

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
    menu.add(DirectoryObject(key=Callback(GetChannels, prevTitle=TEXT_TITLE), title=TEXT_CHANNELS,
        thumb=R('main_kanaler.png')))
    menu.add(DirectoryObject(key=Callback(GetLiveShows, prevTitle=TEXT_TITLE), title=TEXT_LIVE_SHOWS, thumb=R('main_live.png')))
    menu.add(DirectoryObject(key=Callback(GetOAIndex, prevTitle=TEXT_TITLE), title=TEXT_OA,
        thumb=R('category_oppet_arkiv.png')))
    menu.add(DirectoryObject(
        key=Callback(GetLatestNews, prevTitle=TEXT_TITLE), title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png')))
    menu.add(DirectoryObject(
        key=Callback(GetLatestShows, prevTitle=TEXT_TITLE), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    menu.add(DirectoryObject(key=Callback(GetCategories, prevTitle=TEXT_TITLE), title=TEXT_CATEGORIES,
        thumb=R('main_kategori.png')))
    menu.add(DirectoryObject(key=Callback(GetAllIndex, prevTitle=TEXT_TITLE), title=TEXT_INDEX_ALL,
        thumb=R('icon-default.png')))
    menu.add(InputDirectoryObject(key=Callback(SearchShow),title = TEXT_SEARCH_SHOW, prompt=TEXT_SEARCH_SHOW,
        thumb = R('search.png')))

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
def SearchShow (query):
    query = unicode(query)
    oc = ObjectContainer(title1='SVT-Play', title2='Search Results')
    for video in GetAllIndex('Searching').objects:
        if len(query) == 1 and query.lower() == video.title[0].lower():
            # In case of single character - only compare initial character.
            oc.add(video)
        elif len(query) > 1 and query.lower() in video.title.lower():
            oc.add(video)

    if len(oc) == 0:
        return MessageContainer(
            "Search results",
            "Did not find any result for '%s'" % query
            )
    else:
        return oc

#------------ SHOW FUNCTIONS ---------------------
def GetIndexShows(prevTitle):
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
            showUrl = URL_SITE + programLink.get("href")
            showName = programLink.xpath("./text()")[0].strip()
            show = DirectoryObject()
            show.title = showName
            show.key = Callback(GetShowEpisodes, prevTitle=parentTitle, showUrl=showUrl, showName=showName)
            show.thumb = GetShowImgUrl(showName)
            show.summary = GetShowSummary(showName)
            showsList.append(show)
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

def MakeShowContainer(epUrls, title1="", title2="", sort = 0):
    epList      = ObjectContainer(title1=title1, title2=title2)
    resultList  = ObjectContainer(title1=title1, title2=title2)
    clipUrls    = []

    for epUrl in epUrls:
        if "/klipp" in epUrl:
            clipUrls.append(epUrl)
        elif "/video" in epUrl:
            epList.add(GetEpisodeObject(epUrl))
            
    if sort == 1:
        sortOnAirData(epList)
        if len(clipUrls) > 0:
            clip       = DirectoryObject()
            clip.title = "Klipp"
            clip.key   = Callback(ReturnClips,urls=clipUrls,title1=title1,title2=title2)
            clip.thumb = R(ICON)
            clip.art   = R(ART)
            resultList.add(clip)
            for ep in epList.objects:
                resultList.add(ep)
            return resultList
        else:
            return epList
    else:
        return epList

def ReturnClips(urls=None, title1="", title2=""):
    clipList = ObjectContainer(title1=title1, title2=title2)
    for url in urls:
        clipList.add(GetEpisodeObject(url))
    sortOnAirData(clipList)
    return clipList

def GetShowUrls(showUrl=None, maxEp=500, addClips=True):

    suffix = "sida=1&antal=%d" % maxEp
    page   = HTML.ElementFromURL(showUrl)
    link   = page.xpath("//a[@class='playShowMoreButton playButton ']/@data-baseurl")

    # If we can find the page with all episodes in, use it
    if len(link) > 0 and '/klipp' not in link[0]: 
        epUrls = GetShowUrlsHelp(URL_SITE + link[0] + suffix)
        i = 1;
        while (i < len(link)):
            if addClips and '/klipp' in link[i]:
                epUrls = epUrls + GetShowUrlsHelp(URL_SITE + link[i] + suffix)
            i = i + 1
    else: #Use the episodes on the base page
        epUrls = page.xpath("//div[@class='playDisplayTable']/a/@href")

    if addClips:
        return ([URL_SITE + url for url in epUrls if "/video" in url] +
                [URL_SITE + url for url in epUrls if "/klipp" in url])
    else:
        return [URL_SITE + url for url in epUrls if "/video" in url]

def GetShowUrlsHelp(url):
    epPage = HTML.ElementFromURL(url)
    return epPage.xpath("//div[@class='playDisplayTable']/a/@href")

def GetShowEpisodes(prevTitle=None, showUrl=None, showName=""):
    epUrls = GetShowUrls(showUrl)
    return MakeShowContainer(epUrls, prevTitle, showName, 1)

def GetLatestNews(prevTitle):
    epUrls = GetShowUrls(showUrl=URL_LATEST_NEWS, maxEp=15, addClips=False)
    return MakeShowContainer(epUrls, prevTitle, TEXT_LATEST_NEWS)

def GetLatestShows(prevTitle):
    epUrls = GetShowUrls(showUrl=URL_LATEST_SHOWS, maxEp=30, addClips=False)
    return MakeShowContainer(epUrls, prevTitle, TEXT_LATEST_SHOWS)

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
        showsList.add(GetEpisodeObject(url))

    return showsList

#------------ EPISODE FUNCTIONS ---------------------
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
           if "klipp" in url:
               duration = page.xpath("//div[@class='playVideoInfo']//span//strong/../text()")[2].split()
           else:
               duration = page.xpath("//div[@class='playVideoInfo']//span//strong/../text()")[3].split()
           duration = duration2sec(duration) * 1000 #millisecs
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

def duration2sec(durationList):
    i   = 0
    sec = 0
    while (i < len(durationList)):
        if durationList[i+1] == "h":
            sec = sec + (int(durationList[i]) * 3600)
        elif durationList[i+1] == "min":
            sec = sec + (int(durationList[i]) * 60)
        elif durationList[i+1] == "sek":
            sec = sec + int(durationList[i])
        i = i + 2
    return int(sec)

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
    pageElement = HTML.ElementFromURL(showUrl)
    epUrls = pageElement.xpath("//div[@class='svt-display-table-xs']//h3/a/@href")
    for url in epUrls:
        eo = GetOAEpisodeObject(url)
        if eo != None:
            episodes.add(eo)
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
