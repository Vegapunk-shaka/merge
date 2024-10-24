import os
import math
from pyrogram import Client
from pyrogram.types import Message

async def download_file(client: Client, message: Message):
    """Download a file (document or video) from a message."""
    # Check if the message contains a document or a video
    if message.document:
        file_name = message.document.file_name
    elif message.video:
        file_name = message.video.file_name
    else:
        await message.reply_text("Unsupported file type.")
        return None

    file_path = f"downloads/{file_name}"  # Set the download path

    # Ensure the downloads directory exists
    os.makedirs("downloads", exist_ok=True)

    # Send a message to show the download progress
    progress_message = await message.reply_text(f"Downloading {file_name}... 0%")

    last_percentage = -1  # Initialize last percentage

    def progress(current, total):
        """Track download progress and update the message accordingly."""
        nonlocal last_percentage
        percentage = math.floor(current * 100 / total)
        if percentage % 10 == 0 and percentage != last_percentage:  # Update every 10% and only if changed
            async def update_progress():
                try:
                    await progress_message.edit_text(f"Downloading... {percentage}%")
                except Exception as e:
                    print(f"Failed to update progress message: {e}")
            client.loop.create_task(update_progress())
            last_percentage = percentage  # Update last sent percentage

    try:
        # Download the media (document or video)
        await client.download_media(message, file_path, progress=progress)
        await progress_message.edit_text("Download complete!")  # Final update
    except Exception as e:
        await progress_message.edit_text(f"Download failed: {e}")
        return None

    return file_path

async def upload_file(client: Client, message: Message, file_path: str):
    """Upload a file and show upload progress."""
    # Ensure the file exists before uploading
    if not os.path.exists(file_path):
        await message.reply_text("File not found.")
        return None

    progress_message = await message.reply_text(f"Uploading {os.path.basename(file_path)}... 0%")
    last_percentage = -1  # Initialize last percentage

    def progress(current, total):
        """Track upload progress and update the message accordingly."""
        nonlocal last_percentage
        percentage = math.floor(current * 100 / total)
        if percentage % 10 == 0 and percentage != last_percentage:  # Update every 10% and only if changed
            async def update_progress():
                try:
                    await progress_message.edit_text(f"Uploading... {percentage}%")
                except Exception as e:
                    print(f"Failed to update progress message: {e}")
            client.loop.create_task(update_progress())
            last_percentage = percentage  # Update last sent percentage

    try:
        # Upload the document
        await client.send_document(message.chat.id, file_path, progress=progress)
        await progress_message.edit_text("Upload complete!")  # Final update
    except Exception as e:
        await progress_message.edit_text(f"Upload failed: {e}")
        return None
