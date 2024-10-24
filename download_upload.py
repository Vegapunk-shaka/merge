import os
import math
from pyrogram import Client
from pyrogram.types import Message

async def download_file(client: Client, message: Message):
    # Check if the message contains a document or a video
    if message.document:
        file_size = message.document.file_size
        file_name = message.document.file_name
        file_path = f"downloads/{file_name}"
    elif message.video:
        file_size = message.video.file_size
        file_name = message.video.file_name
        file_path = f"downloads/{file_name}"
    else:
        await message.reply_text("Unsupported file type.")
        return None

    # Ensure the downloads directory exists
    os.makedirs("downloads", exist_ok=True)

    progress_message = await message.reply_text(f"Downloading {file_name}... 0%")

    last_percentage = -1  # Initialize last percentage

    def progress(current, total):
        nonlocal last_percentage  # Declare last_percentage as nonlocal
        percentage = math.floor(current * 100 / total)
        if percentage % 5 == 0 and percentage != last_percentage:  # Update every 5% and only if changed
            async def update_progress():
                await progress_message.edit_text(f"Downloading... {percentage}%")
            client.loop.create_task(update_progress())
            last_percentage = percentage  # Update last sent percentage

    # Download the media (document or video)
    await client.download_media(message, file_path, progress=progress)
    await progress_message.edit_text("Download complete!")
    return file_path

async def upload_file(client: Client, message: Message, file_path: str):
    # Ensure the file exists before uploading
    if not os.path.exists(file_path):
        await message.reply_text("File not found.")
        return None

    file_size = os.path.getsize(file_path)
    progress_message = await message.reply_text(f"Uploading {os.path.basename(file_path)}... 0%")

    last_percentage = -1  # Initialize last percentage

    def progress(current, total):
        nonlocal last_percentage  # Declare last_percentage as nonlocal
        percentage = math.floor(current * 100 / total)
        if percentage % 5 == 0 and percentage != last_percentage:  # Update every 5% and only if changed
            async def update_progress():
                await progress_message.edit_text(f"Uploading... {percentage}%")
            client.loop.create_task(update_progress())
            last_percentage = percentage  # Update last sent percentage

    await client.send_document(message.chat.id, file_path, progress=progress)
    await progress_message.edit_text("Upload complete!")
