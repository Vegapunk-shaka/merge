import os
import threading
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from pyrogram.types import Message
import logging

# Suppress Pyrogram INFO logs
logging.getLogger("pyrogram").setLevel(logging.WARNING)
# Enable logging in MoviePy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def merge_files(client, message: Message, file_paths, output_file_name, watermark_file="abc.mp4", frame_rate=30):
    # The output file name is now passed directly to the function
    output_file = output_file_name + ".mp4"  # Append .mp4 extension

    # Inform the user that processing has started
    progress_message = await message.reply_text(f"Processing files... 0% (Output: {output_file_name})")

    try:
        # Load all video files as MoviePy clips
        video_clips = []
        for file_path in file_paths:
            clip = VideoFileClip(file_path)
            clip = clip.set_fps(frame_rate)  # Set the frame rate for each clip
            video_clips.append(clip)

        if len(video_clips) > 1:
            # Concatenate all clips into one video if there is more than one video
            final_clip = concatenate_videoclips(video_clips, method="compose")
        else:
            # If there's only one clip, use it as the final clip directly
            final_clip = video_clips[0]

        # Load the watermark video (abc.mp4)
        watermark_clip = VideoFileClip(watermark_file).set_duration(final_clip.duration)

        # Position the watermark in the upper right corner
        watermark_top_right = watermark_clip.set_position(("right", "top"))

        # Position another instance of the watermark in the lower left corner
        watermark_bottom_left = watermark_clip.set_position(("left", "bottom"))

        # Overlay the watermark video on the final video in both positions
        watermarked_clip = CompositeVideoClip([final_clip, watermark_top_right, watermark_bottom_left])

        # Function to write video and report progress
        def write_video():
            logger.info("Starting video write process...")
            # Write the final video
            watermarked_clip.write_videofile(
                output_file,
                fps=frame_rate,
                codec="libx265",  # Using libx265 codec
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

        # Inform the user that processing is complete
        await progress_message.edit_text(f"Processing complete! File saved as: {output_file}")
        return output_file

    except Exception as e:
        await progress_message.edit_text(f"Processing failed: {str(e)}")
        return None

    finally:
        # Clean up the loaded clips
        for clip in video_clips:
            clip.close()
