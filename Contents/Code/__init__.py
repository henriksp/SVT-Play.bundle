# -*- coding: utf-8 -*

import string

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="5"
PLUGIN_PREFIX	= "/video/svt"

#URLs
URL_SITE = "http://www.svtplay.se"
URL_INDEX = URL_SITE + "/program"
URL_LIVE = URL_SITE + "/?tab=live&sida=1"
URL_LATEST_SHOWS = URL_SITE + "/?tab=episodes&sida=1"
URL_LATEST_NEWS = URL_SITE + "/?tab=news&sida=1"
URL_CHANNELS = URL_SITE + "/kanaler"
#Texts
TEXT_CHANNELS = u'Kanaler'
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_TITLE = u'SVT Play'
TEXT_PREFERENCES = u'Inställningar'
TEXT_LATEST_SHOWS = u'Senaste program'
TEXT_LATEST_NEWS = u'Senaste nyhetsprogram'

#The max number of episodes to get per show
MAX_EPISODES = 1000

ART = "art-default.jpg"
THUMB = 'icon-default.png'

#CACHE_TIME_LONG    = 60*60*24*30 # Thirty days
CACHE_TIME_SHORT   = 60*10    # 10  minutes
CACHE_TIME_1DAY    = 60*60*24
CACHE_TIME_SHOW = CACHE_TIME_1DAY
#CACHE_TIME_EPISODE = CACHE_TIME_LONG

