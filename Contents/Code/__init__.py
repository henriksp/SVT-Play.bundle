TITLE = 'SVT Play'
PREFIX = '/video/svtplay'

ICON  = 'icon-default.png'
ART = 'art-default.jpg'

BASE_URL = 'http://www.svtplay.se'
API_URL = BASE_URL + '/api/'

####################################################################################################
def Start():

    ObjectContainer.title1 = TITLE
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'AppleTV/7.2 iOS/8.3 AppleTV/7.2 model/AppleTV3,2 build/12F69 (3; dt:12)'

####################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():

    oc = ObjectContainer()

    title = 'Senaste Nyhetsprogram'
    oc.add(
        DirectoryObject(
            key = Callback(Videos, title = title, suffix = 'cluster_latest;cluster=nyheter', sort = 'by date'),
            title = title
        )
    )

    title = 'Senaste Program'
    oc.add(
        DirectoryObject(
            key = Callback(Videos, title = title, suffix = 'latest', option = 'only vod', sort = 'by date'),
            title = title
        )
    )
    
    title = unicode('Populärt')
    oc.add(
        DirectoryObject(
            key = Callback(Videos, title = title, suffix = 'popular'),
            title = title
        )
    )
    
    title = unicode('Livesändningar')
    oc.add(
        DirectoryObject(
            key = Callback(Videos, title = title, suffix = 'latest', option = 'only live'),
            title = title
        )
    )
    
    title = 'Rekommenderat'
    oc.add(
        DirectoryObject(
            key = Callback(Videos, title = title, suffix = 'recommended'),
            title = title
        )
    )

    title = 'Kanaler'
    oc.add(
        DirectoryObject(
            key = Callback(Channels, title = title),
            title = title
        )
    )

    title = 'Kategorier'
    oc.add(
        DirectoryObject(
            key = Callback(Categories, title = title),
            title = title
        )
    )
        
    title = 'Alla Program'
    oc.add(
        DirectoryObject(
            key = Callback(Programs, title = title, suffix = 'all_titles_and_singles'),
            title = title
        )
    )
    
    title = unicode("Sök")
    oc.add(
        InputDirectoryObject(
            key = Callback(Search),
            title = title,
            prompt = title,
            thumb = R('search.png'),
            art = R(ART)
        )
    )
    
    return oc

####################################################################################################
# NOTE! Can't have a route on this one since Samsung can't handle it!
def Search(query):

    oc = ObjectContainer(title2='Resultat')
    
    json_data = JSON.ObjectFromURL(API_URL + 'search?q=%s' % unicode(String.Quote(query)))
    
    for item in json_data['titles']:
        do = DirectoryObjectFromItem(item)
        
        if do:
            oc.add(do)
            
    for item in json_data['episodes']:
        episode = EpisodeObjectFromItem(item)
        
        if episode:
            oc.add(episode)
    
    if len(oc) < 1:
        return ObjectContainer(header=unicode('Resultat'), message=unicode('Kunde inte hitta något för: ') + unicode(query))

    return oc

####################################################################################################
@route(PREFIX + '/videos')
def Videos(title, suffix, option = 'all videos', sort = 'by season'):

    oc = ObjectContainer(title2=unicode(title))

    json_data = JSON.ObjectFromURL(API_URL + suffix)
    
    if 'data' in json_data:
        json_data = json_data['data']
    elif 'relatedVideos' in json_data:
        json_data = json_data['relatedVideos']['episodes']
    
    for item in json_data:
        episode = EpisodeObjectFromItem(item, option)
        
        if episode:
            oc.add(episode)

    if sort == 'by season':
        seasons = {}
        for obj in oc.objects:
            if obj.season not in seasons:
                seasons[obj.season] = []
                
            seasons[obj.season].append(obj)
        
        for season in seasons:
            seasons[season] = sorted(seasons[season], key=seasons[season].index, reverse=True)
            
        oc = ObjectContainer(title2=unicode(title))
        for season in seasons:
            for episode in seasons[season]:
                oc.add(episode)
    
    else:
        oc.objects.sort(key = lambda obj: obj.originally_available_at, reverse=True)

    if len(oc) < 1:
        return ObjectContainer(header=unicode('Inga program funna'), message=unicode('Kunde inte hitta några program'))

    return oc

