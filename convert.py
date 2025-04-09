# from  Function import convert_videos
import os
import re
import math
import json
import shutil
import subprocess
from tqdm import tqdm

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    size = round(size_bytes / p, 2)
    return f"{size} {size_name[i]}"

def get_video_resolution(input_file):
    command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', input_file]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        video_info = json.loads(result.stdout)
        width = video_info['streams'][0]['width']
        height = video_info['streams'][0]['height']
        return (width, height)
    else:
        print(f'Error getting video resolution: {result.stderr}')
        return None

def get_video_duration(input_file):
    command = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', input_file]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output = result.stdout
    try:
        duration = json.loads(output)['format']['duration']
        return float(duration)
    except Exception as e:
        print(f"Gagal mendapatkan durasi video: {e}")
        return 0

def convert_video(input_file, output_file, command):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input_file}"'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    total_duration = float(result.stdout)

    input_file_size = float(subprocess.check_output(['stat', '-c', '%s', input_file]))  # Size in bytes
    total_size_MB = round(input_file_size / (1024 * 1024), 2)  # Convert to MB

    process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)

    time_pattern = re.compile(r'time=(\d+):(\d+):(\d+.\d+)')

    pbar = tqdm(total=total_size_MB, unit="MB", desc="Converting", dynamic_ncols=True)

    for line in process.stderr:
        match = time_pattern.search(line)
        if match:
            hours, minutes, seconds = map(float, match.groups())
            elapsed_time = hours * 3600 + minutes * 60 + seconds
            elapsed_size_MB = round((elapsed_time / total_duration) * total_size_MB, 2)
            pbar.update(elapsed_size_MB - pbar.n)

    pbar.close()
    process.wait()

