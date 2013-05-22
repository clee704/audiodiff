=========
audiodiff
=========

audiodiff is a commandline tool that compares two audio files and prints
info whether audio streams and/or tags differ. It can compare two directories
recursively, like ``diff -r``. When doing it recursively, it compares files
with the same name, even the extensions differ (e.g. ``a/c/d.flac`` and
``b/c/d.mp4`` will be compared, unlike ``diff -r``).
You can choose to compare only audio streams, tag contents, or both.

This tool is useful to confirm that lossless conversion is done successfully,
or to compare audio files with backed up data.

You have to install audiotools_ to compare audio streams.

.. _audiotools: http://audiotools.sourceforge.net/install.html
