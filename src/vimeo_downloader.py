#! /usr/bin/env python

# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals
import argparse  # NOQA
import logging
import sys
import os
from os import path

import shutil

from pprint import pprint

# data = json.load(open('data.json'))

import json

#from json import json.JSONDecoder
#import json.decoder
#from json.decoder import WHITESPACE
import requests
import base64

if sys.version_info >= (3, 0):
    import io
    FILE=io.IOBase
    import urllib.parse as urlparse

else: 
    FILE=file #  io.IOBase
    import urlparse


def resolveComponents(url):
    """
    >>> resolveComponents('http://www.example.com/foo/bar/../../baz/bux/')
    'http://www.example.com/baz/bux/'
    >>> resolveComponents('http://www.example.com/some/path/../file.ext')
    'http://www.example.com/some/file.ext'
    """
    parts = list(urlparse.urlparse(url))
    parts[2] = os.path.normpath(parts[2].replace('/', os.sep)).replace(os.sep, '/')
    return urlparse.urlunparse(parts)

#    return os.path.normpath(url)
    import posixpath

    parsed = urlparse.urlparse(url)
    new_path = posixpath.normpath(parsed.path)
    if parsed.path.endswith('/'):
        # Compensate for issue1707768
        new_path += '/'
    cleaned = parsed._replace(path=new_path)
    return cleaned.geturl()


#hasattr(string_or_fp, 'read'): #): # 
import subprocess

def iterload(string_or_fp, cls=json.JSONDecoder, **kwargs):
    if  isinstance(string_or_fp, FILE):
#        print('file!!??')
        string = string_or_fp.read()
    else:
            string = str(string_or_fp)

#    print(string)

    decoder = cls(**kwargs)
    idx = json.decoder.WHITESPACE.match(string, 0).end()
    while idx < len(string):
        obj, end = decoder.raw_decode(string, idx)
        yield obj
        idx = json.decoder.WHITESPACE.match(string, end).end()



def my_json_parse(j, url):
    url = url[0:url.rfind("/")] + '/'
#    url = url + '/'
    print('base url: ', url)

    assert 'audio' in j
    assert 'video' in j
    assert 'clip_id' in j
    assert 'base_url' in j

#    for k in j:
#        print(k)
#        if k not in ['video', 'audio']:
#            pprint({ k: j[k] })

    v = j['video']
    a = j['audio']

    aa = None

    for i in a:
#        pprint(i.keys())
        # 'init_segment', 'segments',
        assert 'id' in i
        f = open("a_{}.list".format(i['id']), "w")

        for k in ['clip_id' , 'base_url']:
            assert k in j
            f.write("### {0}: {1}\n".format(k,j[k]))

        for k in ['avg_bitrate', 'id', 'bitrate', 'codecs', 'mime_type', 'channels', 'sample_rate', 'max_segment_duration', 'base_url', 'format', 'duration']:
            assert k in i
            f.write("## {0}: {1}\n".format(k,i[k]))
        assert 'segments' in i
#        for s in sorted(i['segments'], key=(lambda x: x['start'])):
        for s in i['segments']:
            assert 'url' in s
            assert 'end' in s
            assert 'start' in s
            f.write("# start: {0}, end: {1}\n".format(s['start'], s['end']))
            f.write(resolveComponents("{3}{2}{1}{0}".format(s['url'], i['base_url'], j['base_url'], url)))
            f.write("\n")
        f.close()
        assert 'init_segment' in i
        f = open("a_{}.init".format(i['id']), "wb")
#        f.write(i['init_segment'])
        f.write(base64.b64decode(i['init_segment']))
        f.close()

        if aa is None:
            aa = i
        elif aa['bitrate'] < i['bitrate']:
            aa = i

    print("best audio: a_{0}.list/init".format(aa['id']))


    vv = None

    for i in v:
#        pprint(i.keys())
        # 'init_segment',  'segments', 
        assert 'id' in i
        f = open("v_{}.list".format(i['id']), "w")

        for k in ['clip_id' , 'base_url']:
            assert k in j
            f.write("### {0}: {1}\n".format(k,j[k]))

        for k in ['avg_bitrate', 'width', 'id', 'bitrate', 'height', 'codecs', 'mime_type', 'format', 'max_segment_duration', 'base_url', 'framerate', 'duration']:
            assert k in i
            f.write("## {0}: {1}\n".format(k,i[k]))
        assert 'segments' in i
        for s in sorted(i['segments'], key=(lambda x: x['start'])):
            assert 'url' in s
            assert 'end' in s
            assert 'start' in s
#            f.write("# start: {0}, end: {1}\n{5}{4}{3}{2}\n".format(s['start'], s['end'], s['url'], i['base_url'], j['base_url'], url))
            f.write("# start: {0}, end: {1}\n".format(s['start'], s['end']))
            f.write(resolveComponents("{3}{2}{1}{0}".format(s['url'], i['base_url'], j['base_url'], url)))
            f.write("\n")

        f.close()
        assert 'init_segment' in i
        f = open("v_{}.init".format(i['id']), "wb")
        f.write(base64.b64decode(i['init_segment']))
        f.close()

        if vv is None:
            vv = i
        elif vv['bitrate'] < i['bitrate']:
            vv = i

    print("best video: v_{0}.list/init".format(vv['id']))

    if url.startswith('http'):
        f = open("a_{}.m4a".format(aa['id']), "wb")
        f.write(base64.b64decode(aa['init_segment']))
        for s in sorted(aa['segments'], key=(lambda x: x['start'])):
            u = resolveComponents("{3}{2}{1}{0}".format(s['url'], aa['base_url'], j['base_url'], url))
            r = requests.get(u, stream=True)
            if r.status_code != 200:
                print('ERROR: could not get ['+ u +']!')
            else:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        f.close()

        f = open("v_{}.mp4".format(vv['id']), "wb")
        f.write(base64.b64decode(vv['init_segment']))
        for s in sorted(vv['segments'], key=(lambda x: x['start'])):
            u = resolveComponents("{3}{2}{1}{0}".format(s['url'], vv['base_url'], j['base_url'], url))
            r = requests.get(u, stream=True)
            if r.status_code != 200:
                print('ERROR: could not get ['+ u +']!')
            else:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        f.close()

        subprocess.check_output(['ffmpeg', '-i', "a_{}.m4a".format(aa['id']), '-i', "v_{}.mp4".format(vv['id']), '-c:v', 'copy', '-c:a', 'copy', "{0}.mp4".format(j['clip_id'])])




import argparse
parser = argparse.ArgumentParser()
parser.add_argument("url", nargs='?', default=None)
args = parser.parse_args()

#print(args)

if args.url is None:

    for o in iterload(sys.stdin):
        my_json_parse(o, '')

else:
    try:
        url = str(args.url)
#        print(url)
        r = requests.get(url)
        string = r.text
#        print()
#        print(string)
#        print()
        my_json_parse(r.json(), url)
#        print()

    except BaseException as e:
        print("EXCEPTION: ", e)
        sys.exit(1)
