audiodiff
=========

audiodiff is a small Python library for comparing audio files. Two audio flies
are considered equal if they have the same audio streams and normalized tags.


Dependencies
------------

audiodiff requires FFmpeg to be installed in your system. The path is
``ffmpeg`` by default, but you can change it by following ways (later rules
take precedence over earlier ones):

1. ``audiodiff.FFMPEG_BIN`` module property
2. ``FFMPEG_BIN`` environment variable
3. ``--ffmpeg_bin`` flag (commandline tool only)

You can install ``ffmpeg`` with following commands.

- Debian/Ubuntu: ``sudo apt-get install ffmpeg``
- OS X (with Homebrew_): ``brew install ffmpeg``

.. _Homebrew: http://brew.sh


Install
-------

audiodiff can be installed with ``pip``::

    $ pip install audiodiff

This will also install the commandline tool. Run ``audiodiff -h`` for help.


Examples
--------

Suppose you have two files, ``airplane.flac`` and ``airplane.m4a``. The second
one is obtained by converting the first one with an ALAC encoder, so its audio
stream should be identical with the first one's. After the conversion, you
changed the tags in the FLAC file. Then you may get the following results with
audiodiff::

    >>> import audiodiff
    >>> audiodiff.equal('airplane.flac', 'airplane.m4a')
    False
    >>> audiodiff.audio_equal('airplane.flac', 'airplane.m4a')
    True
    >>> audiodiff.tags_equal('airplane.flac', 'airplane.m4a')
    False

It means the two files are not the same because tha tags differ, but the audio
streams are identical.

If you want more information about those files, you can get stream checksums
and tags::

    >>> audiodiff.checksum('airplane.flac')
    'ed871b3c164998cf243e39d4b97d21f93bba9427'
    >>> audiodiff.checksum('airplane.m4a')
    'ed871b3c164998cf243e39d4b97d21f93bba9427'
    >>> tags1 = audiodiff.tags('airplane.flac')
    >>> tags1
    {'artist': 'f(x)', 'album': 'Pink Tape', 'title': 'Airplane'}
    >>> tags2 = audiodiff.tags('airplane.m4a')
    >>> tags2
    {'title': 'f(x) - Pink Tape - Airplane'}

It can also be used as a commandline tool. When used as a commandline tool,
it supports comparing audio files in two directories recursively. Audio files
with the same name except for the extension are compared to each other.

.. code-block:: console

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

Currently audiodiff recognizes only WAV, FLAC, M4A, and MP3 files as
audiofiles. They must have ``wav``, ``flac``, ``m4a``, ``mp3`` file extensions,
respectively. Note that WAV files are assumed to have no tags, because tagging
WAV files are inconsistent among many applications.


Caveats
-------

Tag reading is done by mutagenwrapper_ for which there isn't a stable
version yet. It may omit some tags, thus incorrectly reporting tags in files
being compared are equal while they are not.


.. _mutagenwrapper: https://mutagenwrapper.readthedocs.org/en/latest/


Changes
-------

.. include:: ../CHANGES


API reference
-------------

.. automodule:: audiodiff
   :members:
   :member-order: bysource

.. automodule:: audiodiff.commandlinetool
   :members:
   :member-order: bysource


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
