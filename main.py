import csv, json, re, threading, webbrowser
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
import requests
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

VIDEO_RE = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?.*?v=|embed/|shorts/|live/))([A-Za-z0-9_-]{11})")

def video_id(value):
    value = value.strip()
    m = VIDEO_RE.search(value)
    if m: return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value): return value
    raise ValueError("Enter a valid YouTube video URL or 11-character video ID.")

def analyze(url):
    vid = video_id(url)
    canonical = f"https://www.youtube.com/watch?v={vid}"
    result = {
        "video_id": vid, "video_url": canonical,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "title": "", "channel": "", "channel_url": "", "upload_date": "",
        "description": "", "public_location_field": "", "latitude": None,
        "longitude": None, "location_evidence": [],
        "upload_location": {
            "status": "not_publicly_available",
            "details": "YouTube does not publicly expose an ordinary video's uploader IP address or exact physical upload location. This tool cannot determine it."
        },
        "limitations": [
            "A channel country is not proof of where a particular video was uploaded.",
            "A filming-location clue may be incomplete or inaccurate.",
            "Text in a description is not verified GPS evidence."
        ]
    }
    try:
        r = requests.get("https://www.youtube.com/oembed",
                         params={"url": canonical, "format": "json"}, timeout=20)
        r.raise_for_status()
        o = r.json()
        result.update(title=o.get("title", ""), channel=o.get("author_name", ""),
                      channel_url=o.get("author_url", ""))
    except Exception as e:
        result["oembed_note"] = str(e)

    if yt_dlp:
        try:
            opts = {"quiet": True, "no_warnings": True, "skip_download": True,
                    "noplaylist": True, "socket_timeout": 20}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(canonical, download=False)
            for key in ("title", "description", "upload_date"):
                if info.get(key): result[key] = info[key]
            result["channel"] = info.get("channel") or info.get("uploader") or result["channel"]
            result["channel_url"] = info.get("channel_url") or info.get("uploader_url") or result["channel_url"]
            loc = info.get("location")
            if loc:
                result["public_location_field"] = loc
                result["location_evidence"].append({
                    "type": "Public metadata location field", "value": loc,
                    "confidence": "Metadata-provided; not independently verified"})
            lat, lon = info.get("latitude"), info.get("longitude")
            if lat is not None and lon is not None:
                result["latitude"], result["longitude"] = lat, lon
                result["location_evidence"].append({
                    "type": "Public GPS coordinates", "value": {"latitude": lat, "longitude": lon},
                    "confidence": "Coordinates exposed in public metadata; verify independently"})
            desc = info.get("description") or ""
            result["description"] = desc
            clues = [re.sub(r"\s+", " ", x).strip()[:300] for x in desc.splitlines()
                     if re.search(r"location|filmed in|shot in|recorded in|place:|address:|📍", x, re.I)]
            if clues:
                result["location_evidence"].append({
                    "type": "Description text clues", "value": clues[:12],
                    "confidence": "Unverified text clues; may not describe filming location"})
        except Exception as e:
            result["metadata_note"] = f"Detailed metadata unavailable: {e}"

    if result["public_location_field"] or result["latitude"] is not None:
        result["filming_location_status"] = "public_location_metadata_found"
    elif result["location_evidence"]:
        result["filming_location_status"] = "possible_clues_found"
    else:
        result["filming_location_status"] = "not_found_in_public_metadata"
    return result

def map_url(data):
    if data.get("latitude") is not None and data.get("longitude") is not None:
        return f"https://www.google.com/maps?q={data['latitude']},{data['longitude']}"
    if data.get("public_location_field"):
        from urllib.parse import quote
        return "https://www.google.com/maps/search/?api=1&query=" + quote(data["public_location_field"])
    return None

