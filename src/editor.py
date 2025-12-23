from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import os


def cut_video(input_path, output_dir, start_time, end_time):
    filename = os.path.basename(input_path)
    output_path = os.path.join(output_dir, f"cut_{filename}")

    print(f"✂️ [Editor] Cutting video from {start_time} to {end_time}...")

    ffmpeg_extract_subclip(input_path, start_time, end_time, targetname=output_path)

    print(f"🎉 [Done] Saved to: {output_path}")
    return output_path