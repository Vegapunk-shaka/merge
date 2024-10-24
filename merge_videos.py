import os
import threading
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ColorClip
from pyrogram.types import Message
import logging

# Suppress Pyrogram INFO logs
logging.getLogger("pyrogram").setLevel(logging.WARNING)
# Enable logging in MoviePy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def merge_files(client, message: Message, file_paths, output_file_name, frame_rate=30, watermark_text="Sample Watermark", font_path=None):
    # The output file name is now passed directly to the function
    output_file = output_file_name + ".mp4"  # Append .mp4 extension

    # Inform the user that merging has started
    progress_message = await message.reply_text(f"Merging files... 0% (Output: {output_file_name})")

    try:
        # Load all video files as MoviePy clips
        video_clips = []
        for file_path in file_paths:
            clip = VideoFileClip(file_path)
            clip = clip.set_fps(frame_rate)  # Set the frame rate for each clip
            video_clips.append(clip)

        # Concatenate all clips into one video
        final_clip = concatenate_videoclips(video_clips, method="compose")

        # Create the text watermark
        text_clip = TextClip(watermark_text, fontsize=24, font=font_path or "Arial", color="white")
        text_clip = text_clip.set_duration(final_clip.duration).set_position(("right", "top"))

        # Create a rectangular border behind the text
        border_width = text_clip.w + 20  # Add some padding
        border_height = text_clip.h + 10  # Add some padding
        border_clip = ColorClip(size=(border_width, border_height), color=(0, 0, 0), ismask=False)  # Black border
        border_clip = border_clip.set_duration(final_clip.duration).set_position(("right", "top"))

        # Set the opacity of the border
        border_clip = border_clip.set_opacity(0.5)

        # Overlay the border and text on the final video
        watermarked_clip = CompositeVideoClip([final_clip, border_clip, text_clip])

        # Function to write video and report progress
        def write_video():
            logger.info("Starting video write process...")
            # Write the final video
            watermarked_clip.write_videofile(
                output_file,
                fps=frame_rate,
                codec="libx265",  # Using libx264 codec
                preset="veryfast",  # Adjust for speed/quality tradeoff
                ffmpeg_params=["-crf", "30"],  # Pass CRF via ffmpeg_params
                threads=4
            )
            logger.info("Video write process completed.")

        # Start writing the video in a separate thread
        write_thread = threading.Thread(target=write_video)
        write_thread.start()

        # Wait for the thread to finish
        write_thread.join()

        # Inform the user that merging is complete
        await progress_message.edit_text(f"Merging complete! File saved as: {output_file}")
        return output_file

    except Exception as e:
        await progress_message.edit_text(f"Merging failed: {str(e)}")
        return None

    finally:
        # Clean up the loaded clips
        for clip in video_clips:
            clip.close()
