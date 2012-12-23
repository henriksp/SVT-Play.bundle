
# -*- coding: utf-8 -*

import string
from common import *
import hashlib

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
    menu.add(DirectoryObject(key=Callback(GetLiveShows, prevTitle=TEXT_TITLE), title=TEXT_LIVE_SHOWS, thumb=R('main_live.png')))
    menu.add(DirectoryObject(
        key=Callback(GetLatestNews, prevTitle=TEXT_TITLE), title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png')))
    menu.add(DirectoryObject(
        key=Callback(GetLatestShows, prevTitle=TEXT_TITLE), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    menu.add(PrefsObject(title=TEXT_PREFERENCES, thumb=R('icon-prefs.png')))
    return menu

#------------SHOW FUNCTIONS ---------------------
def GetIndexShows(prevTitle):
    showsList = ObjectContainer(title1 = prevTitle, title2=TEXT_INDEX_SHOWS)
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//a[@class='playAlphabeticLetterLink']")
    for s in CreateShowList(programLinks, TEXT_INDEX_SHOWS):
        showsList.add(s)

    Thread.Create(HarvestShowData, programLinks = programLinks)
    return showsList

#This function wants a <a>..</a> tag list
def CreateShowList(programLinks, parentTitle=None):
    showsList = []
    for programLink in programLinks:
        try:
            showUrl = URL_SITE + programLink.get("href")
            showName = string.strip(programLink.xpath("text()")[0])
            show = DirectoryObject()
            show.title = showName
            show.key = Callback(GetShowEpisodes, prevTitle=parentTitle, showUrl=showUrl, showName=showName)
            show.thumb = R(THUMB)
            show.summary = GetShowSummary(showUrl, showName)
            showsList.append(show)
        except: 
            Log("Error creating show: "+programLink.get("href"))
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
	    
            if (len(sum) > 0):
                showSumSave = showName + sumExt
                showSumSave = ReplaceSpecials(showSumSave)
                Data.SaveObject(showSumSave, sum[0].encode('utf-8'))
        except:
            Log("Error harvesting show data: "+programLink.get("href"))
            pass

def GetShowEpisodes(prevTitle = None, showUrl = None, showName = ""):
    pages = GetPaginateUrls(showUrl, "pr")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = ObjectContainer(title1=prevTitle, title2=showName)
    for epUrl in epUrls:
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)

    return epList

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
        show = EpisodeObject(
            url = url,
            title = title,
            thumb = thumb
            )
        showsList.add(show)
    return showsList
        
def GetLatestNews(prevTitle):
    pages = GetPaginateUrls(URL_LATEST_NEWS, "en", URL_SITE + "/")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = ObjectContainer(title1=prevTitle, title2=TEXT_LATEST_NEWS)
    for epUrl in epUrls:
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)

    return epList

def GetLatestShows(prevTitle):
    pages = GetPaginateUrls(URL_LATEST_SHOWS, "ep", URL_SITE + "/")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = ObjectContainer(title1=prevTitle, title2=TEXT_LATEST_SHOWS)
    for epUrl in epUrls:
        epObj = GetEpisodeObject(epUrl)
        epList.add(epObj)

    return epList


#------------EPISODE FUNCTIONS ---------------------
def GetEpisodeUrlsFromPage(url):
    epUrls = []
    try:
        pageElement = HTML.ElementFromURL(url)
    except:
        Log("Error finding episode urls: "+url )
        return epUrls

    xpath = "//div[@class='playDisplayTable']//a[contains(@href,'video')]//@href"
    episodeElements = pageElement.xpath(xpath)
    for epElem in episodeElements:
        epUrl = URL_SITE + epElem
        epUrls.append(epUrl)
        HTTP.PreCache(epUrl)

    return epUrls

def GetEpisodeObject(url):
    try:
        # Request the page
       page = HTML.ElementFromURL(url)

       show = page.xpath("//div[@class='playVideoBox']//h1/text()")[0]
       title = page.xpath("//div[@class='playVideoInfo']//h2/text()")[0]
       description = page.xpath("//div[@class='playVideoInfo']//p/text()")[0]

       air_date = ""
       try:
           air_date = page.xpath("//div[@class='playVideoInfo']//time")[0].get("datetime")
           air_date = air_date.split('+')[0] #cut off timezone info as python can't parse this
           air_date = Datetime.ParseDate(air_date)
       except:
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
        Log.Exception("An error occurred while attempting to retrieve the required meta data.")

#------------MISC FUNCTIONS ---------------------

def ValidatePrefs():
    global MAX_PAGINATE_PAGES
    try:
         MAX_PAGINATE_PAGES = int(Prefs[PREF_PAGINATE_DEPTH])
    except ValueError:
        pass

def ReplaceSpecials(replaceString):
    return replaceString.encode('utf-8')
