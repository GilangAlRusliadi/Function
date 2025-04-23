import os
import re
import yt_dlp
import subprocess
import gradio as gr
import webbrowser
import threading

def open_browser():
    webbrowser.open("http://127.0.0.1:7860")

# Deteksi orientasi video berdasarkan URL atau metadata
def get_orientation(url):
    result = subprocess.run(['yt-dlp', '--get-filename', '-o', '%(width)sx%(height)s', url], capture_output=True, text=True)
    resolution = result.stdout.strip()

    if 'x' in resolution:
        width, height = map(int, resolution.split('x'))
        return 'landscape' if width >= height else 'portrait'
    else:
        return None

# Fungsi download video
def video_download(url, video_folder = r"H:\Videos\Youtube\Video"):
    if not os.path.exists(video_folder):
        os.makedirs(video_folder)
    try:
        result = subprocess.run(['yt-dlp', '--get-title', url], capture_output=True, text=True, check=True)
        title = result.stdout.strip()
        title = re.sub(r'[\\/:*?"<>|]', ' ', title)

        if not title:
            raise ValueError("Tidak dapat mendapatkan judul video.")

        orientation = get_orientation(url)
        if orientation == 'landscape':
            format_filter = 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]'
        elif orientation == 'portrait':
            format_filter = 'bestvideo[ext=mp4][width<=720]+bestaudio[ext=m4a]/best[ext=mp4][width<=720]'
        else:
            print("Gagal mendeteksi orientasi video.")
            return None

        video_file = os.path.join(video_folder, f"{title.replace('/', ' ')}.mp4")
        subprocess.run(['yt-dlp', '-f', format_filter, '-o', video_file, url], check=True)

        return video_file

    except subprocess.CalledProcessError as e:
        print(f"Terjadi kesalahan saat menjalankan yt-dlp: {e}")
        return None
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        return None

# Fungsi download MP3
def audio_download(url, audio_folder = r"H:\Videos\Youtube\Audio"):
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)
    try:
        if "youtube" not in url:
            url = "https://www.youtube.com/watch?v=" + url.split("[")[-1].split("]")[0]
        url = url.split("&")[0]

        result = subprocess.run(['yt-dlp', '--get-title', url], capture_output=True, text=True, check=True)
        title = result.stdout.strip()
        title = re.sub(r'[\\/:*?"<>|]', ' ', title)

        if not title:
            raise ValueError("Tidak dapat mendapatkan judul audio.")

        audio_file = os.path.join(audio_folder, f"{title.replace('/', ' ')}.mp3")
        subprocess.run(['yt-dlp', '-x', '--audio-format', 'mp3', '--embed-thumbnail', '-o', audio_file, url], check=True)
        
        return audio_file

    except subprocess.CalledProcessError as e:
        print(f"Terjadi kesalahan saat menjalankan yt-dlp: {e}")
        return None
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        return None

# Fungsi proses input untuk Gradio
def process_input(url, download_type):
    if download_type == "Video":
        return video_download(url)
    else:
        return audio_download(url)

# Gradio interface
with gr.Blocks() as youtube:
    gr.Markdown("# YouTube Downloader - Video dan Audio")
    input_text = gr.Textbox(label="Masukkan URL YouTube")
    download_type = gr.Radio(["Video", "Audio"], label="Pilih Format Download", value="Video")
    download_button = gr.Button("Download")
    output_file = gr.File(label="Download File")

    download_button.click(process_input, inputs=[input_text, download_type], outputs=output_file)

threading.Thread(target=open_browser).start()
youtube.launch()
