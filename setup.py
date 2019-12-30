#!/usr/bin/python3
# -*- coding: utf-8 -*-
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#       OS : GNU/Linux Ubuntu 16.04 or 18.04
# LANGUAGE : Python 3.5.2 or later
#   AUTHOR : Klim V. O.
#     DATE : 14.10.2019
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

import os
from setuptools import setup, find_packages


__version__ = 1.3


with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


install_requires = [
    'pydub==0.23.1',
    'webrtcvad==2.0.10',
    'librosa==0.7.1'
]


setup(
    name='webrtcvad-wrapper',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts':
            ['webrtcvad_wrapper = webrtcvad_wrapper.cli:cli']
        },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
    version=__version__,
    install_requires=install_requires,
    description='WebRTCVAD-Wrapper is a simple wrapper to simplify working with WebRTCVAD',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Vlad Klim',
    author_email='valdsklim@gmail.com',
    license='Apache 2.0',
    url='https://github.com/Desklop/WebRTCVAD_Wrapper',
    keywords='vad voice-activity-detection silence-suppression webrtc rtc dsp audio audio-processing wav nlp',
    project_urls={
        'Source': 'https://github.com/Desklop/WebRTCVAD_Wrapper',
    }
)


print('\nWebRTCVAD-Wrapper is ready for work and defense!')
print('All information about the module is available at https://github.com/Desklop/WebRTCVAD_Wrapper')

# To build package run: python3 setup.py sdist
