# Archive Structure

## Purpose

This document details how all downloaded content is stored.

It is designed to:

- Support multiple platforms (YouTube, Twitch, etc.)*
  1. *(Although only YouTube for now)
- Keep data organized and easily readable/explorable
- Avoid naming conflicts
- Support long-term archival and preservation

---

## Root Structure

All archived content is stored inside the main `archive/`* directory.

*`archive/` is just an example of the root directory

```
archive/
 ├─ youtube/
 └─ twitch/   (possible in future)
```

Each platform has its own dedicated directory.

---

## Platform Structure

### YouTube

```
archive/
 └─ youtube/
    └─ ChannelName [ChannelID]/
```

Each channel is stored in a folder using the format:

```
ChannelName [ChannelID]
```

Example:

```
Achievement Hunter [UCsB0LwkHPWyjfZ-JwvtwEXw]
```

- Unique identification (ChannelID)
- Readable names (ChannelName)

---

## Channel Structure

```
ChannelName [ChannelID]/
 ├─ channel.info.json
 ├─ channel.jpg
 ├─ banners/
 └─ videos/
```

### Files

- `channel.info.json`  
  Full metadata for the channel

- `channel.jpg`  
  Default channel icon

---

### Banners

```
banners/
 ├─ banner_small.jpg
 ├─ banner_medium.jpg
 └─ banner_large.jpg
```

Multiple banner sizes are stored for different UI usages.

---

# Video Folder Contents

## Video Structure

```
videos/
 └─ VideoID/
```

Each video is stored in its own folder using its YouTube Video ID.

Example:

```
videos/
 └─ edvpnfvmEYU/
```

---


## Optional Components

Not all videos will contain every file or folder.

Depending on user settings and availability, a video may include:

- Video file (`.mp4`)
- Subtitles
- Preview sprites
- Chat data

The system will be designed to handle missing components.

---

## Chat Data (Optional)

```
VideoID/
 └─ chat.json
```

Chat data may be stored for videos that support it (such as livestreams).

This allows future support for:

- Chat replay synchronized with video playback
- Stream-style viewing experiences

Chat storage is optional and depends on availability and user settings.

---

## Video Folder Contents

```
VideoID/
 ├─ VideoID.mp4
 ├─ VideoID.info.json
 ├─ VideoID.jpg
 ├─ VideoID.description
 │
 ├─ subtitles/
 ├─ previews/
 └─ history/
```

### Video File Presence

It is not required to store all videos locally.

Possible cases:

- Fully archived videos will include `VideoID.mp4`
- Metadata-only videos will NOT include a video file

This allows ArchiveTube to support:

- Streaming with YouTube embed
- Partial archives
- Storage-efficient collections

---

### Core Files

- `VideoID.mp4`  
  The video file

- `VideoID.info.json`  
  Metadata from yt-dlp

- `VideoID.jpg`  
  Thumbnail image

- `VideoID.description`  
  Video description

---

## Subtitles

```
subtitles/
 ├─ VideoID.en.vtt
 └─ VideoID.en-orig.vtt
```

Subtitles are stored in VTT format.

Languages and availability are user-configurable.

---

## Preview System

```
previews/
 ├─ sprite_0.jpg
 ├─ sprite_1.jpg
 └─ index.json
```

Preview sprites are generated using ffmpeg.

- Each sprite contains multiple frames
- `index.json` maps timestamps to sprite positions

This enables timeline hover previews for local video files.

---

## History System (Planned)

```
history/
```

This folder stores historical metadata changes.

Examples:

- title changes
- description updates
- thumbnail changes
- view count tracking

This system allows ArchiveTube to:

- track metadata over time
- detect changes between updates

---

## Design Notes

- All files are stored in a user-friendly format
- Folder structure is consistent
- Video files are never overwritten automatically
- Metadata can be updated without affecting video files
- The structure supports future platforms without modification
- New videos and files can be added manually, as long as they follow the expected folder and file structure.

---

## Future Platforms

This project may include other platforms in the future, such as Twitch

Additional platforms (such as Twitch) will follow the same pattern:

```
archive/
 ├─ youtube/
 └─ twitch/
```

Each platform may define its own internal structure depending on its data requirements.


## Full Example Structure

This example shows a realistic archive layout with both fully archived and metadata-only videos.

```
archive/
│
├─ youtube/
│   │
│   ├─ Achievement Hunter [UCsB0LwkHPWyjfZ-JwvtwEXw]/
│   │   │
│   │   ├─ channel.info.json
│   │   ├─ channel.jpg
│   │   │
│   │   ├─ banners/
│   │   │   ├─ banner_small.jpg
│   │   │   ├─ banner_medium.jpg
│   │   │   └── banner_large.jpg
│   │   │
│   │   └── videos/
│   │       │
│   │       ├─ edvpnfvmEYU/
│   │       │   ├─ edvpnfvmEYU.mp4
│   │       │   ├─ edvpnfvmEYU.info.json
│   │       │   ├─ edvpnfvmEYU.jpg
│   │       │   ├─ edvpnfvmEYU.description
│   │       │   │
│   │       │   ├─ subtitles/
│   │       │   │   ├─ edvpnfvmEYU.en.vtt
│   │       │   │   └── edvpnfvmEYU.en-orig.vtt
│   │       │   │
│   │       │   ├─ previews/
│   │       │   │   ├─ sprite_0.jpg
│   │       │   │   ├─ sprite_1.jpg
│   │       │   │   └── index.json
│   │       │   │
│   │       │   └── chat.json
│   │       │
│   │       └── sB-iLoXCvfo/
│   │           ├─ sB-iLoXCvfo.info.json
│   │           ├─ sB-iLoXCvfo.jpg
│   │           │
│   │           └── (no video file - metadata only)
│   │
│   └── Rooster Teeth [UCzH3iADRIq1IJlIXjfNgTpA]/
│       └── ...
│
└── twitch/   (future)
```
