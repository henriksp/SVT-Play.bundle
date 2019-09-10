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

    title = 'Senaste Program'
    oc.add(
        DirectoryObject(
            key = Callback(Videos, title = title, suffix = 'latest', option = 'only vod'),
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

    title = 'Sista Chansen'
    oc.add(
        DirectoryObject(
            key = Callback(Videos, title = title, suffix = 'last_chance'),
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
    
    for item in json_data['videosAndTitles']:

        if item['contentType'] == "titel":
            do = DirectoryObjectFromItem(item)
        
            if do:
                oc.add(do)
            
        elif item['contentType'] == "videoEpisod":
            episode = EpisodeObjectFromItem(item)
        
            if episode:
                oc.add(episode)
    
    if len(oc) < 1:
        return ObjectContainer(header=unicode('Resultat'), message=unicode('Kunde inte hitta något för: ') + unicode(query))

    return oc

####################################################################################################
@route(PREFIX + '/videos')
def Videos(title, suffix = None, slug = None, option = 'all videos', sort = 'none'):

    oc = ObjectContainer(title2=unicode(title))

    request_url = ''

    if suffix:
        request_url = API_URL + suffix
    else:
        title_data = JSON.ObjectFromURL(API_URL + 'title?slug=%s' % slug.replace("/", ""))
        request_url = API_URL + 'title_episodes_by_article_id?articleId=%s' % title_data['articleId']

    if '?' in request_url:
        request_url = request_url + '&'
    else:
        request_url = request_url + '?'

    request_url = request_url + 'excludedTagsString=lokalt'
    json_data = JSON.ObjectFromURL(request_url)
    
    if 'data' in json_data:
        json_data = json_data['data']
    elif 'relatedVideos' in json_data:
        json_data = json_data['relatedVideos']['episodes']
    
    for item in json_data:
        episode = EpisodeObjectFromItem(item, option)
        
        if episode:
            oc.add(episode)

    if sort == 'by season':
        oc.objects.sort(key = lambda obj: (obj.season, obj.index), reverse=False)

    if len(oc) < 1:
        return ObjectContainer(header=unicode('Inga program funna'), message=unicode('Kunde inte hitta några program'))

    return oc

####################################################################################################
@route(PREFIX + '/channels')
def Channels(title):

    oc = ObjectContainer(title2=unicode(title))

    json_data = JSON.ObjectFromURL(API_URL + 'channel_page?now=%s' % Datetime.Now())
    
    for item in json_data['hits']:
        try: 
            channel = item['channel'].replace('SVTK', 'Kunskapskanalen').replace('SVTB', 'Barnkanalen')
            title = unicode(channel)
            url = BASE_URL + '/kanaler/%s' % channel.lower()
        except: 
            continue
        
        try: title = title + ' - ' + unicode(item['episodeTitle'])
        except: pass
        
        try: show = unicode(item['programmeTitle'])
        except: show = None
        
        try: summary = unicode(item['longDescription'])
        except: summary = None
        
        try: thumb = 'http://www.svtplay.se/public/images/channels/posters/%s.png' % channel.lower() 
        except: thumb = None
        
        try: season = item['season']
        except: season = None
        
        oc.add(
            EpisodeObject(
                url = url,
                title = title,
                thumb = thumb,
                summary = summary,
                season = season,
                show = show
            )
        )
    
    oc.objects.sort(key = lambda obj: obj.title)
    
    return oc

####################################################################################################
@route(PREFIX + '/categories')
def Categories(title):

    oc = ObjectContainer(title2=unicode(title))
    
    json_data = JSON.ObjectFromURL(API_URL + 'clusters')
    
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

    title_id = None
    slug = None

    try:
        title = unicode(item['programTitle']) if 'programTitle' in item else unicode(item['title'])
        url = item['contentUrl'] if 'contentUrl' in item else item['url']
        
        if '/video' in url:
            return None

        if 'articleId' in item:
            title_id = item['articleId']
        else:
            slug = url

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
    
    suffix = None
    if title_id:
        suffix = 'title_episodes_by_article_id?articleId=%s' % title_id

    return DirectoryObject(
        key = Callback(Videos, title = title, suffix = suffix, slug = slug, sort = 'by season'),
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
