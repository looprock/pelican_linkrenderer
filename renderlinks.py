#!/usr/bin/env python
"""Process links in a file for pelican formatting."""
import requests
import bs4
import sys
import re
import os

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
from random import choice
from string import ascii_uppercase


# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = os.environ['DEVELOPER_KEY']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def youtube_search(vid):
    """Search youtube."""
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    search_response = youtube.videos().list(
        id=vid,
        part="snippet"
    ).execute()

    return search_response['items'][0]['snippet']['title']

# reload(sys)
# sys.setdefaultencoding('utf8')


debug = False

# the slideshare oembed API can be REALLY slow
timeout = 20.0


def bug(msg):
    """Debug mode."""
    if debug:
        print "*** DEBUG: %s" % msg


def gettitle(link):
    """Retrieve the title of a webpage."""
    try:
        r = requests.get(link, timeout=timeout)
        if r.status_code == 200:
            html = bs4.BeautifulSoup(r.text, "lxml")
            t = html.title.text
            v = t.strip()
            bug("Title: %s")
        else:
            bug("status code: %s" % str(r.status_code))
            bug(r.content)
    except:
            bug("Unable to get title")
            v = None
    return v


def process_vimeo(link):
    """Embed links from vimeo."""
    try:
        v = ""
        if gettitle(link):
            v += "**%s**\n" % gettitle(link)
            v += " "
        x = re.match(r'^(.*)vimeo.com\/(\d+)(.*)', link)
        vid = x.group(2)
        bug('vimeo ID: %s' % vid)
        v += ".. vimeo:: %s\n" % vid
        v += " \n"
        v += "|  \n"
    except:
        v = link
    return v


def process_slideshare(link):
    """Embed links from slideshare."""
    try:
        link = link.split('?')[0]
        bug("trying link: %s" % link)
        v = ""
        if gettitle(link):
            v += "**%s**\n" % gettitle(link)
            v += " "
        url = 'http://www.slideshare.net/api/oembed/2?format=json&url=%s' % link
        r = requests.get(url, timeout=timeout)
        bug("Response code to oembed link: %s" % str(r.status_code))
        k = r.json()['html']
        x = re.match(r'^.*(\/key\/)(\S+)"(.*)', k)
        shkey = x.group(2)
        v += ".. slideshare:: %s\n" % shkey
        v += " \n"
        v += "|  \n"
    except requests.exceptions.Timeout:
        bug("ERROR: hit timeout")
        v = link
    except requests.exceptions.TooManyRedirects:
        bug("ERROR: too many redirects")
        v = link
    except requests.exceptions.RequestException as e:
        bug(e)
        v = link
    return v


def process_youtube(link):
    """Embed links from youtube."""
    try:
        x = re.match(r'^(.*)?v=([A-Za-z0-9_-]+)(.*)', link)
        bug(x)
        bug('youtube ID: %s' % x.group(2))
        v = ""
        v += "**%s**\n" % youtube_search(x.group(2))
        v += " "
        v += ".. youtube:: %s\n" % x.group(2)
        v += " \n"
        v += "|  \n"
    except:
        v = link
    return v


def linktitle(link):
    """Where the magic happens."""
    bug("Processing link: %s" % link)
    if re.match(r'(.*)slideshare\.net(.*)', link):
        bug('matched slideshare')
        linktype = 'slideshare'
    elif re.match(r'(.*)youtube\.com(.*)', link):
        bug('matched youtube')
        linktype = 'youtube'
    elif re.match(r'(.*)vimeo\.com(.*)', link):
        bug('matched vimeo')
        linktype = 'vimeo'
    else:
        bug('matched nothing: vanilla link')
        linktype = 'vanilla'
    try:
        if linktype == 'slideshare':
            bug('processing link as slideshare')
            return process_slideshare(link)
        elif linktype == 'youtube':
            bug('processing link as youtube')
            return process_youtube(link)
        elif linktype == 'vimeo':
            bug('processing link as vimeo')
            return process_vimeo(link)
        else:
            bug('processing link as plain')
            r = requests.get(link, timeout=timeout)
            if r.status_code == 200:
                html = bs4.BeautifulSoup(r.text, "lxml")
                t = html.title.text
                return "`%s <%s>`__" % (t.strip(), link)
            else:
                return link
    except:
        return link

f = open(sys.argv[1])
try:
    # Read whole file as one string.
    data = f.read()
finally:
    # Close file
    f.close()

lines = data.split("\n")
for line in lines:
    if line:
        print linktitle(line)
        print ""
