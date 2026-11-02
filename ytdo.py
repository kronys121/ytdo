"""YouTube downloader: обычные видео и Shorts с выбором качества."""

import os
import sys

try:
    import yt_dlp
except ImportError:
    print("Не найден yt-dlp. Запустите install.bat.")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "Downloads")


def setup_console():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def human_size(num):
    if not num:
        return "?"
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if num < 1024:
            return f"{num:.0f} {unit}" if unit in ("Б", "КБ") else f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} ТБ"


def human_duration(sec):
    if not sec:
        return "?"
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def base_opts():
    opts = {
        "noplaylist": True,
        "windowsfilenames": True,
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 4,
    }
    if FFMPEG:
        opts["ffmpeg_location"] = FFMPEG
    return opts


def fetch_info(url):
    opts = base_opts()
    opts.update({"quiet": True, "no_warnings": True, "skip_download": True})
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise RuntimeError("Плейлист пуст")
        info = entries[0]
    return info


def is_vertical(info):
    w, h = info.get("width"), info.get("height")
    if w and h:
        return h > w
    return False


def is_short(url, info):
    if "/shorts/" in url or "/shorts/" in (info.get("webpage_url") or ""):
        return True
    return is_vertical(info) and (info.get("duration") or 0) <= 180


def collect_qualities(info, vertical):
    """Вернуть список (метка_качества, fps, размер), отсортированный по убыванию."""
    best_audio = 0
    for f in info.get("formats") or []:
        if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none"):
            best_audio = max(best_audio, f.get("filesize") or f.get("filesize_approx") or 0)

    by_q = {}
    for f in info.get("formats") or []:
        if f.get("vcodec") in (None, "none"):
            continue
        w, h = f.get("width"), f.get("height")
        if not h:
            continue
        q = min(w, h) if (w and vertical) else h
        size = f.get("filesize") or f.get("filesize_approx") or 0
        if f.get("acodec") in (None, "none") and size:
            size += best_audio
        fps = f.get("fps") or 0
        cur = by_q.get(q)
        if cur is None or (fps, size) > (cur[0], cur[1]):
            by_q[q] = (fps, size)
    return [(q, v[0], v[1]) for q, v in sorted(by_q.items(), reverse=True)]


def build_selector(q, vertical):
    dim = "width" if vertical else "height"
    return f"bv*[{dim}<={q}]+ba/b[{dim}<={q}]/bv*+ba/b"


def choose(info, url):
    vertical = is_vertical(info)
    short = is_short(url, info)
    qualities = collect_qualities(info, vertical)

    print()
    print(f"Название : {info.get('title')}")
    print(f"Канал    : {info.get('uploader') or info.get('channel') or '?'}")
    print(f"Длина    : {human_duration(info.get('duration'))}")
    print(f"Тип      : {'Shorts' if short else 'Обычное видео'}"
          f"{' (вертикальное)' if vertical else ''}")
    print()

    options = []
    for q, fps, size in qualities:
        fps_txt = f" {int(fps)}fps" if fps and fps > 30 else ""
        label = f"{q}p{fps_txt}  (~{human_size(size)})"
        options.append((label, build_selector(q, vertical), False))
    options.append(("Только звук (m4a)", "ba[ext=m4a]/ba", True))

    print("Доступное качество:")
    for i, (label, _, _) in enumerate(options, 1):
        best = "  <- лучшее" if i == 1 and len(options) > 1 else ""
        print(f"  {i}. {label}{best}")
    print("  0. Отмена")

    while True:
        raw = input("Выберите номер [1]: ").strip()
        if raw == "":
            raw = "1"
        if raw.isdigit():
            n = int(raw)
            if n == 0:
                return None
            if 1 <= n <= len(options):
                _, selector, audio = options[n - 1]
                return selector, audio, short
        print("Неверный ввод, попробуйте ещё раз.")


def download(url, selector, audio_only, short):
    sub = "Audio" if audio_only else ("Shorts" if short else "Videos")
    target = os.path.join(OUT_DIR, sub)
    os.makedirs(target, exist_ok=True)

    opts = base_opts()
    opts.update({
        "format": selector,
        "outtmpl": os.path.join(target, "%(title).150B [%(id)s].%(ext)s"),
        # при равном разрешении предпочитаем H.264 + AAC (открывается везде)
        "format_sort": ["res", "fps", "vcodec:h264", "acodec:aac"],
    })
    if not audio_only:
        opts["merge_output_format"] = "mp4"

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    print(f"\nГотово. Папка: {target}")


def main():
    setup_console()
    print("=" * 50)
    print(" YouTube Downloader (видео и Shorts)")
    print(f" yt-dlp {yt_dlp.version.__version__}")
    print("=" * 50)
    if not FFMPEG:
        print("ВНИМАНИЕ: ffmpeg не найден, высокое качество может не склеиться."
              " Запустите install.bat.")

    while True:
        print()
        url = input("Вставьте ссылку (пусто = выход): ").strip().strip('"')
        if not url:
            break
        try:
            print("Получаю информацию о видео...")
            info = fetch_info(url)
            picked = choose(info, url)
            if picked is None:
                print("Отменено.")
                continue
            download(url, *picked)
        except KeyboardInterrupt:
            print("\nПрервано.")
        except Exception as e:
            print(f"\nОшибка: {e}")
            print("Если ошибки повторяются, запустите install.bat для обновления yt-dlp.")


if __name__ == "__main__":
    main()
