import argparse, json
from pathlib import Path
from main import analyze, map_url

def main():
    p = argparse.ArgumentParser(description="YouTubeGeoX public location clue analyzer")
    p.add_argument("url", help="YouTube video URL or ID")
    p.add_argument("--output", default=".", help="Report output folder")
    a = p.parse_args()
    d = analyze(a.url)
    print("Title:", d.get("title") or "Unavailable")
    print("Channel:", d.get("channel") or "Unavailable")
    print("Upload date:", d.get("upload_date") or "Unavailable")
    print("Uploader physical upload location: NOT PUBLICLY AVAILABLE")
    print("Filming location status:", d.get("filming_location_status"))
    print("Public location:", d.get("public_location_field") or "Not found")
    print("Coordinates:", d.get("latitude"), d.get("longitude"))
    for clue in d.get("location_evidence", []): print("-", clue)
    if map_url(d): print("Map:", map_url(d))
    out = Path(a.output); out.mkdir(parents=True, exist_ok=True)
    vid = d["video_id"]
    (out/f"YouTubeGeoX_{vid}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    (out/f"YouTubeGeoX_{vid}.txt").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Reports saved to", out.resolve())

if __name__ == "__main__": main()
