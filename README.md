﻿Negar-GUI
==============
[![code size](https://img.shields.io/github/languages/code-size/javadr/negar-gui?style=social)](https://github.com/javadr/negar-gui/archive/master.zip)
[![GitHub forks](https://img.shields.io/github/forks/javadr/negar-gui?style=social)](https://github.com/javadr/negar-gui/network/members)
[![GitHub license](https://img.shields.io/github/license/javadr/negar-gui?style=social)](https://github.com/javadr/negar-gui/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/javadr/negar-gui?style=social)](https://github.com/javadr/negar-gui/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/javadr/negar-gui?style=social)](https://github.com/javadr/negar-gui/issues)
[![Downloads](https://pepy.tech/badge/negar-gui)](https://pepy.tech/project/negar-gui)

Graphical User interface for `negar`


![Negar's English view](https://raw.github.com/javadr/negar-gui/master/images/negar-en.png)
![Negar's Persian view](https://raw.github.com/javadr/negar-gui/master/images/negar-fa.png)

Installation
==============

## PyPi

**python-negar** is available on [PyPi](http://pypi.python.org/pypi/negar-gui):

    $ pip install negar-gui

## Git

You can get latest stable changes from github server:

    $ git clone https://github.com/javadr/negar-gui.git
    $ cd negar-gui
    $ python setup.py install

## Zip, Tarball

You can download the latest tarball.

### *nix

Get the latest tarball & install:

    $ wget -O negar-gui-master.tar.gz https://github.com/javadr/negar-gui/archive/master.tar.gz
    $ tar xvzf negar-gui-master.tar.gz && cd negar-gui-master
    $ python setup.py install

### Windows

Download latest zip archive.

https://github.com/javadr/negar-gui/archive/master.zip

Decompress it, and run the following command in root directory of `negar-gui`

    $ python setup.py install

#### Requirements
The GUI is relied on `python-negar` as well as `PyQt5`, `pyperclip`, `pyuca`, `regex`.
If you want to just run it by calling the script, you need to install its dependencies.

    $ pip install python-negar PyQt5 pyuca pyperclip regex

## Usage
Just use one of the following in your terminal.

    $ negar-gui

or simply

    $ negar
