#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys

try:
    from urllib.request import urlopen
except ImportError:
    # For Python 2
    from urllib2 import urlopen


SYSTEMS = {
    'ubuntu14.04': {'base': 'ubuntu:14.04'},
    'ubuntu16.04': {'base': 'ubuntu:16.04'},
    'ubuntu17.04': {'base': 'ubuntu:17.04'},
    'centos6':     {'base': 'centos:6'},
    'centos7':     {'base': 'centos:7'},
}

CUDA = ['6.5', '7.0', '7.5', '8.0', '9.0', '9.1']
CUDNN = ['2', '3', '4', '5', '6', '7']

_verbose = False


def _log(msg):
    if _verbose:
        sys.stderr.write('{}\n'.format(msg))


def _fetch_file(url):
    _log('Downloading: {}'.format(url))
    return urlopen(url).read().decode()


def _fetch_dockerfile(url):
    lines = []
    for line in _fetch_file(url).splitlines():
        if (line == 'ARG repository' or
                line.startswith('FROM ') or
                line.startswith('LABEL maintainer ')):
            _log('Stripped: {}'.format(line))
            continue
        lines.append(line)
    return lines


def _generate_dockerfile(urls, os, base_image, user):
    default_image = SYSTEMS[os]['base']
    lines = [
        '# FROM {}'.format(default_image),
        'ARG image={}'.format(
            default_image if base_image is None else base_image),
        'FROM ${image}',
        '',
        'USER root',
    ]

    for url in urls:
        lines += [
            '',
            '###',
            '### {}'.format(url),
            '###',
        ] + _fetch_dockerfile(url)

    if user is not None:
        lines += [
            '',
            '###',
            '### Reset User and Group',
            '###',
            'USER {}'.format(user),
        ]

    return '\n'.join(lines)


def _generate_urls(conf):
    stages = []
    assets = []

    # Dockerfiles.
    base_available = conf.cuda.startswith('9.')
    if base_available:
        stages += ['base']

    if conf.variant == 'base':
        assert base_available
        assert conf.cudnn == 'none'
    elif conf.variant == 'runtime':
        stages += ['runtime']
    elif conf.variant == 'devel':
        stages += ['runtime', 'devel']

    if conf.cudnn != 'none':
        stages.append('{}/cudnn{}'.format(stages[-1], conf.cudnn))

    # Assets
    if conf.os.startswith('centos'):
        assets += ['{}/cuda.repo'.format(stages[0])]

    # Translate to URL.
    df_urls = [
        'https://gitlab.com/nvidia/cuda/raw/{}/{}/{}/Dockerfile'.format(
            conf.os, conf.cuda, stage)
        for stage in stages
    ]

    asset_urls = [
        'https://gitlab.com/nvidia/cuda/raw/{}/{}/{}'.format(
            conf.os, conf.cuda, asset)
        for asset in assets
    ]

    return df_urls, asset_urls


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--os', type=str, required=True,
        choices=sorted(SYSTEMS.keys()),
        help='CUDA distribution')
    parser.add_argument(
        '--cuda', type=str, required=True,
        choices=CUDA,
        help='CUDA version')
    parser.add_argument(
        '--cudnn', type=str, default='none',
        choices=(CUDNN + ['none']),
        help='cuDNN version')
    parser.add_argument(
        '--variant', type=str, default='devel',
        choices=['base', 'runtime', 'devel'],
        help='Image variant')
    parser.add_argument(
        '--base', type=str, default=None,
        help='Base Docker image')
    parser.add_argument(
        '--user', type=str, default=None,
        help='User and group to use when running the image; specify '
             '<user>[:<group>] or <UID>[:<GID>]')
    parser.add_argument(
        '--output', type=str, default='.',
        help='Path to the output directory')
    parser.add_argument(
        '--verbose', action='store_true', default=False,
        help='Log verbosely')

    return parser.parse_args(args)


def main(args):
    global _verbose
    conf = parse_args(args[1:])
    _verbose = conf.verbose

    df_urls, asset_urls = _generate_urls(conf)

    _log('-------------------------------')
    _log('Dockerfiles to be concatenated:')
    for url in df_urls:
        _log('  {}'.format(url))
    _log('Assets to be retrieved:')
    for url in asset_urls:
        _log('  {}'.format(url))
    _log('-------------------------------')

    # Download resources.
    dockerfile = _generate_dockerfile(df_urls, conf.os, conf.base, conf.user)
    assets = [_fetch_file(url) for url in asset_urls]

    # Output.
    path = '{}/Dockerfile'.format(conf.output)
    _log('Writing: {}'.format(path))
    with open(path, 'w') as f:
        f.write(dockerfile)

    for (url, data) in zip(asset_urls, assets):
        path = '{}/{}'.format(conf.output, os.path.basename(url))
        _log('Writing: {}'.format(path))
        with open(path, 'w') as f:
            f.write(data)

    _log('Done!')


if __name__ == '__main__':

    main(sys.argv)
