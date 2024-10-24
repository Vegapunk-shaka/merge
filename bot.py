from pyrogram import Client, filters
from pyrogram.types import Message
from download_upload import download_file, upload_file
from merge_videos import merge_files
import os

# Initialize the bot with your API credentials
api_id = "18530329"
api_hash = "edefebe693e029e6aca6c7c1df2745ec"
bot_token = "7632646326:AAHUdQR9PFEgLWPAbHlNupsvttSmd4uUMK4"

app = Client("file_merger_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Store the file info uploaded by the user
uploaded_files = []
awaiting_filename = {}  # Dictionary to track when the bot is awaiting a filename from the user

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text("Welcome! Please send me the files you want to merge. After uploading, reply with 'done' to start the download.")

@app.on_message(filters.command("cancel"))
async def cancel(client, message: Message):
    """Cancel the current merging process and clear uploaded files."""
    if uploaded_files:
        uploaded_files.clear()
        await message.reply_text("The current merging process has been canceled, and uploaded files have been cleared.")
    else:
        await message.reply_text("There is no ongoing merging process.")

@app.on_message(filters.command("restart"))
async def restart(client, message: Message):
    """Restart the bot by clearing the uploaded files."""
    uploaded_files.clear()
    awaiting_filename.clear()
    await message.reply_text("The bot has been restarted. You can now send me new files to merge.")

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

# Handle replies with 'merge' to add the file to the download list
@app.on_message(filters.text & filters.reply & filters.regex("merge"))
async def handle_merge(client, message: Message):
    if message.reply_to_message and (message.reply_to_message.document or message.reply_to_message.video):
        uploaded_files.append(message.reply_to_message)
        await message.reply_text(f"Added {message.reply_to_message.document.file_name if message.reply_to_message.document else message.reply_to_message.video.file_name} to the merging list.")
    else:
        await message.reply_text("Please reply to a document or video file to add it to the merging list.")

# Handle replies with 'done' to initiate the download and merging process
@app.on_message(filters.text & filters.regex("done"))
async def confirm_upload_complete(client, message: Message):
    if len(uploaded_files) < 2:
        await message.reply_text("Please upload at least two files before merging.")
    else:
        await message.reply_text("All files uploaded. What would you like to name the merged file? (without extension)")
        awaiting_filename[message.chat.id] = True  # Set the bot to await a filename from the user

# Handle text responses that are filenames (but not commands)
@app.on_message(filters.text & ~filters.command("start") & ~filters.command("cancel") & ~filters.command("restart"))
async def capture_filename(client, message: Message):
    if message.chat.id in awaiting_filename:
        # Get the filename from the user's message
        output_file_name = message.text.strip() + ".mp4"  # Append .mp4 extension
        await message.reply_text(f"Starting download of uploaded files...")

        downloaded_file_paths = []

        # Download each uploaded file
        for file_msg in uploaded_files:
            file_path = await download_file(client, file_msg)
            downloaded_file_paths.append(file_path)

        # After downloading all files, start merging
        await message.reply_text("Files downloaded. Merging files, please wait...")
        merged_file = await merge_files(client, message, downloaded_file_paths, output_file_name)

        if merged_file:
            await message.reply_text("Merging complete! Uploading the merged file...")
            await upload_file(client, message, merged_file)
            await message.reply_text("Merged file uploaded successfully!")

            # Clean up downloaded files
            for f in downloaded_file_paths:
                if os.path.exists(f):
                    os.remove(f)
            uploaded_files.clear()  # Clear the list after merging
        else:
            await message.reply_text("Merging failed.")

        # Clear the awaiting filename state after processing
        del awaiting_filename[message.chat.id]

# Run the bot
app.run()