def convert_videos(search, height, download_folder, konversi_folder, quality, mulus = False, zero_size = "Skip"):
    konversi_folder  = rf'{konversi_folder}\{search} - {str(height)}p'
    if not os.path.exists(konversi_folder):
        os.makedirs(konversi_folder)

    video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.mpeg', '.3gp', '.m4v', '.mpg', '.vob', '.ts', '.asf', '.rm', '.swf', '.ogv']

    files_to_convert = sorted([file for file in os.listdir(download_folder) if os.path.splitext(file)[1].lower() in video_extensions and search in file])

    for file in files_to_convert:
        try:
            input_file = os.path.join(download_folder, file)
            output_file = os.path.join(konversi_folder, os.path.splitext(file)[0] + ".mp4")

            print(f"Memulai konversi '{file}'.")
            input_file_size = os.path.getsize(input_file)
            print(f"Ukuran file input: {convert_size(input_file_size)}")

            duration = get_video_duration(input_file)

            if height == 720:
                if quality == "Low":
                    video_bitrate = 850
                elif quality == "High":
                    video_bitrate = 1350
                audio_bitrate = 160
            elif height == 480:
                video_bitrate = 600
                audio_bitrate = 95
            elif height == 360:
                video_bitrate = 250
                audio_bitrate = 50

            predicted_output_size = (video_bitrate + audio_bitrate) * duration / 8  # dalam kilobyte
            predicted_output_size_MB = predicted_output_size / 1024  # dalam megabyte

            print(f"Ukuran file output prediksi: {convert_size(predicted_output_size * 1000)}")

            if predicted_output_size_MB > input_file_size / (1024 * 1024) and input_file_size / (1024 * 1024) > 10:
                print(f"Ukuran file output prediksi lebih besar dari ukuran file input. Melewati konversi dan memindahkan file '{file}'.")
                shutil.move(input_file, output_file)
            else:
                if os.path.exists(output_file):
                    print(f"File '{file}' sudah ada di folder konversi. Melewati konversi.")

                    output_file_size = os.path.getsize(output_file)

                    if output_file_size == 0 or output_file_size > input_file_size:
                        print(f"Menghapus output...")
                        os.remove(output_file)
                        print(f"Memindahkan input...")
                        shutil.move(input_file, output_file)

                else:
                    resolution = get_video_resolution(input_file)
                    if resolution is not None:
                        width_ori, height_ori = resolution
                        if height_ori < width_ori:
                            width = int(width_ori / height_ori * height)
                            if (width_ori / height_ori) * height % 1 != 0:
                                width += 1
                            if mulus:
                                command = [
                                    'ffmpeg', '-i', input_file,
                                    '-s', f'{str(width)}x{str(height)}',
                                    output_file
                                ]
                            else:
                                if height == 720:
                                    if quality == "Low":
                                        command = [
                                            'ffmpeg', '-i', input_file,
                                            '-s', f'{str(width)}x{str(height)}',
                                            '-b:v', '850k', '-bufsize', '1000k', '-r', '30',
                                            '-b:a', '160k', '-ar', '44100', '-ac', '2',
                                            output_file
                                        ]
                                    elif quality == "High":
                                        command = [
                                            'ffmpeg', '-i', input_file,
                                            '-s', f'{str(width)}x{str(height)}',
                                            '-b:v', '1350k', '-bufsize', '1500k', '-r', '30',
                                            '-b:a', '160k', '-ar', '48000', '-ac', '2',
                                            output_file
                                        ]
                                elif height == 480:
                                    command = [
                                        'ffmpeg', '-i', input_file,
                                        '-s', f'{str(width)}x{str(height)}',
                                        '-b:v', '600k', '-bufsize', '700k', '-r', '24',
                                        '-b:a', '95k', '-ar', '44100', '-ac', '2',
                                        output_file
                                    ]
                                elif height == 360:
                                    command = [
                                        'ffmpeg', '-i', input_file,
                                        '-s', f'{str(width)}x{str(height)}',
                                        '-b:v', '250k', '-bufsize', '300k', '-r', '24',
                                        '-b:a', '50k', '-ar', '44100', '-ac', '2',
                                        output_file
                                    ]

                        else:
                            width = height
                            height = int(height_ori / width_ori * width)
                            if (height_ori / width_ori) * width % 1 != 0:
                                height += 1
                            if mulus:
                                command = [
                                    'ffmpeg', '-i', input_file,
                                    '-s', f'{str(width)}x{str(height)}',
                                    output_file
                                ]
                            else:
                                if width == 720:
                                    if quality == "Low":
                                        command = [
                                            'ffmpeg', '-i', input_file,
                                            '-s', f'{str(width)}x{str(height)}',
                                            '-b:v', '850k', '-bufsize', '1000k', '-r', '30',
                                            '-b:a', '160k', '-ar', '44100', '-ac', '2',
                                            output_file
                                        ]
                                    elif quality == "High":
                                        command = [
                                            'ffmpeg', '-i', input_file,
                                            '-s', f'{str(width)}x{str(height)}',
                                            '-b:v', '1350k', '-bufsize', '1500k', '-r', '30',
                                            '-b:a', '160k', '-ar', '48000', '-ac', '2',
                                            output_file
                                        ]
                                elif width == 480:
                                    command = [
                                        'ffmpeg', '-i', input_file,
                                        '-s', f'{str(width)}x{str(height)}',
                                        '-b:v', '600k', '-bufsize', '700k', '-r', '24',
                                        '-b:a', '95k', '-ar', '44100', '-ac', '2',
                                        output_file
                                    ]
                                elif height == 360:
                                    command = [
                                        'ffmpeg', '-i', input_file,
                                        '-s', f'{str(width)}x{str(height)}',
                                        '-b:v', '250k', '-bufsize', '300k', '-r', '24',
                                        '-b:a', '50k', '-ar', '44100', '-ac', '2',
                                        output_file
                                    ]

                        convert_video(input_file, output_file, command)

                        print(f"Video '{file}' telah berhasil dikonversi.")
                        output_file_size = os.path.getsize(output_file)
                        print(f"Ukuran file output: {convert_size(output_file_size)}")

                        if output_file_size > input_file_size:
                            print(f"Menghapus output...")
                            os.remove(output_file)
                            print(f"Memindahkan input...")
                            shutil.move(input_file, output_file)

                        if output_file_size == 0:
                            if zero_size == "Skip":
                                print(100 * "=")
                                print("Size file output 0KB")
                                print(f"Menghapus output dan SKIP...")
                                print(100 * "=")
                                os.remove(output_file)
                            elif zero_size == "Copy":
                                print(100 * "=")
                                print("Size file output 0KB")
                                print(f"Menghapus output...")
                                os.remove(output_file)
                                print(f"Memindahkan input...")
                                shutil.copy(input_file, output_file)
                                print(100 * "=")
                            elif zero_size == "Try Again":
                                print(100 * "=")
                                print("Size file output 0KB")
                                print(f"Menghapus output...")
                                os.remove(output_file)
                                print(f"Memcoba lagi...")
                                convert_video(input_file, output_file, command)
                                print(100 * "=")
                                if output_file_size == 0:
                                    print(f"Menghapus output...")
                                    os.remove(output_file)
                                    print(f"Memindahkan input...")
                                    shutil.move(input_file, output_file)

                    print()

        except Exception as e:
            print("==========================================================")
            print(f"Terjadi kesalahan: {e}")
            print("==========================================================")
            if width_ori > 720 and height_ori > 720:
                print("Maaf coba lagi...")
            else:
                print(f"Panjang Ori = {str(width_ori)}")
                print(f"Lebar Ori = {str(height_ori)}")
                try:
                    command = [
                        'ffmpeg', '-i', input_file,
                        '-s', f'{str(width_ori)}x{str(height_ori)}',
                        '-b:v', '1350k', '-bufsize', '1500k', '-r', '30',
                        '-b:a', '160k', '-ar', '48000', '-ac', '2',
                        output_file
                    ]

                    convert_video(input_file, output_file, command)

                except Exception as e:
                    print(f"Nyerah bos: {e}")
                    print("==========================================================")

    return konversi_folder
