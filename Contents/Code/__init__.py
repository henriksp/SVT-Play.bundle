# -*- coding: utf-8 -*

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
            sum = pageElement.xpath("//div[@class='playVideoInfo']/span[2]/text()")
            summary = ""
            if (len(sum) > 0):
                summary = unicode(sum[0])

            imgUrl = ""
            try:
                #Find the image for the show
                category = pageElement.xpath("//div[@class='playCategoryInfo']/p/a/text()")[0]
                Log(category)
                url = URL_SITE + cat2url[category] + "&antal=500"
                Log(url)
                pe = HTML.ElementFromURL(url)
                imgUrl = pe.xpath("//article[@data-title='%s']//img/@data-imagename" % showName)
                # Regional News has it's own category for images but not in the general view on the page
                if len(imgUrl) == 0 and category == "Nyheter":
                    url = URL_SITE + cat2url["Regionala"] + "&antal=500"
                    pe = HTML.ElementFromURL(url)
                    imgUrl = pe.xpath("//article[@data-title='%s']//img/@data-imagename" % showName)
                imgUrl = imgUrl[0]
            except:
                Log("Error looking for image for show %s" % showName)
                pass

            # I need to unicode it to save it in the Dict
            imgUrl = unicode(imgUrl)
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

def MakeShowContainer(epUrls, title1="", title2=""):

    epList = ObjectContainer(title1=title1, title2=title2)

    for epUrl in epUrls:
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)

    return epList

def GetEpisodeUrls(showUrl=None, maxEp=500):

    suffix = "sida=1&antal=%d" % maxEp
    page = HTML.ElementFromURL(showUrl)
    link = page.xpath("//a[@class='playShowMoreButton playButton ']/@data-baseurl")

    if len(link) > 0 and 'klipp' not in link[0]: #If we can find the page with all episodes in, use it
        epPageUrl = URL_SITE + link[0] + suffix
        epPage = HTML.ElementFromURL(epPageUrl)
        epUrls = epPage.xpath("//div[@class='playDisplayTable']/a/@href")
    else: #Use the episodes on the base page
        epUrls = page.xpath("//div[@class='playDisplayTable']/a/@href")

    return [URL_SITE + url for url in epUrls if "video" in url]

def GetShowEpisodes(prevTitle=None, showUrl=None, showName=""):
    epUrls = GetEpisodeUrls(showUrl)
    return MakeShowContainer(epUrls, prevTitle, showName)

def GetLatestNews(prevTitle):
    epUrls = GetEpisodeUrls(showUrl=URL_LATEST_NEWS, maxEp=15)
    return MakeShowContainer(epUrls, prevTitle, TEXT_LATEST_NEWS)

def GetLatestShows(prevTitle):
    epUrls = GetEpisodeUrls(showUrl=URL_LATEST_SHOWS, maxEp=30)
    return MakeShowContainer(epUrls, prevTitle, TEXT_LATEST_NEWS)

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
       title = page.xpath("//div[@class='playVideoInfo']//h2/text()")[0]
       description = page.xpath("//div[@class='playVideoInfo']/p/text()")[0].strip()

       try:
           air_date = page.xpath("//div[@class='playVideoInfo']//time")[0].get("datetime")
           air_date = air_date.split('+')[0] #cut off timezone info as python can't parse this
           air_date = Datetime.ParseDate(air_date)
       except:
           Log.Exception("Error converting airdate: " + air_date)
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
