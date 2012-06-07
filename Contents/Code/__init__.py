# -*- coding: utf-8 -*

import re
import string
from show import *
import cerealizer
from common import *
from episode import *
from category import *

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, TEXT_TITLE, "icon-default.png", "art-default.jpg")
    Plugin.AddViewGroup(name="List")
    HTTP.CacheTime = CACHE_TIME_SHORT
    HTTP.PreCache(URL_INDEX)

    #Start asap to reindex all shows
    #Thread.Create(ReindexShows)

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def MainMenu():
    menu = ObjectContainer(view_group="List", title1= TEXT_TITLE + " " + VERSION)
    menu.add(DirectoryObject(key=Callback(GetIndexShows), title=TEXT_INDEX_SHOWS, thumb=R('main_index.png')))
    #menu.Append(Function(DirectoryItem(GetRecommendedShows, title=TEXT_RECOMMENDED_SHOWS,
        #thumb=R('main_rekommenderat.png'))))
    #menu.Append(WebVideoItem(url="http://svtplay.se/t/102782/mitt_i_naturen", title="PauseTest"))
    #menu.Append(Function(DirectoryItem(GetLatestNews, title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png'))))
    #menu.Append(Function(DirectoryItem(GetLatestClips, title=TEXT_LATEST_CLIPS, thumb=R('main_senaste_klipp.png'))))
    #menu.Append(Function(DirectoryItem(GetLatestShows, title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png'))))
    #menu.Append(Function(DirectoryItem(GetMostViewed, title=TEXT_MOST_VIEWED, thumb=R('main_mest_sedda.png'))))
    #menu.Append(Function(DirectoryItem(GetCategories, title=TEXT_CATEGORIES, thumb=R('main_kategori.png'))))
    #menu.Append(Function(DirectoryItem(ListLiveMenu, title=TEXT_LIVE_SHOWS, thumb=R('main_live.png'))))
    #menu.Append(PrefsItem(title=TEXT_PREFERENCES, thumb=R('icon-prefs.png')))
    return menu

#------------SHOW FUNCTIONS ---------------------
def ReindexShows():
    GetIndexShows()

def GetIndexShows():
    Log("GetIndexShows")
    showsList = ObjectContainer(title1=TEXT_INDEX_SHOWS)
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath("//a[@class='playLetterLink']")
    for s in CreateShowList(programLinks):
        showsList.add(s)

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
    else: #No summary available atm. Don't wait for it.
        Thread.Create(GetShowSummaryAsync, url=url, showSumSave=showSumSave)
        return ""

def GetShowSummaryAsync(url, showSumSave):
    pageElement = HTML.ElementFromURL(url)
    sum = pageElement.xpath("//div[@class='playVideoInfo']/span[2]/text()")
    if (len(sum) > 0):
        Data.SaveObject(showSumSave, str(sum[0]))


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


######################## unchecked legacy code #####################
def GetCategories(sender):
    Log("GetCategories")
    catMenu = MediaContainer(viewGroup="List", title1 = sender.title1, title2=TEXT_CATEGORIES)
    catMenu.Append(Function(DirectoryItem(key=GetCategoryShows, title=TEXT_CAT_CHILD, thumb=R("category_barn.png")),
        catUrl=URL_CAT_CHILD, catName=TEXT_CAT_CHILD))
    catMenu.Append(Function(DirectoryItem(key=GetCategoryShows, title=TEXT_CAT_MOVIE_DRAMA, thumb=R("category_film_och_drama.png")),
        catUrl=URL_CAT_MOVIE_DRAMA, catName=TEXT_CAT_MOVIE_DRAMA))
    catMenu.Append(Function(DirectoryItem(key=GetCategoryShows, title=TEXT_CAT_FACT,
        thumb=R("category_samhalle_och_fakta.png")),
        catUrl=URL_CAT_FACT, catName=TEXT_CAT_FACT))
    catMenu.Append(Function(DirectoryItem(key=GetCategoryNewsShows, title=TEXT_CAT_NEWS,
        thumb=R("category_nyheter.png")),
        catUrl=URL_CAT_NEWS, catName=TEXT_CAT_NEWS))
    catMenu.Append(Function(DirectoryItem(key=GetCategoryNewsShows, title=TEXT_CAT_SPORT,
        thumb=R("category_sport.png")),
        catUrl=URL_CAT_SPORT, catName=TEXT_CAT_SPORT))

    return catMenu

def GetLatestNews(sender):
    Log("GetLatestNews")
    newsList = MediaContainer(title1=sender.title1, title2 = TEXT_LATEST_NEWS)
    pages = GetPaginatePages(url=URL_LATEST_NEWS, divId='pb')
    linksList = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='pb']//div[@class='content']//a/@href")
        for link in links:
            newsLink = URL_SITE + link
            linksList.append(newsLink)

    for link in linksList:
        epInfo = GetEpisodeInfo(link)        
        newsList.Append(epInfo.GetMediaItem())

    return newsList

def GetMostViewed(sender):
    Log("GetMostViewed")
    showsList = MediaContainer(title1 = sender.title1, title2 = TEXT_MOST_VIEWED)
    pages = GetPaginatePages(url=URL_MOST_VIEWED, divId='pb', maxPaginateDepth = MAX_PAGINATE_PAGES)
    linksList = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='pb']//div[@class='content']//a")
        linksList = linksList + links

    showsList.Extend(CreateShowList(linksList, True))
 
    return showsList

def GetLatestShows(sender):
    Log("GetLatestShows")
    showsList = MediaContainer(title1 = sender.title1, title2 = TEXT_LATEST_SHOWS)
    pages = GetPaginatePages(url=URL_LATEST_SHOWS, divId='pb', maxPaginateDepth = MAX_PAGINATE_PAGES)
    linksList = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='pb']//div[@class='content']//a")
        linksList = linksList + links

    showsList.Extend(CreateShowList(linksList, True))
    return showsList
   
def GetLatestClips(sender):
    Log("GetLatestClips")
    clipsList = MediaContainer(title1 = sender.title1, title2 = TEXT_LATEST_CLIPS)
    clipsPages = GetPaginatePages(url=URL_LATEST_CLIPS, divId='cb', maxPaginateDepth = MAX_PAGINATE_PAGES)
    clipLinks = []
    for page in clipsPages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='cb']//div[@class='content']//a/@href")
        for link in links:
            clipLink = URL_SITE + link
            clipLinks.append(clipLink)
            Log("clipLink: %s" % clipLink)

    for clipLink in clipLinks:
        epInfo = GetEpisodeInfo(clipLink)        
        clipsList.Append(epInfo.GetMediaItem())

    return clipsList


def ValidatePrefs():
    Log("Validate prefs")
    global MAX_PAGINATE_PAGES
    try:
         MAX_PAGINATE_PAGES = int(Prefs[PREF_PAGINATE_DEPTH])
    except ValueError:
        pass

    Log("max paginate %d" % MAX_PAGINATE_PAGES)

def ListLiveMenu(sender):
    liveList = MediaContainer()
    pageElement = HTML.ElementFromURL(URL_LIVE, cacheTime = 0)
    activeLinks = pageElement.xpath("//span[@class='description']/a/@href")
    for link in activeLinks:
        newLink = URL_SITE + link
        Log("Link: %s " % newLink)
        epInfo = GetEpisodeInfo(newLink, True)
        liveList.Append(epInfo.GetMediaItem())

    return liveList

