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
from moviepy.editor import VideoFileClip, concatenate_videoclips
from pyrogram.types import Message
from moviepy.config import get_setting
import logging

# Enable logging in MoviePy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def merge_files(client, message: Message, file_paths, frame_rate=30):
    output_file = "merged_output.mp4"

    # Inform the user that merging has started
    progress_message = await message.reply_text("Moviepy - Building video...")

    try:
        # Load all video files as MoviePy clips
        video_clips = []
        for file_path in file_paths:
            clip = VideoFileClip(file_path)
            clip = clip.set_fps(frame_rate)  # Set the frame rate for each clip
            video_clips.append(clip)

        # Concatenate all clips into one video
        final_clip = concatenate_videoclips(video_clips, method="compose")

        # Display messages about the merging process
        logger.info("Moviepy - Building video merged_output.mp4.")
        await progress_message.edit_text("Moviepy - Building video merged_output.mp4...")

        # Write the output video file (shows detailed progress)
        def progress_callback(total_frames, frame_number):
            percentage = int((frame_number / total_frames) * 100)
            if percentage % 10 == 0:  # Update every 10%
                client.loop.create_task(progress_message.edit_text(f"Merging... {percentage}%"))

        final_clip.write_videofile(
            output_file, 
            fps=frame_rate, 
            codec="libx264", 
            logger='bar',  # Use progress bar logger from MoviePy
            progress_bar=True,
            verbose=True
        )

        # Inform the user that merging is complete
        await progress_message.edit_text("Moviepy - Done. Merging complete!")
        return output_file

    except Exception as e:
        await progress_message.edit_text(f"Merging failed: {str(e)}")
        return None

    finally:
        # Clean up the loaded clips
        for clip in video_clips:
            clip.close()
