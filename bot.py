import os
import logging
from datetime import datetime as dt
from pyrogram import Client, filters
from pyrogram.types import Message
from download_upload import download_file, upload_file
from merge_videos import merge_files

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
api_id = "18530329"
api_hash = "edefebe693e029e6aca6c7c1df2745ec"
bot_token = "7632646326:AAHUdQR9PFEgLWPAbHlNupsvttSmd4uUMK4"
app = Client("file_merger_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Store the uploaded files
uploaded_files = []
uptime = dt.now()

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text("Welcome! Please send me the files you want to merge or watermark. After uploading, reply with 'done' to start processing.")

@app.on_message(filters.command("cancel"))
async def cancel(client, message: Message):
    """Cancel the current process and clear uploaded files."""
    if uploaded_files:
        uploaded_files.clear()
        await message.reply_text("The current process has been canceled, and uploaded files have been cleared.")
    else:
        await message.reply_text("There is no ongoing process.")

@app.on_message(filters.command("restart"))
async def restart(client, message: Message):
    """Restart the bot by clearing the uploaded files."""
    uploaded_files.clear()
    await message.reply_text("The bot has been restarted. You can now send me new files.")

@app.on_message(filters.document | filters.video)
async def handle_file_upload(client, message: Message):
    uploaded_files.append(message)
    await message.reply_text(f"{message.document.file_name if message.document else message.video.file_name} has been uploaded. Send more files, or type 'done' when finished.")

@app.on_message(filters.text & filters.reply & filters.regex("add"))
async def handle_merge(client, message: Message):
    if message.reply_to_message and (message.reply_to_message.document or message.reply_to_message.video):
        uploaded_files.append(message.reply_to_message)
        await message.reply_text(f"Added {message.reply_to_message.document.file_name if message.reply_to_message.document else message.reply_to_message.video.file_name} to the merging list.")
    else:
        await message.reply_text("Please reply to a document or video file to add it to the merging list.")

@app.on_message(filters.text & filters.regex("done"))
async def confirm_upload_complete(client, message: Message):
    if len(uploaded_files) == 0:
        await message.reply_text("No files uploaded. Please upload at least one file.")
        return

    await message.reply_text("What would you like to name the output file? (without extension)")
    user_response = await app.listen(message.chat.id)
    output_file_name = user_response.text.strip()

    # Start processing the files with a single message update
    await message.reply_text("Starting download and merging process... Please wait while we process your files.")
    downloaded_file_paths = []

    # Download each uploaded file
    for file_msg in uploaded_files:
        logger.info(f"Downloading file: {file_msg.document.file_name if file_msg.document else file_msg.video.file_name}")
        file_path = await download_file(client, file_msg)
        if file_path:
            downloaded_file_paths.append(file_path)

    # Process the downloaded files
    if len(downloaded_file_paths) == 1:
        watermarked_file = await merge_files(client, message, [downloaded_file_paths[0]], output_file_name)

        if watermarked_file:
            await message.reply_text("Watermark added! Uploading the file...")
            await upload_file(client, message, watermarked_file)
            await message.reply_text("File uploaded successfully!")
        else:
            await message.reply_text("Watermarking failed.")
    else:
        merged_file = await merge_files(client, message, downloaded_file_paths, output_file_name)

        if merged_file:
            await message.reply_text("Merging complete! Uploading the file...")
            await upload_file(client, message, merged_file)
            await message.reply_text("Merged file uploaded successfully!")
        else:
            await message.reply_text("Merging failed.")

    # Clean up downloaded files and reset uploaded files
    for f in downloaded_file_paths:
        if os.path.exists(f):
            os.remove(f)
    uploaded_files.clear()

# Run the bot
app.run()