#Prefs settings
PREF_MAX_EPISODES = 'max_episodes'

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, TEXT_TITLE, "icon-default.png", "art-default.jpg")
    HTTP.CacheTime = CACHE_TIME_SHORT
    HTTP.PreCache(URL_INDEX)

    DirectoryObject.art = R(ART)
    DirectoryObject.thumb = R(THUMB)
    ObjectContainer.art = R(ART)
    EpisodeObject.art = R(ART)
    EpisodeObject.thumb = R(THUMB)
    TVShowObject.art = R(ART)
    TVShowObject.thumb = R(THUMB)

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def MainMenu():
    menu = ObjectContainer(title1=TEXT_TITLE + " " + VERSION)
    menu.add(DirectoryObject(key=Callback(GetIndexShows, prevTitle=TEXT_TITLE), title=TEXT_INDEX_SHOWS, thumb=R('main_index.png')))
    menu.add(DirectoryObject(key=Callback(GetChannels, prevTitle=TEXT_TITLE), title=TEXT_CHANNELS,
        thumb=R('main_kanaler.png')))
    menu.add(DirectoryObject(key=Callback(GetLiveShows, prevTitle=TEXT_TITLE), title=TEXT_LIVE_SHOWS, thumb=R('main_live.png')))
    menu.add(DirectoryObject(
        key=Callback(GetLatestNews, prevTitle=TEXT_TITLE), title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png')))
    menu.add(DirectoryObject(
        key=Callback(GetLatestShows, prevTitle=TEXT_TITLE), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    menu.add(PrefsObject(title=TEXT_PREFERENCES, thumb=R('icon-prefs.png')))
    Log(VERSION)
    return menu

#------------SHOW FUNCTIONS ---------------------
def GetIndexShows(prevTitle):
    showsList = ObjectContainer(title1 = prevTitle, title2=TEXT_INDEX_SHOWS)
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//a[@class='playAlphabeticLetterLink']")
    for s in CreateShowList(programLinks, TEXT_INDEX_SHOWS):
        showsList.add(s)

    #Thread.Create(HarvestShowData, programLinks = programLinks)
    return showsList

#This function wants a <a>..</a> tag list
def CreateShowList(programLinks, parentTitle=None):
    showsList = []
    for programLink in programLinks:
        try:
	    Log("showUrl")
            showUrl = URL_SITE + programLink.get("href")
            Log(showUrl)
            showName = string.strip(programLink.xpath("text()")[0])
            show = DirectoryObject()
            show.title = showName
            show.key = Callback(GetShowEpisodes, prevTitle=parentTitle, showUrl=showUrl, showName=showName)
            show.thumb = R(THUMB)
            show.summary = str(GetShowSummary(showUrl, showName))
            showsList.append(show)
        except: 
            Log(VERSION)
            pass

    return showsList     

def GetShowSummary(url, showName):
    sumExt = ".summary"
    showSumSave = showName + sumExt
    showSumSave = ReplaceSpecials(showSumSave)
    if Data.Exists(showSumSave):
        return Data.LoadObject(showSumSave)
    return ""

def HarvestShowData(programLinks):
    sumExt = ".summary"
    for programLink in programLinks:
        try:
            showURL = URL_SITE + programLink.get("href")
            showName = string.strip(programLink.xpath("text()")[0])
            pageElement = HTML.ElementFromURL(showURL, cacheTime = CACHE_TIME_1DAY)
            sum = pageElement.xpath("//div[@class='playVideoInfo']/span[2]/text()")
            Log(sum)
	    
            if (len(sum) > 0):
                showSumSave = showName + sumExt
                showSumSave = ReplaceSpecials(showSumSave)
                Data.SaveObject(showSumSave, sum[0].encode('utf-8'))
        except:
            Log(VERSION)
            pass

def MakeShowContainer(epUrls, title1="", title2=""):
    epList = ObjectContainer(title1=title1, title2=title2)
    for epUrl in epUrls:
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)
    return epList

def GetEpisodeUrls(showUrl = None, maxEp = MAX_EPISODES):
    suffix = "sida=1&antal=" + str(maxEp)
    page = HTML.ElementFromURL(showUrl)
    Log(showUrl)

    link = page.xpath("//a[@class='playShowMoreButton playButton ']/@data-baseurl")
    if len(link) > 0 and 'klipp' not in link[0]: #If we can find the page with all episodes in, use it
        epPageUrl = URL_SITE + link[0] + suffix
        epPage = HTML.ElementFromURL(epPageUrl)
        epUrls = epPage.xpath("//div[@class='playDisplayTable']/a/@href")
    else: #Use the episodes on the base page
        epUrls = page.xpath("//div[@class='playDisplayTable']/a/@href")

    return [URL_SITE + url for url in epUrls if "video" in url]

def GetShowEpisodes(prevTitle = None, showUrl = None, showName = ""):
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
    shows = page.xpath("//div[@class='playChannelSchedule']//article[1]")
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
    page = HTML.ElementFromURL(URL_LIVE, cacheTime = 0)
    liveshows = page.xpath("//img[@class='playBroadcastLiveIcon']//../..")
    showsList = ObjectContainer(title1=prevTitle, title2=TEXT_LIVE_SHOWS)

    for a in liveshows:
        url = a.xpath("@href")[0]
        url = URL_SITE + url
        showsList.add(GetEpisodeObject(url))
    return showsList
    
    for a in liveshows:
        url = a.xpath("@href")[0]
        url = URL_SITE + url
        title = a.xpath(".//h5/text()")[0]
        thumb = a.xpath(".//img[2]/@src")[0]
        Log(url)
        Log(title)
        Log(thumb)
        show = EpisodeObject(
            url = url,
            title = title,
            thumb = thumb
            )
        showsList.add(show)
    return showsList
        
#------------EPISODE FUNCTIONS ---------------------

def GetEpisodeObject(url):
    try:
        # Request the page
       page = HTML.ElementFromURL(url)

       show = page.xpath("//h1[@class='playVideoBoxHeadline-Inner']/text()")[0]
       title = page.xpath("//div[@class='playVideoInfo']//h2/text()")[0]
       description = page.xpath("//div[@class='playVideoInfo']/p/text()")[0].strip()

       air_date = ""
       try:
           air_date = page.xpath("//div[@class='playVideoInfo']//time")[0].get("datetime")
           air_date = air_date.split('+')[0] #cut off timezone info as python can't parse this
           air_date = Datetime.ParseDate(air_date)
       except:
           Log(VERSION)
           Log.Exception("Error converting airdate: " + air_date)
           air_date = Datetime.Now()
     
       try:
           duration = page.xpath("//div[@class='playVideoInfo']//span//strong/../text()")[3].split()[0]
           duration = int(duration) * 60 * 1000 #millisecs
       except:
           duration = 0
     
       thumb =  page.xpath("//div[@class='playVideoBox']//a[@id='player']//img/@src")[0]
     
       return EpisodeObject(
               url = url,
               show = show,
               title = title,
               summary = description,
               duration = duration,
               thumb = thumb,
               art = thumb,
               originally_available_at = air_date)
     
    except:
        Log(VERSION)
        Log.Exception("An error occurred while attempting to retrieve the required meta data.")

#------------MISC FUNCTIONS ---------------------

def ValidatePrefs():
    Log("Validate prefs")
    global MAX_EPISODES

    try:
         MAX_EPISODES = int(Prefs[PREF_MAX_EPISODES])
    except ValueError:
        pass

    Log("max episodes %d" % MAX_EPISODES)

def ReplaceSpecials(replaceString):
    return replaceString.encode('utf-8')