####################################################################################################
@route(PREFIX + '/channels')
def Channels(title):

    oc = ObjectContainer(title2=unicode(title))

    json_data = JSON.ObjectFromURL(API_URL + 'channel_page')
    
    for item in json_data['channels']:
        try: 
            title = unicode(item['name'])
            url = BASE_URL + '/kanaler/%s' % item['title']
        except: 
            continue
        
        try: title = title + ' - ' + unicode(item['schedule'][0]['title'])
        except: pass
        
        try: summary = unicode(item['schedule'][0]['description'])
        except: summary = None
        
        try: thumb = 'http://www.svtplay.se/public/images/channels/posters/%s.png' % item['title'] 
        except: thumb = None
        
        try: art = item['schedule'][0]['titlePage']['thumbnailLarge']
        except: art = None
        
        oc.add(
            VideoClipObject(
                url = url,
                title = title,
                thumb = thumb,
                summary = summary,
                art = art
            )
        )
    
    oc.objects.sort(key = lambda obj: obj.title)
    
    return oc

####################################################################################################
@route(PREFIX + '/categories')
def Categories(title):

    oc = ObjectContainer(title2=unicode(title))
    
    json_data = JSON.ObjectFromURL(API_URL + 'active_clusters')
    
    for item in json_data:
        try: 
            title = unicode(item['name'])
            slug = item['slug']
        except:
            continue
        
        summary = None
        try: summary = item['description']
        except: pass
        
        thumb = None
        try: 
            if 'thumbnailImage' in item and item['thumbnailImage'] is not None:
                thumb = GetImage(item['thumbnailImage'])
            else:
                thumb = GetImage(item['backgroundImage'])
        except: pass
        
        art = None
        try: art = GetImage(item['backgroundImage'])
        except: pass
        
        oc.add(
            DirectoryObject(
                key = Callback(Programs, title = title, suffix = 'cluster_titles_and_episodes/?cluster=' + slug),
                title = title,
                summary = summary,
                thumb = thumb,
                art = art
            )
        )
        
        
    return oc

####################################################################################################
@route(PREFIX + '/programs')
def Programs(title, suffix):

    oc = ObjectContainer(title2=unicode(title))
    
    json_data = JSON.ObjectFromURL(API_URL + suffix)
    
    for item in json_data:
        do = DirectoryObjectFromItem(item)
        
        if do:
            oc.add(do)
    
    return oc
    
    oc.objects.sort(key = lambda obj: obj.title)
    
    return oc

####################################################################################################
def EpisodeObjectFromItem(item, option = 'all videos'):

    try:
        title = unicode(item['title'])

        if 'programTitle' in item:
            title = unicode(item['programTitle']) + ' - ' + title

        url = BASE_URL + item['contentUrl'] if 'contentUrl' in item else BASE_URL + item['url']
        
        if not '/video' in url:
            return None
    except:
        return None
    
    if option != 'all videos':
        try:
            if item['broadcastedNow'] and option == 'only vod':
                return None
            
            elif option == 'only live' and not item['broadcastedNow']:
                return None
        except:
            pass
    
    thumb = None
    if 'thumbnail' in item:
        thumb = GetImage(item['thumbnail'])
        
    if not thumb:
        if 'poster' in item:
            thumb = GetImage(item['poster'])
            
    if not thumb:
        if 'image' in item:
            thumb = GetImage(item['image'])
    
    try: summary = item['description']
    except: summary = None

    try: show = item['prefix'] if 'prefix' in item else unicode(item['programTitle'])
    except: show = None
    
    try: season = int(item['season'])
    except: season = None
    
    try: index = int(item['episodeNumber'])
    except: index = None
    
    try: duration = int(item['materialLength']) * 1000
    except: duration = None
    
    try: originally_available_at = Datetime.ParseDate(item['broadcastDate'].split('T')[0]).date()
    except: originally_available_at = None
  
    return EpisodeObject(
        url = url,
        title = title,
        thumb = thumb,
        summary = summary,
        show = show,
        season = season,
        index = index,
        duration = duration,
        originally_available_at = originally_available_at,
        art = thumb
    )

####################################################################################################
def DirectoryObjectFromItem(item):

    try:
        title = unicode(item['programTitle']) if 'programTitle' in item else unicode(item['title'])
        url = item['contentUrl'] if 'contentUrl' in item else item['url']
        
        if '/video' in url:
            return None

    except: return None
    
    summary = None
    try: summary = item['description']
    except: pass
    
    thumb = None
    if 'thumbnail' in item:
        thumb = GetImage(item['thumbnail'])
        
    if not thumb:
        if 'poster' in item:
            thumb = GetImage(item['poster'])
            
    if not thumb:
        if 'image' in item:
            thumb = GetImage(item['image'])
    
    art = None
    try: art = GetImage(item['poster'])
    except: pass 
    
    return DirectoryObject(
        key = Callback(Videos, title = title, suffix = 'title_page;title=%s' % url),
        title = title,
        summary = summary,
        thumb = thumb,
        art = art
    )

####################################################################################################
def GetImage(url):

    if url:
        return url.replace('{format}','extralarge')
    else:
        return None
