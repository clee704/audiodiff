audiodiff
=========

audiodiff is a library that can be used to compare audio files.

Examples::

    >>> import audiodiff
    >>> audiodiff.equal('airplane.flac', 'airplane.m4a')
    False
    >>> audiodiff.audioequal('airplane.flac', 'airplane.m4a')
    True
    >>> audiodiff.tagsequal('airplane.flac', 'airplane.m4a')
    False
    >>> audiodiff.checksum('airplane.flac')
    'ffa0d242f8642b20e90f521a898a0ab5'
    >>> audiodiff.checksum('airplane.m4a')
    'ffa0d242f8642b20e90f521a898a0ab5'
    >>> audiodiff.tags('airplane.flac')
    {'artist': 'f(x)', 'album': 'Pink Tape', 'title': 'Airplane'}
    >>> audiodiff.tags('airplane.m4a')
    {'title': 'f(x) - Pink Tape - Airplane'}
    >>> audiodiff.tagsdiff('airplane.flac', 'airplane.m4a')
    --- airplane.flac
    +++ airplane.m4a
    -artist: f(x)
    -album: Pink Tape
    -title: Airplane
    +title: f(x) - Pink Tape - Airplane

It can be also used as a commandline tool. When used as a commandline tool,
it supports comparing audio files in two directories recursively. Audio files
with the same name except for the extensions are considered to be compared.

Commandline examples::

    $ ls . -R
    mylib1:
    a.flac  b.flac  cover.jpg

    mylib2:
    a.m4a  b.m4a  cover.jpg
    $ audiodiff mylib1 mylib2
    Audio streams in mylib1/a.flac and mylib2/a.m4a differ
    Audio streams in mylib1/b.flac and mylib2/b.m4a differ
    --- mylib1/b.flac
    +++ mylib2/b.m4a
    -album: [u'Purple Heart']
    +album: [u'Blue Jean']
    +date: [u'2001']
    Binary files mylib1/cover.jpg and mylib2/cover.jpg differ


Supported audio formats
-----------------------

Currently audiodiff can only read FLAC, M4A, MP3 files.


Caveats
-------

Tag reading is done by mutagenwrapper_ for which there isn't a stable
version yet. It may omit some tags, thus incorrectly reporting tags in files
being compared are equal while they are not.


.. _mutagenwrapper: https://mutagenwrapper.readthedocs.org/en/latest/


Install
-------

audiodiff can be installed with `pip`. To install, run:

    pip install audiodiff

For help using the commandline tool, run ``audiodiff -h``.


Dependencies
------------

audiodiff requires `ffmpeg` to be installed in your system. The path is
``ffmpeg`` by default, but you can change it by following ways (later rules
take precedence over earlier ones):

1. ``audiodiff.FFMPEG_BIN`` module property
2. ``FFMPEG_BIN`` environment variable
3. ``--ffmpeg_bin`` flag (commandline tool only)
