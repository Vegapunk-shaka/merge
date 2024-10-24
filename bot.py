from pyrogram import Client, filters
from pyrogram.types import Message
from download_upload import download_file, upload_file
from merge_videos import merge_files
import os

api_id = "18530329"
api_hash = "edefebe693e029e6aca6c7c1df2745ec"
bot_token = "7936026368:AAGUVaduGFrc6XwUy9BOrCX0gcNdTytO_xE"

app = Client("file_merger_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Store the file info uploaded by the user
uploaded_files = []

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text("Welcome! Please send me the files you want to merge. After uploading, reply with 'done' to start the download.")

# Handle document uploads
@app.on_message(filters.document)
async def handle_document(client, message: Message):
    uploaded_files.append(message)
    await message.reply_text(f"Document {message.document.file_name} has been uploaded. Send more files, or type 'done' when finished.")

# Handle video uploads
@app.on_message(filters.video)
async def handle_video(client, message: Message):
    uploaded_files.append(message)
    await message.reply_text(f"Video {message.video.file_name} has been uploaded. Send more files, or type 'done' when finished.")

# Start downloading and merging after 'done' command
@app.on_message(filters.text & filters.regex("done"))
async def confirm_upload_complete(client, message: Message):
    if len(uploaded_files) < 2:
        await message.reply_text("Please upload at least two files before merging.")
    else:
        await message.reply_text("All files uploaded. Starting download...")
        downloaded_file_paths = []

        # Download each uploaded file
        for file_msg in uploaded_files:
            file_path = await download_file(client, file_msg)
            downloaded_file_paths.append(file_path)

        # After downloading all files, start merging
        await message.reply_text("Files downloaded. Merging files, please wait...")
        merged_file = await merge_files(client, message, downloaded_file_paths)

        if merged_file:
            await message.reply_text("Merging complete! Uploading the merged file...")
            await upload_file(client, message, merged_file)
            await message.reply_text("Merged file uploaded successfully!")
            # Clean up
            for f in downloaded_file_paths:
                os.remove(f)
            uploaded_files.clear()
        else:
            await message.reply_text("Merging failed.")

app.run()
