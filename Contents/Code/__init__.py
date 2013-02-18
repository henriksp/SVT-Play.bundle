# -*- coding: utf-8 -*

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
URL_LIVE = URL_SITE + "/?tab=live&sida=1"
URL_LATEST_SHOWS = URL_SITE + "/?tab=episodes&sida=1"
URL_LATEST_NEWS = URL_SITE + "/?tab=news&sida=1"
URL_CHANNELS = URL_SITE + "/kanaler"
#Texts
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_TITLE = u'SVT Play'
TEXT_LATEST_SHOWS = u'Senaste program'
TEXT_LATEST_NEWS = u'Senaste nyhetsprogram'

ART = 'art-default.jpg'
ICON = 'icon-default.png'

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():

    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)

    HTTP.CacheTime = 600

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
@handler('/video/svt', TEXT_TITLE, thumb=ICON, art=ART)
def MainMenu():

    menu = ObjectContainer(title1=TEXT_TITLE)
    menu.add(DirectoryObject(key=Callback(GetIndexShows, prevTitle=TEXT_TITLE), title=TEXT_INDEX_SHOWS, thumb=R('main_index.png')))
    menu.add(DirectoryObject(key=Callback(GetLiveShows, prevTitle=TEXT_TITLE), title=TEXT_LIVE_SHOWS, thumb=R('main_live.png')))
    menu.add(DirectoryObject(key=Callback(GetLatestNews, prevTitle=TEXT_TITLE), title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png')))
    menu.add(DirectoryObject(key=Callback(GetLatestShows, prevTitle=TEXT_TITLE), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    return menu

#------------ SHOW FUNCTIONS ---------------------
def GetIndexShows(prevTitle):

    showsList = ObjectContainer(title1=prevTitle, title2=TEXT_INDEX_SHOWS)
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//a[@class='playAlphabeticLetterLink']")

    for s in CreateShowList(programLinks, TEXT_INDEX_SHOWS):
        showsList.add(s)

    Thread.Create(HarvestShowData, programLinks=programLinks)
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
            show.thumb = R(ICON)
            show.summary = GetShowSummary(showUrl, showName)

            showsList.append(show)
        except: 
            Log("Error creating show: "+programLink.get("href"))
            pass

    return showsList     

def GetShowSummary(url, showName):

    sumExt = ".summary"
    showSumSave = showName + sumExt

    if Data.Exists(showSumSave):
        return unicode(Data.LoadObject(showSumSave))

    return ""

def HarvestShowData(programLinks):

    sumExt = ".summary"

    for programLink in programLinks:
        try:
            showURL = URL_SITE + programLink.get("href")
            showName = programLink.xpath("./text()")[0].strip()
            pageElement = HTML.ElementFromURL(showURL, cacheTime=CACHE_1DAY)
            sum = pageElement.xpath("//div[@class='playVideoInfo']/span[2]/text()")
	    
            if (len(sum) > 0):
                showSumSave = showName + sumExt
                Data.SaveObject(showSumSave, sum[0])
        except:
            Log("Error harvesting show data: "+programLink.get("href"))
            pass

def MakeShowContainer(epUrls, title1="", title2=""):

    epList = ObjectContainer(title1=title1, title2=title2)

    for epUrl in epUrls:
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)

    return epList

def GetEpisodeUrls(showUrl=None, maxEp=1000):

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

def GetChannels():
    page = HTML.ElementFromURL(URL_CHANNELS, cacheTime = 0)
    shows = page.xpath("//div[@class='playChannelSchedule']//article[1]")
    thumbBase = "/public/images/channels/backgrounds/%s-background.jpg"
    channels = []

    for show in shows:
        channel = show.get("data-channel")
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
        channels.append(show)
    return channels

def GetLiveShows(prevTitle):
    page = HTML.ElementFromURL(URL_LIVE, cacheTime=0)
    liveshows = page.xpath("//img[@class='playBroadcastLiveIcon']//../..")
    showsList = ObjectContainer(title1=prevTitle, title2=TEXT_LIVE_SHOWS)

    channels = GetChannels()
    for c in channels:
        showsList.add(c)

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
