.. audiodiff documentation master file, created by
   sphinx-quickstart on Thu Jan 31 11:29:44 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to audiodiff's documentation!
=====================================

audiodiff is a commandline tool that compares two audio files and prints
the difference.

Example::

    ~$ ls . -R
    mylib1:
    a.flac  b.flac  cover.jpg

    mylib2:
    a.m4a  b.m4a  cover.jpg
    ~$ audiodiff mylib1 mylib2
    Audio streams in mylib1/a.flac and mylib2/a.m4a differ
    Audio streams in mylib1/b.flac and mylib2/b.m4a differ
    --- mylib1/b.flac
    +++ mylib2/b.m4a
    -album: [u'Purple Heart']
    +album: [u'Blue Jean']
    +date: [u'2001']
    Binary files mylib1/cover.jpg and mylib2/cover.jpg differ


API reference
-------------

.. automodule:: audiodiff
   :members:


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

