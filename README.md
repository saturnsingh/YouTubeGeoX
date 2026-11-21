# YouTubeGeoX

Python GUI + CLI utility to inspect publicly available clues about a YouTube video's filming location.

## Important distinction

- **Physical upload location / uploader IP:** YouTube does not publicly expose the IP address or exact physical place from which an ordinary video was uploaded. YouTubeGeoX cannot determine this.
- **Filming location:** Sometimes public metadata contains a location or GPS coordinates, or the creator mentions a place in the description. The tool reports those clues and labels them as unverified where appropriate.
- A channel's country, language, or audience is not proof of where a particular video was uploaded or filmed.

No login, Google password, private session, or access-control bypass is used. YouTube may rate-limit anonymous requests, so retrieval is not guaranteed.

## Features

- Paste YouTube URL or video ID
- Retrieve public title, channel, upload date and description
- Check public location fields and GPS coordinates when exposed
- Highlight location-related description lines as unverified clues
- Open Google Maps when a public location is available
- Export JSON, TXT and CSV
- CustomTkinter GUI and CLI
- Windows, Linux and Termux support (CLI recommended on Termux)

## Windows

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

CLI:
```bat
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Linux

```bash
sudo apt update
sudo apt install python3 python3-venv python3-tk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

CLI:
```bash
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Android Termux

CLI is recommended on standard Termux:

```bash
pkg update
pkg install python
python -m pip install --upgrade pip
pip install -r requirements-termux.txt
python cli.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

GUI requires Termux:X11 and compatible Tk/CustomTkinter support. This varies by device and setup.

## Troubleshooting

- Private, age-restricted or unavailable videos may not expose metadata.
- If YouTube rate-limits requests, wait and retry retry; update yt-dlp with `pip install -U yt-dlp`.
- If no filming location is found, the video may simply have no public geotag or location clue.
- The map button appears only when public coordinates or a location field is available.

## Disclaimer

Independent project; not affiliated with YouTube or Google. Respect creators' privacy and applicable platform terms.
