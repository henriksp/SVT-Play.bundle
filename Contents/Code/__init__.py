TITLE = 'SVT Play'
PREFIX = '/video/svtplay'

ICON  = 'icon-default.png'
ART = 'art-default.jpg'

BASE_URL = 'http://www.svtplay.se'
START_URL = BASE_URL + '/xml/start.xml'
ALL_PROGRAMS_URL = BASE_URL + '/xml/programmes.xml'
CATEGORIES_URL = BASE_URL + '/xml/categories.xml'
VIDEO_URL_TEMPLATE = BASE_URL + '/video/'
URL_SEARCH = BASE_URL + '/xml/search-results.xml?q=%s'
NEWS_URLS = {'Aktuellt': BASE_URL + '/xml/title/29529.xml', 'Rapport': BASE_URL + '/xml/title/1109035.xml'}

CHANNELS = {'svt1': 'SVT1', 'svt2': 'SVT2', 'barnkanalen': 'Barnkanalen', 'svt24': 'SVT24', 'kunskapskanalen': 'Kunskapskanalen'}

RE_URL = Regex("'(.+)'")
RE_SEASON = Regex(unicode("Säsong ([0-9]+)"))
RE_EPISODE = Regex("Avsnitt ([0-9]+)")
RE_DURATION_MINS = Regex("([0-9]+) minuter")
RE_DURATION_HOURS = Regex("([0-9]+) timm")
RE_DATE_INFO = Regex(unicode("Sändes (.+)"))
RE_DATE = Regex("([0-9]+) (.+) *([0-9]*)")