def report(d):
    lines = [
        f"TITLE: {d.get('title') or 'Unavailable'}",
        f"CHANNEL: {d.get('channel') or 'Unavailable'}",
        f"CHANNEL URL: {d.get('channel_url') or 'Unavailable'}",
        f"VIDEO: {d['video_url']}", f"UPLOAD DATE: {d.get('upload_date') or 'Unavailable'}",
        "", "UPLOAD LOCATION", "NOT PUBLICLY AVAILABLE",
        d["upload_location"]["details"], "", "FILMING LOCATION",
        f"Status: {d.get('filming_location_status')}",
        f"Public location field: {d.get('public_location_field') or 'Not found'}",
        f"Coordinates: {d.get('latitude')}, {d.get('longitude')}", "",
        "LOCATION EVIDENCE / CLUES"
    ]
    if d["location_evidence"]:
        for item in d["location_evidence"]:
            lines += [f"- {item['type']}: {item['value']}", f"  Confidence: {item['confidence']}"]
    else: lines.append("No public filming-location evidence found.")
    lines += ["", "DESCRIPTION", d.get("description") or "Unavailable", "", "LIMITATIONS"]
    lines += ["- " + x for x in d["limitations"]]
    if d.get("metadata_note"): lines += ["", "NOTE", d["metadata_note"]]
    return "\n".join(lines)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTubeGeoX")
        self.geometry("980x730")
        self.minsize(760, 580)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.data = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        head = ctk.CTkFrame(self, corner_radius=14)
        head.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        ctk.CTkLabel(head, text="YouTubeGeoX", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=16, pady=(12, 0))
        ctk.CTkLabel(head, text="Public metadata & filming-location clue investigator", text_color="gray").pack(anchor="w", padx=16, pady=(0, 12))
        bar = ctk.CTkFrame(self, corner_radius=14)
        bar.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(bar, placeholder_text="Paste YouTube video URL…")
        self.entry.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="ew")
        self.go = ctk.CTkButton(bar, text="Analyze video", command=self.start)
        self.go.grid(row=0, column=1, padx=(8, 12), pady=12)
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, padx=18, pady=(2, 8), sticky="ew")
        self.status = ctk.CTkLabel(actions, text="Ready — no login required")
        self.status.pack(side="left")
        self.export_btn = ctk.CTkButton(actions, text="Export JSON / TXT / CSV", command=self.export, state="disabled")
        self.export_btn.pack(side="right", padx=4)
        self.map_btn = ctk.CTkButton(actions, text="Open map", command=self.open_map, state="disabled")
        self.map_btn.pack(side="right", padx=4)
        self.box = ctk.CTkTextbox(self, wrap="word")
        self.box.grid(row=3, column=0, padx=18, pady=(0, 10), sticky="nsew")
        self.show("Paste a YouTube video link and click Analyze video.\n\n"
                  "Upload location: YouTube does not publicly expose the uploader's IP or exact upload location.\n"
                  "Filming location: this app checks public location metadata, coordinates and description clues. "
                  "It will not invent a location if none is available.")
        ctk.CTkLabel(self, text="Upload IP/location is not public. Filming locations require public evidence.",
                     text_color="gray", font=ctk.CTkFont(size=11)).grid(row=4, column=0, padx=18, pady=(0, 12), sticky="w")

    def show(self, text):
        self.box.configure(state="normal")
        self.box.delete("1.0", "end")
        self.box.insert("1.0", text)
        self.box.configure(state="disabled")

    def start(self):
        try: video_id(self.entry.get())
        except ValueError as e:
            messagebox.showerror("Invalid URL", str(e)); return
        self.go.configure(state="disabled")
        self.export_btn.configure(state="disabled")
        self.map_btn.configure(state="disabled")
        self.status.configure(text="Analyzing public information…")
        self.show("Contacting public YouTube endpoints…")
        def work():
            try:
                data = analyze(self.entry.get())
                self.after(0, lambda: self.done(data))
            except Exception as e:
                self.after(0, lambda: self.failed(str(e)))
        threading.Thread(target=work, daemon=True).start()

    def done(self, data):
        self.data = data
        self.go.configure(state="normal")
        self.export_btn.configure(state="normal")
        if map_url(data): self.map_btn.configure(state="normal")
        self.status.configure(text="Analysis complete")
        self.show(report(data))

    def failed(self, error):
        self.go.configure(state="normal")
        self.status.configure(text="Analysis failed")
        self.show(error)
        messagebox.showwarning("YouTubeGeoX", error)

    def open_map(self):
        if self.data and map_url(self.data): webbrowser.open(map_url(self.data))

    def export(self):
        if not self.data: return
        folder = filedialog.askdirectory(title="Choose report folder")
        if not folder: return
        p = Path(folder); vid = self.data["video_id"]
        jf, tf, cf = p/f"YouTubeGeoX_{vid}.json", p/f"YouTubeGeoX_{vid}.txt", p/f"YouTubeGeoX_{vid}.csv"
        jf.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tf.write_text(report(self.data), encoding="utf-8")
        with cf.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(["field", "value"])
            for k, v in self.data.items():
                w.writerow([k, json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v])
        messagebox.showinfo("Export complete", f"Saved:\n{jf}\n{tf}\n{cf}")

if __name__ == "__main__":
    App().mainloop()
