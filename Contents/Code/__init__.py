from datetime import datetime
import time
import re

####################################################################################################

PLUGIN_PREFIX = "/video/baratsandbereta"

FEED = 'http://gdata.youtube.com/feeds/api/users/BaratsAndBereta/uploads?v=2'
YOUTUBE_VIDEO_PAGE = 'http://www.youtube.com/watch?v=%s'
YOUTUBE_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
YOUTUBE_FMT = [34, 18, 35, 22, 37]

NAME          = L('Title')

# make sure to replace artwork with what you want
ART           = 'art-default.jpg'
ICON          = 'icon-default.png'

####################################################################################################

def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, Menu, NAME, ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    VideoItem.thumb = R(ICON)
    
    HTTP.CacheTime = CACHE_1HOUR

def Menu():

    dir = MediaContainer(viewGroup="InfoList",title2=L('Episodes'), httpCookies=HTTP.GetCookiesForURL('http://www.youtube.com/'))
    dir = FeedMenu(feed = FEED)
    return dir

def FeedMenu(feed=''):
    dir = MediaContainer(viewGroup="InfoList",title2=L('Episodes'), httpCookies=HTTP.GetCookiesForURL('http://www.youtube.com/'))

    if '?' in feed:
	  feed = feed + '&alt=json'
    else:
	  feed = feed + '?alt=json'

    rawfeed = JSON.ObjectFromURL(feed, encoding='utf-8',cacheTime=CACHE_1HOUR)
    if rawfeed['feed'].has_key('entry'):
      for video in rawfeed['feed']['entry']:
        if video.has_key('yt$videoid'):
          video_id = video['yt$videoid']['$t']
        elif video['media$group'].has_key('media$player'):
          try:
            video_page = video['media$group']['media$player'][0]['url']
          except:
            video_page = video['media$group']['media$player']['url']
          video_id = re.search('v=([^&]+)', video_page).group(1)
        else:
          video_id = None      
        title = video['title']['$t']

        if (video_id != None) and not(video.has_key('app$control')):
	      try:
		    published = Datetime.ParseDate(video['published']['$t']).strftime('%a %b %d, %Y')
	      except: 
	  	    published = Datetime.ParseDate(video['updated']['$t']).strftime('%a %b %d, %Y')
	      if video.has_key('content') and video['content'].has_key('$t'):
		    summary = video['content']['$t']
	      else:
		    summary = video['media$group']['media$description']['$t']
	      duration = int(video['media$group']['yt$duration']['seconds']) * 1000
	      try:
		    rating = float(video['gd$rating']['average']) * 2
	      except:
		    rating = 0
	      thumb = video['media$group']['media$thumbnail'][0]['url']
	      dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=published, summary=summary, duration=duration, rating=rating, thumb=Function(Thumb, url=thumb)), video_id=video_id))
	
    if len(dir) == 0:
      return MessageContainer(L('Error'), L('This query did not return any result'))
    else:
      return dir

def Thumb(url):
  try:
    data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))
    
def PlayVideo(sender, video_id):
  yt_page = HTTP.Request(YOUTUBE_VIDEO_PAGE % (video_id), cacheTime=1).content
    
  fmt_url_map = re.findall('"url_encoded_fmt_stream_map".+?"([^"]+)', yt_page)[0]
  fmt_url_map = fmt_url_map.replace('\/', '/').split(',')
    
  fmts = []
  fmts_info = {}

  for f in fmt_url_map:
    map = {}
    params = f.split('\u0026')
    for p in params:
      try:
        (name, value) = p.split('=')
        map[name] = value
      except:
        pass
    quality = str(map['itag'])
    fmts_info[quality] = String.Unquote(map['url'])
    fmts.append(quality)

  index = YOUTUBE_VIDEO_FORMATS.index(Prefs['youtube_fmt'])
  if YOUTUBE_FMT[index] in fmts:
    fmt = YOUTUBE_FMT[index]
  else:
    for i in reversed( range(0, index+1) ):
      if str(YOUTUBE_FMT[i]) in fmts:
        fmt = YOUTUBE_FMT[i]
        break
      else:
        fmt = 5

  url = (fmts_info[str(fmt)]).decode('unicode_escape')
  Log("  VIDEO URL --> " + url)
  return Redirect(url)

