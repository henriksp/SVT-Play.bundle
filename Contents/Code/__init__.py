# -*- coding: utf-8 -*

import string
from common import *

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, TEXT_TITLE, "icon-default.png", "art-default.jpg")
    Plugin.AddViewGroup(name="List")
    HTTP.CacheTime = CACHE_TIME_SHORT
    HTTP.PreCache(URL_INDEX)

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def MainMenu():
    menu = ObjectContainer(view_group="List", title1= TEXT_TITLE + " " + VERSION)
    menu.add(DirectoryObject(key=Callback(GetIndexShows), title=TEXT_INDEX_SHOWS, thumb=R('main_index.png')))
    menu.add(DirectoryObject(key=Callback(GetLiveShows), title=TEXT_LIVE_SHOWS, thumb=R('main_live.png')))
    #menu.Append(Function(DirectoryItem(GetRecommendedShows, title=TEXT_RECOMMENDED_SHOWS,
        #thumb=R('main_rekommenderat.png'))))
    menu.add(DirectoryObject(
        key=Callback(GetLatestNews), title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png')))
    #menu.Append(Function(DirectoryItem(GetLatestClips, title=TEXT_LATEST_CLIPS, thumb=R('main_senaste_klipp.png'))))
    menu.add(DirectoryObject(
        key=Callback(GetLatestShows), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    #menu.Append(Function(DirectoryItem(GetMostViewed, title=TEXT_MOST_VIEWED, thumb=R('main_mest_sedda.png'))))
    #menu.Append(Function(DirectoryItem(GetCategories, title=TEXT_CATEGORIES, thumb=R('main_kategori.png'))))
    #menu.Append(Function(DirectoryItem(ListLiveMenu, title=TEXT_LIVE_SHOWS, thumb=R('main_live.png'))))
    menu.add(PrefsObject(title=TEXT_PREFERENCES, thumb=R('icon-prefs.png')))
    return menu

#------------SHOW FUNCTIONS ---------------------
def GetIndexShows():
    Log("GetIndexShows")
    showsList = ObjectContainer(title1=TEXT_INDEX_SHOWS)
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//a[@class='playLetterLink']")
    for s in CreateShowList(programLinks):
        showsList.add(s)

    Thread.Create(HarvestShowData, programLinks = programLinks)
    return showsList

#This function wants a <a>..</a> tag list
def CreateShowList(programLinks):
    showsList = []
    for programLink in programLinks:
        showUrl = URL_SITE + programLink.get("href")
        showName = string.strip(programLink.xpath("text()")[0])
        Log(showName)
        show = TVShowObject()
        show.title = showName
        show.key = Callback(GetShowEpisodes, showUrl=showUrl, showName=showName)
        show.rating_key = showUrl
        show.thumb = R(THUMB)
        show.summary = GetShowSummary(showUrl, showName)
        showsList.append(show)

    return showsList     

def GetShowSummary(url, showName):
    sumExt = ".summary"
    showSumSave = showName + sumExt
    if Data.Exists(showSumSave):
        return Data.LoadObject(showSumSave)
    return ""

def HarvestShowData(programLinks):
    for programLink in programLinks:
        showURL = URL_SITE + programLink.get("href")
        showName = string.strip(programLink.xpath("text()")[0])
        pageElement = HTML.ElementFromURL(url)
        sum = pageElement.xpath("//div[@class='playVideoInfo']/span[2]/text()")

        if (len(sum) > 0):
            Data.SaveObject(showSumSave, str(sum[0]))

    return

def GetShowEpisodes(showUrl = None, showName = ""):
    pages = GetPaginateUrls(showUrl, "pr")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = ObjectContainer(title1=showName)
    for epUrl in epUrls:
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)

    return epList

def GetLiveShows():
    page = HTML.ElementFromURL(URL_LIVE, cacheTime = 0)
    liveshows = page.xpath("//img[@class='playBroadcastLiveIcon']//../..")
    showsList = ObjectContainer(title1="Live shows")
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
        
def GetLatestNews():
    pages = GetPaginateUrls(URL_LATEST_NEWS, "en", URL_SITE + "/")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = ObjectContainer(title1=TEXT_LATEST_NEWS)
    for epUrl in epUrls:
        Log(epUrl)
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)

    return epList

def GetLatestShows():
    pages = GetPaginateUrls(URL_LATEST_SHOWS, "ep", URL_SITE + "/")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = ObjectContainer(title1=TEXT_LATEST_SHOWS)
    for epUrl in epUrls:
        Log(epUrl)
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)

    return epList


#------------EPISODE FUNCTIONS ---------------------
def GetEpisodeUrlsFromPage(url):
    epUrls = []
    Log(url)
    try:
        pageElement = HTML.ElementFromURL(url)
    except:
        return epUrls

    xpath = "//div[@class='playPagerArea']//section[@class='playPagerSection svtHide-E-XS']//a[contains(@href,'video')]//@href"
    episodeElements = pageElement.xpath(xpath)
    for epElem in episodeElements:
        epUrl = URL_SITE + epElem
        epUrls.append(epUrl)
        HTTP.PreCache(epUrl)

    Log(len(epUrls))
    return epUrls

def GetEpisodeObject(url):
    try:
        # Request the page
       page = HTML.ElementFromURL(url)

       show = page.xpath("//div[@class='playVideoBox']/h1/text()")[0]
       title = page.xpath("//div[@class='playVideoInfo']//h1/text()")[0]
       description = page.xpath("//div[@class='playVideoInfo']//p/text()")[0]

       try:
           air_date = page.xpath("//div[@class='playVideoInfo']//time")[0].get("datetime")
           air_date = air_date.split('+')[0] #cut off timezone info as python can't parse this
           air_date = Datetime.ParseDate(air_date)
       except:
           Log.Exception("Error converting airdate: " + air_date)
           air_date = Datetime.now()
     
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
        Log.Exception("An error occurred while attempting to retrieve the required meta data.")

#------------MISC FUNCTIONS ---------------------

def ValidatePrefs():
    Log("Validate prefs")
    global MAX_PAGINATE_PAGES
    try:
         MAX_PAGINATE_PAGES = int(Prefs[PREF_PAGINATE_DEPTH])
    except ValueError:
        pass

    Log("max paginate %d" % MAX_PAGINATE_PAGES)

