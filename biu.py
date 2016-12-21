#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: orange

import argparse
import datetime
import glob
import json
import os
from multiprocessing import Pool
from xml.etree.ElementTree import ParseError

import ipaddress
import requests

import defusedxml.cElementTree as ET

today = str(datetime.datetime.today()).split(' ')[0].replace('-', '.')

targets = []


def parse_crossdomain(target):
    url = 'http://{}/crossdomain.xml'.format(target)
    response = requests.get(url, timeout=1).text
    try:
        response = requests.get(url, timeout=1).text
        if "cross-domain-policy" in response:
            dom = ET.fromstring(response)
            elems = dom.findall(".//allow-access-from")
            for el in elems:
                target = el.get('domain').replace('*', 'www')
                generate_url(target)
    except:
        pass


def generate_url(target):
    if target in targets:
        return
    else:
        targets.append(target)
    for plugin in plugins:
        urls = []
        with open(plugin) as f:
            plugin = json.load(f)
        if plugin['port'] == [80]:
            urls.append('http://{}{}'.format(target, plugin['suffix']))
        else:
            for port in plugin['port']:
                urls.append('http://{}:{}{}'.format(target, port, plugin[
                    'suffix']))
        for url in urls:
            audit(url, plugin)


def audit(url, plugin):
    try:
        if plugin['method'] in ['GET']:
            http = requests.get
        else:
            http = requests.post
        # response = http(url, timeout=1,verify=False).text
        response = http(url, timeout=1).text
        for hit in plugin['hits']:
            if hit not in response:
                pass
            else:
                print('\033[0;92m[+]{}\t[{}]'.format(url, plugin['name']))
                with open('reports/result_{}_{}.txt'.format(
                        plugin['name'], today), 'a+') as result_file:
                    result_file.writelines(url + '\n')
                break
            print('\033[0;31m[-] \033[0;29m{}'.format(url))
    except:
        pass


if __name__ == '__main__':
    plugins = glob.glob("./plugins/*.json")
    parser = argparse.ArgumentParser(description='Biu~')
    parser.add_argument('-f', help='目标文件: 每行一个ip或域名')
    parser.add_argument('-d', help='目标: example.com或233.233.233.233')
    parser.add_argument('-a', help='ip范围: 233.233.233.233/24')
    args = parser.parse_args()
    p = Pool(10)
    if args.f:
        domain_file = args.f
        with open(domain_file, 'r') as f:
            for target in f.readlines():
                target = target.strip('\n').strip('\t').strip(' ')
                p.apply_async(generate_url, (target, ))
                p.apply_async(parse_crossdomain, (target, ))
        p.close()
        p.join()
    elif args.d:
        generate_url(args.d)
    elif args.a:
        for target in ipaddress.IPv4Network(args.a):
            p.apply_async(generate_url, (str(target), ))
            p.apply_async(parse_crossdomain, (str(target), ))
        p.close()
        p.join()
    else:
        pass