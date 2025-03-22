#!/usr/bin/env python3
"""
Setup script for Music RPC
"""
from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    name="music-rpc",
    version="2.0.0",
    author="Jakub Sladek",
    description="Discord Rich Presence for Music Players",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/music-rpc",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "music-rpc=deezer_rpc.main:main",
        ],
    },
    include_package_data=True,
) 