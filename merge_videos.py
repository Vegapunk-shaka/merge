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

class VideoWriterThread(threading.Thread):
    """Custom thread class to handle video writing with exception capturing."""
    def __init__(self, watermarked_clip, output_file, frame_rate):
        super().__init__()
        self.watermarked_clip = watermarked_clip
        self.output_file = output_file
        self.frame_rate = frame_rate
        self.exception = None

    def run(self):
        try:
            logger.info("Starting video write process...")
            self.watermarked_clip.write_videofile(
                self.output_file,
                fps=self.frame_rate,
                codec="libx265",  # Using libx265 codec
                preset="veryfast",  # Adjust for speed/quality tradeoff
                ffmpeg_params=["-crf", "30"],  # Pass CRF via ffmpeg_params
                threads=4
            )
            logger.info("Video write process completed.")
        except Exception as e:
            self.exception = e

async def merge_files(client, message: Message, file_paths, output_file_name, watermark_file="abc.mp4", frame_rate=30):
    output_file = output_file_name + ".mp4"  # Append .mp4 extension

    # Inform the user that processing has started
    progress_message = await message.reply_text(f"Processing files... 0% (Output: {output_file_name})")
    last_progress_text = None  # To track last progress message content

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
            final_clip = video_clips[0]

        # Load the watermark video
        watermark_clip = VideoFileClip(watermark_file).set_duration(final_clip.duration)

        # Position watermarks
        watermark_top_right = watermark_clip.set_position(("right", "top"))
        watermark_bottom_left = watermark_clip.set_position(("left", "bottom"))

        # Overlay watermarks
        watermarked_clip = CompositeVideoClip([final_clip, watermark_top_right, watermark_bottom_left])

        # Start writing the video in a separate thread
        writer_thread = VideoWriterThread(watermarked_clip, output_file, frame_rate)
        writer_thread.start()

        # Polling the thread's progress (pseudo-progress)
        while writer_thread.is_alive():
            new_progress_text = "Processing files... Please wait."
            if last_progress_text != new_progress_text:
                await progress_message.edit_text(new_progress_text)
                last_progress_text = new_progress_text
            time.sleep(5)  # Sleep for 5 seconds between updates

        # Wait for the thread to finish
        writer_thread.join()

        # Check if the thread encountered any exceptions
        if writer_thread.exception:
            raise writer_thread.exception

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
