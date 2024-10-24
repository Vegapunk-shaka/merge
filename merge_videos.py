import os
import threading
import time
import subprocess
from pyrogram.types import Message
import logging

# Suppress Pyrogram INFO logs
logging.getLogger("pyrogram").setLevel(logging.WARNING)
# Enable logging in the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoWriterThread(threading.Thread):
    """Custom thread class to handle video writing with exception capturing."""
    def __init__(self, input_files, output_file, watermark_file=None, frame_rate=30):
        super().__init__()
        self.input_files = input_files
        self.output_file = output_file
        self.watermark_file = watermark_file
        self.frame_rate = frame_rate
        self.exception = None

    def run(self):
        try:
            logger.info("Starting video write process...")

            # Create a temporary file for the concat filter
            with open('concat_list.txt', 'w') as f:
                for file in self.input_files:
                    f.write(f"file '{file}'\n")

            # Build the FFmpeg command
            command = [
                'ffmpeg',
                '-y',  # Overwrite output files without asking
                '-f', 'concat',  # Use concat demuxer
                '-safe', '0',  # Allow unsafe file paths
                '-i', 'concat_list.txt',  # Input file list for concatenation
            ]
            
            # If a watermark file is specified, add it to the command
            if self.watermark_file:
                command += [
                    '-i', self.watermark_file,
                    '-filter_complex',
                    # Position the watermark in the upper right corner
                    "[0:v][1:v]overlay=W-w-10:10",  # Correct overlay parameters for upper right
                ]
            else:
                command += ['-filter_complex', 'null']

            # Finalizing the command
            command += [
                '-r', str(self.frame_rate),  # Set frame rate
                '-c:v', 'libx265',  # Using libx265 codec
                '-preset', 'veryfast',  # Adjust for speed/quality tradeoff
                '-crf', '30',  # Constant Rate Factor
                self.output_file
            ]

            # Execute the FFmpeg command
            subprocess.run(command, check=True)
            logger.info("Video write process completed.")
        except Exception as e:
            self.exception = e
        finally:
            os.remove('concat_list.txt')  # Clean up temporary file

async def merge_files(client, message: Message, file_paths, output_file_name, watermark_file="abc.mp4", frame_rate=30):
    output_file = output_file_name + ".mp4"  # Append .mp4 extension

    # Inform the user that processing has started
    progress_message = await message.reply_text(f"Processing files... 0% (Output: {output_file_name})")
    last_progress_text = None  # To track last progress message content

    try:
        # Start writing the video in a separate thread
        writer_thread = VideoWriterThread(file_paths, output_file, watermark_file, frame_rate)
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
