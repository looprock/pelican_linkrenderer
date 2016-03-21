#!/usr/bin/env python
"""Process links in a file for pelican formatting."""
import requests
import bs4
import sys
import re

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
    except:
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
        v = ""
        if gettitle(link):
            v += "**%s**\n" % gettitle(link)
            v += " "
        x = re.match(r'^(.*)?v=([A-Za-z0-9_-]+)(.*)', link)
        bug('youtube ID: %s' % x.group(2))
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
