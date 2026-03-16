# Project Overview

ArchiveTube will be a self-hosted, personal YouTube archive, designed primarily for personal collections.

The goal of ArchiveTube is to create an offline archive that lets users browse, search, and watch archived YouTube content as well as provide the tools for archiving using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

Unlike others, ArchiveTube focuses on being user-friendly and maintaining an organized archive with as much detail as possible.

## Goals

ArchiveTube is designed with several ideas in mind:

- Preserve YouTube videos and channel content for long-term personal archiving
- Store as much metadata as possible
- Provide a user-friendly web interface for browsing archived content
- Allow offline playback of archived videos
- Track user viewing history and statistics
- Detect videos that have been removed/deleted/privated from YouTube
- Detect changes in the archive (videos/files removed/missing)
- Support manual and scheduled metadata updates
- Detect changes in the filesystem and allow importing of new videos or files

## Components

### Archive Storage

Storage organizes downloaded videos and channel data into a structured folder layout designed for easy identification.

### Metadata System

Metadata is stored for each video and channel, allowing the archive to preserve titles, descriptions, upload dates, thumbnails, subtitles, and other information.

### Indexing System

An indexing system allows the archive to quickly search and filter videos using stored metadata.

### Web Interface

A browser-based interface allows users to browse channels, watch videos, and explore the archive.

### Admin System

Administrative tools allow users to archive new videos, update metadata, and manage the archive.

## Documentation

Detailed documentation for each system can be found in the `/docs` directory.

## Status

ArchiveTube is currently in early planning and development.
