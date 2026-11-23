#!/usr/bin/env python3
"""Pone la portada de Reels como PRIMER fotograma del video, sin recodificar el clip original.

Instagram solo acepta la portada como URL pública; este método no necesita alojarla: el Reel se publica con
thumb_offset=0, así la portada es ese primer fotograma (1/60 s, imperceptible al reproducir).
Uso: python pipeline/ig_cover_frame.py <clip.mp4> <portada_REELS_1080x1920.jpg> <salida.mp4>
Requiere que clip y portada sean 1080x1920 y que el clip sea del render de edit.py (h264 yuv420p 60 fps + AAC 48 kHz).
"""
import json
import subprocess
import sys
import tempfile
import os


def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                   "stream=codec_type,width,height,r_frame_rate,pix_fmt,sample_rate,channels",
                                   "-of", "json", path])
    s = json.loads(out)["streams"]
    v = next(x for x in s if x["codec_type"] == "video")
    a = next((x for x in s if x["codec_type"] == "audio"), None)
    return v, a


def main(clip, cover, out):
    v, a = probe(clip)
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    d = tempfile.mkdtemp()
    seg = os.path.join(d, "cover_seg.mp4")
    dur = 1.0 / fps
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(fps), "-i", cover]
    if a:
        cmd += ["-f", "lavfi", "-i", f"anullsrc=r={a['sample_rate']}:cl={'stereo' if int(a['channels']) == 2 else 'mono'}"]
    cmd += ["-frames:v", "1", "-vf", f"scale={v['width']}:{v['height']},format={v['pix_fmt']}",
            "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", v["pix_fmt"], "-r", str(fps)]
    if a:
        cmd += ["-t", f"{dur:.5f}", "-c:a", "aac", "-b:a", "192k", "-ar", a["sample_rate"], "-ac", str(a["channels"])]
    cmd += ["-video_track_timescale", "15360", seg]
    subprocess.check_call(cmd)
    lst = os.path.join(d, "list.txt")
    with open(lst, "w") as f:
        f.write(f"file '{seg}'\nfile '{os.path.abspath(clip)}'\n")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                           "-c", "copy", "-movflags", "+faststart", out])
    print(out)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