MONTHS = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'maj': '05', 'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09', 'okt': '10', 'nov': '11', 'dec': '12'}

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
    
    xml_data = XML.ObjectFromURL(START_URL)
    
    for item in xml_data.xpath("//collectionDivider"):
        title = item.xpath("./title/text()")[0]
        id = item.xpath("./following-sibling::shelf/@id")[0]
    
        oc.add(
            DirectoryObject(
                key = Callback(Collections, title = title, id = id),
                title = title
            )
        )

    title = 'Senaste Nyhetsprogram'
    oc.add(
        DirectoryObject(
            key = Callback(LatestNews, title = title),
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
            key = Callback(Programs, title = title, url = ALL_PROGRAMS_URL),
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
    
    search_url = URL_SEARCH % unicode(String.Quote(query))
    xml_data = XML.ObjectFromURL(search_url)
    
    for item in xml_data.xpath("//twoLineEnhancedMenuItem"):
        title = unicode(item.xpath(".//label/text()")[0])
        url = RE_URL.search(item.xpath("./@onSelect")[0]).groups()[0]
            
        try: thumb = item.xpath(".//image/text()")[0]
        except: thumb = None

        if 'xml/category' in url:
            oc.add(
                DirectoryObject(
                    key = Callback(Category, title = title, url = url, thumb = thumb),
                    title = title,
                    thumb = thumb
                )
            )
        
        elif 'xml/title' in url:
            oc.add(
                DirectoryObject(
                    key = Callback(Videos, title = title, url = url, thumb = thumb),
                    title = title,
                    thumb = thumb
                )
            )
    
    for item in xml_data.xpath("//comboMenuItem"):
        url = RE_URL.search(item.xpath("./@onSelect")[0]).groups()[0]
        
        if not 'xml/video' in url:
            continue

        oc.add(
            EpisodeObjectFromItem(item = item, show = unicode(item.xpath(".//label/text()")[0]))
        )

    if len(oc) < 1:
        return ObjectContainer(header=unicode("Resultat"), message=unicode("Kunde inte hitta något för: ") + unicode(query))

    return oc
        
####################################################################################################
@route(PREFIX + '/latestnews')
def LatestNews(title):

    oc = ObjectContainer(title2=unicode(title))

    for show in NEWS_URLS:
        oc.add(
            DirectoryObject(
                key = Callback(Videos, title = show, url = NEWS_URLS[show]),
                title = show
            )
        )
    
    return oc

####################################################################################################
@route(PREFIX + '/channels')
def Channels(title):

    oc = ObjectContainer(title2=unicode(title))
    
    # Just hardcode all channels
    for channel in CHANNELS:
        oc.add(
            VideoClipObject(
                url = BASE_URL + '/kanaler/%s' % channel,
                title = CHANNELS[channel],
                thumb = 'http://www.svtplay.se/public/images/channels/posters/%s.png' % channel
            )
        )
    
    oc.objects.sort(key = lambda obj: obj.title)
    
    return oc

####################################################################################################
@route(PREFIX + '/categories')
def Categories(title):

    oc = ObjectContainer(title2=unicode(title))
    
    xml_data = XML.ObjectFromURL(CATEGORIES_URL)
    
    for item in xml_data.xpath("//items/sixteenByNinePoster"):
        title = unicode(item.xpath("./@accessibilityLabel")[0])
        url = RE_URL.search(item.xpath("./@onSelect")[0]).groups()[0]
        
        try: thumb = item.xpath(".//image/text()")[0]
        except: thumb = None
        
        oc.add(
            DirectoryObject(
                key = Callback(Category, title = title, url = url, thumb = thumb),
                title = title,
                thumb = thumb
            )
        )
    
    return oc

####################################################################################################
@route(PREFIX + '/category')
def Category(title, url, thumb):

    oc = ObjectContainer(title2=unicode(title))
    
    xml_data = XML.ObjectFromURL(url)
    
    for item in xml_data.xpath("//items/oneLineMenuItem"):
        title = unicode(item.xpath(".//label/text()")[0])
        url = item.xpath(".//link/text()")[0]
        
        oc.add(
            DirectoryObject(
                key = Callback(Programs, title = title, url = url),
                title = title,
                thumb = thumb
            )
        )
    
    return oc

####################################################################################################
@route(PREFIX + '/programs')
def Programs(title, url):

    oc = ObjectContainer(title2=unicode(title))
    
    xml_data = XML.ObjectFromURL(url)
    
    programs = []
    for item in xml_data.xpath("//items/sixteenByNinePoster"):
        title = unicode(item.xpath(".//title/text()")[0])
        url = RE_URL.search(item.xpath("./@onSelect")[0]).groups()[0]
        
        try: thumb = item.xpath(".//image/text()")[0]
        except: thumb = None
        
        if not title in programs:
            programs.append(title)
        else:
            continue
        
        oc.add(
            DirectoryObject(
                key = Callback(Videos, title = title, url = url, thumb = thumb),
                title = title,
                thumb = thumb
            )
        )
    
    oc.objects.sort(key = lambda obj: obj.title)
    
    return oc

####################################################################################################
@route(PREFIX + '/collections')
def Collections(title, id):

    oc = ObjectContainer(title2=unicode(title))
    
    xml_data = XML.ObjectFromURL(START_URL)
    
    for item in xml_data.xpath("//shelf[@id='" + id + "']//items//sixteenByNinePoster"):
        title = unicode(item.xpath(".//title/text()")[0])
        
        try: title = title + ': ' + unicode(item.xpath(".//subtitle/text()")[0])
        except: pass
        
        url = RE_URL.search(item.xpath("./@onSelect")[0]).groups()[0]
        
        try: thumb = item.xpath(".//image/text()")[0]
        except: thumb = None

        if 'xml/video' in url:
            id = url.replace("http://www.svtplay.se/xml/video/", "").replace(".xml", "").strip()
            video_url = VIDEO_URL_TEMPLATE + id
        
            oc.add(
                VideoClipObject(
                    url = video_url,
                    title = title,
                    thumb = thumb
                )
            )

        else:
            oc.add(
                DirectoryObject(
                    key = Callback(Videos, title = title, url = url, thumb = thumb),
                    title = title,
                    thumb = thumb
                )
            )
    
    return oc
    
####################################################################################################
@route(PREFIX + '/videos')
def Videos(title, url, thumb=None):

    oc = ObjectContainer(title2=unicode(title))
    xml_data = XML.ObjectFromURL(url)
    
    show = None
    try: show = xml_data.xpath("//title/text()")[0]
    except: pass
    
    episodes_url = xml_data.xpath("//navigationItem[@id='episodes']/url/text()")[0]
    episodes_xml_data = XML.ObjectFromURL(episodes_url)
    
    for item in episodes_xml_data.xpath("//navigationItem[@id='episodes']//items//twoLineEnhancedMenuItem"):
        oc.add(
            EpisodeObjectFromItem(item, show)
        )
    
    
    return oc

####################################################################################################
def EpisodeObjectFromItem(item, show=None):

    title = unicode(item.xpath(".//title/text()")[0])
    xml_url = RE_URL.search(item.xpath("./@onSelect")[0]).groups()[0]
    
    if "," in xml_url:
        id = xml_url.split(",")[-1].replace("'", "").strip()
    else:
        id = xml_url.split("/")[-1].replace(".xml", "").strip()
    
    url = VIDEO_URL_TEMPLATE + id
    
    try: thumb = item.xpath(".//image/text()")[0]
    except: thumb = None
    
    try: 
        summary = unicode(item.xpath(".//summary/text()")[0])
    except:
        try: 
            summary = ''
            for label in item.xpath(".//label/text()"):
                summary = summary + label + '\n'
        except:
            summary = None
    
    season = None
    index = None
    duration = None
    originally_available_at = None
     
    for label in item.xpath(".//label/text()"):
        if not season:
            try: season = int(RE_SEASON.search(label).groups()[0])
            except: pass
        
        if not index:
            try: index = int(RE_EPISODE.search(label).groups()[0])
            except: pass
            
        if not duration:
            duration_mins = 0
            duration_hours = 0
            
            try: 
                duration_mins = int(RE_DURATION_MINS.search(label).groups()[0])
            except: 
                pass
                
            try: 
                duration_hours = int(RE_DURATION_HOURS.search(label).groups()[0])
            except: 
                pass
                
            if duration_mins > 0 or duration_hours > 0:
                duration = (duration_mins * 60 + duration_hours * 3600) * 1000
            
        if not originally_available_at:
            date_info = RE_DATE_INFO.search(label)

            if not date_info:
                continue
                
            date_info = date_info.groups()[0]
            
            if ('idag' in date_info) or ('ikväll' in date_info):
                originally_available_at = Datetime.Now()
            
            elif 'igår' in date_info:
                originally_available_at = Datetime.Now() - Datetime.Delta(days=1)
            
            else:
                data = RE_DATE.search(label)
                
                if not data:
                    continue

                data = data.groups()
                day = data[0]
                month = data[1].split(" ")[0]
                
                if int(day) < 10:
                    day = '0%s' % day
                
                try:
                    year = data[1].split(" ")[1]
                except:
                    year = str(Datetime.Now()).split("-")[0]
                   
                originally_available_at = Datetime.ParseDate('%s-%s-%s' % (year, MONTHS[month], day)).date()

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
