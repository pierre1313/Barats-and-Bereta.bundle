# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *
from datetime import datetime
import time
import re

####################################################################################################

# also make sure to edit the Info.plist to give it a unique name
PLUGIN_PREFIX = "/video/baratsandbereta"

# add more than one feed if you want, it will combine them and sort by date
FEED = 'http://gdata.youtube.com/feeds/base/users/BaratsAndBereta/uploads'

NAME          = 'Barats and Bereta'

# make sure to replace artwork with what you want
ART           = 'art-default.png'
ICON          = 'icon-default.png'

####################################################################################################

yt_videoURL         = "http://www.youtube.com/get_video?video_id="
def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, Menu, NAME, ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)

def Menu():

    dir = MediaContainer(viewGroup="InfoList",title2="Episodes")
    dir = parseFeed(FEED,dir)
    return dir

def FeedMenu(sender,feed=''):
    PMS.Log('FEED: %s' % feed)
    dir = MediaContainer(viewGroup="InfoList",title2="Episodes")
    dir = parseFeed(feed,dir)
    return dir

def parseFeed(feed,dir):
  xml = XML.ElementFromURL(feed,cacheTime=Constants.CACHE_1HOUR)

  count = 1

  ns = {
      'a':  'http://www.w3.org/2005/Atom',
      'os': 'http://a9.com/-/spec/opensearchrss/1.0/',
  }

  nextUrl = None
  try:
      nextUrl = xml.xpath('//a:link[@rel="next"]',namespaces=ns)[0].get('href')
  except:
      pass

  prevUrl = None
  try:
      prevUrl = xml.xpath('//a:link[@rel="previous"]',namespaces=ns)[0].get('href')
  except:
      pass

  if prevUrl:
      dir.Append(Function(DirectoryItem(FeedMenu,title='Previous Page...'),feed=prevUrl))

  for e in xml.xpath('//a:entry',namespaces=ns):

      date = ''
      try:
          date = re.sub('T.*','',e.xpath('.//a:published/text()',namespaces=ns)[0])
      except:
          pass


      url = e.xpath('.//a:link[@rel="alternate"]',namespaces=ns)[0].get('href')
      title = e.xpath('.//a:title/text()',namespaces=ns)[0]

      summary_html = e.xpath('.//a:content/text()',namespaces=ns)[0]
      summary_xml = XML.ElementFromString(summary_html, isHTML=True)

      thumb = R(ICON)
      try:
          thumb = summary_xml.xpath('//img')[0].get('src')
          thumb = re.sub(r'/default.jpg','/hqdefault.jpg',thumb)
      except:
          pass

      summary = ''
      try:
          summary = summary_xml.xpath('//span')[0].text
      except:
          pass

      duration = 0
      try:
        dur_parts = summary_xml.xpath('//span')[-2].text.split(':')
        dur_parts.reverse()
        i = 0
        for p in dur_parts:
            duration = duration + int(p)*(60**i)
            i = i + 1
        duration = duration * 1000
      except:
          pass

      e = {
        'url': '%s' % url,
        'title': '%s' % title,
        'summary': '%s' % summary,
        'duration': '%s' % duration,
        'thumb': '%s' % thumb,
        'subtitle': '%s' % date,
      }

      PMS.Log(e)

      dir.Append(Function(VideoItem(VidRedirect, title=e['title'], summary=e['summary'], duration=e['duration'], thumb=e['thumb'], subtitle=e['subtitle']),url=e['url']))

  if nextUrl:
      dir.Append(Function(DirectoryItem(FeedMenu,title='Next Page...'),feed=nextUrl))

  return dir

def VidRedirect(sender,url=''):

    ytPage = HTTP.Request(url)
    
    t = re.findall('"t": "([^"]+)"', ytPage)[0]
    v = re.findall("'VIDEO_ID': '([^']+)'", ytPage)[0] #
    hd = re.findall("'IS_HD_AVAILABLE': ([^,]+),", ytPage)[0] #

    
    fmt = "18"
    if hd == "true":
      fmt = "22"
      
    u = yt_videoURL + v + "&t=" + t + "&fmt=" + fmt
    return Redirect(u)
