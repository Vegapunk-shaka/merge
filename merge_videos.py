# import subprocess
# import os
# from pyrogram.types import Message

# async def merge_files(client, message: Message, file_paths, frame_rate=30):
#     output_file = "merged_output.mp4"
#     file_list_path = "file_list.txt"
    
#     # Create a text file for ffmpeg input
#     with open(file_list_path, "w") as f:
#         for file_path in file_paths:
#             f.write(f"file '{file_path}'\n")  # Ensure correct formatting

#     # Inform the user that merging has started
#     progress_message = await message.reply_text("Merging files... 0%")

#     try:
#         process = subprocess.Popen(
#             [
#                 "ffmpeg", 
#                 "-f", "concat", 
#                 "-safe", "0",
#                 "-fflags", "+genpts", 
#                 "-i", file_list_path, 
#                 "-r", str(frame_rate),  # Set the frame rate here
#                 "-c", "copy", 
#                 output_file
#             ],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE
#         )

#         # Monitor the process and output
#         while True:
#             output = process.stdout.readline()
#             if output == b"" and process.poll() is not None:
#                 break
#             if output:
#                 # Optional: log FFmpeg output
#                 print(output.decode().strip())  

#         process.wait()  # Wait for the ffmpeg process to finish
#         await progress_message.edit_text("Merging complete!")
#         return output_file
#     except subprocess.CalledProcessError:
#         await progress_message.edit_text("Merging failed.")
#         return None
#     finally:
#         if os.path.exists(file_list_path):
#             os.remove(file_list_path)
import os
import threading
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, ImageClip
from pyrogram.types import Message
import logging

# Suppress Pyrogram INFO logs
logging.getLogger("pyrogram").setLevel(logging.WARNING)
# Enable logging in MoviePy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Install ImageMagick and configure the security policy
!apt-get install -y imagemagick

# Create a policy.xml file to allow PDF and SVG formats
policy_file_content = """<?xml version="1.0" encoding="UTF-8"?>
<policymap>
    <policy domain="coder" name="PDF" value="read|write"/>
    <policy domain="coder" name="SVG" value="read|write"/>
    <policy domain="path" value="@/tmp" rights="read|write"/>
</policymap>
"""

# Write the policy file
with open("/etc/ImageMagick-6/policy.xml", "w") as f:
    f.write(policy_file_content)

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
        border_width = text_clip.w + 20  # Add padding to width
        border_height = text_clip.h + 10  # Add padding to height

        # Create the border using ImageMagick
        border_clip_path = '/tmp/border.png'
        os.system(f"convert -size {border_width}x{border_height} xc:black -alpha set -channel A -evaluate set 50% {border_clip_path}")

        # Load the border as a clip
        border_clip = ImageClip(border_clip_path).set_duration(final_clip.duration).set_position(("right", "top"))

        # Overlay the border and text on the final video
        watermarked_clip = CompositeVideoClip([final_clip, border_clip, text_clip])

        # Function to write video and report progress
        def write_video():
            logger.info("Starting video write process...")
            watermarked_clip.write_videofile(
                output_file,
                fps=frame_rate,
                codec="libx264",  # Use libx264 codec for encoding
                preset="medium",  # You can adjust the preset for speed/quality tradeoff
                ffmpeg_params=["-crf", "28"],  # Set Constant Rate Factor
                threads=4
            )
            logger.info("Video write process completed.")

        # Start writing the video in a separate thread
        write_thread = threading.Thread(target=write_video)
        write_thread.start()

        # Track the last progress message to avoid sending duplicate edits
        last_progress_message = "Merging... 0% | Estimated time left: 0 seconds"

        # Periodically update progress while the thread is running
        while write_thread.is_alive():
            # Calculate the elapsed time and progress percentage
            elapsed_time = final_clip.duration - (final_clip.end - final_clip.start)  # Adjust if necessary
            progress_percentage = int((elapsed_time / final_clip.duration) * 100) if final_clip.duration else 0
            estimated_time = int(final_clip.duration - elapsed_time) if final_clip.duration else 0

            # Create the new message content
            new_progress_message = f"Merging... {progress_percentage}% | Estimated time left: {estimated_time} seconds"

            # Only update the message if it's different
            if new_progress_message != last_progress_message:
                await progress_message.edit_text(new_progress_message)
                last_progress_message = new_progress_message
            
            time.sleep(1)  # Wait a bit before updating again

        # Wait for the thread to finish
        write_thread.join()

        # Inform the user that merging is complete
        await progress_message.edit_text(f"Merging complete! File saved as: {output_file_name}")
        return output_file

    except Exception as e:
        await progress_message.edit_text(f"Merging failed: {str(e)}")
        return None

    finally:
        # Clean up the loaded clips
        for clip in video_clips:
            clip.close()
