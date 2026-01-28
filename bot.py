print("🔥 BOT FILE IS RUNNING")

import discord
from discord import app_commands
import json
import os

# ========= CONFIG =========
TOKEN = os.getenv("TOKEN")
GUILD_ID = 1462083992865214484
# ==========================
intents = discord.Intents.default()
intents.message_content = True

# ========= DATA STORAGE =========
DATA_FILE = "users.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load saved users (JSON keys are strings)
users = load_data()

# Convert to int keys for runtime use
AUTO_REACT_USERS: dict[int, str] = {
    int(user_id): emoji for user_id, emoji in users.items()
}

# ========= CLIENT =========
class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

client = MyClient()

# ========= EVENTS =========
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await client.tree.sync(guild=guild)
    print("✅ Slash commands synced to guild")
    print(f"🤖 Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    for user in message.mentions:
        if user.id in AUTO_REACT_USERS:
            emoji = AUTO_REACT_USERS[user.id]
            try:
                await message.add_reaction(emoji)
            except Exception as e:
                print(f"❌ Failed to react: {e}")

# ================= SLASH COMMANDS =================

@client.tree.command(
    name="adduser",
    description="Auto-react when a user is pinged",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    user="User to watch",
    emoji="Emoji or custom emoji ID"
)
async def adduser(
    interaction: discord.Interaction,
    user: discord.User,
    emoji: str
):
    # Convert raw emoji ID into usable format
    if emoji.isdigit():
        emoji = f"<:emoji:{emoji}>"

    # Update runtime dictionary
    AUTO_REACT_USERS[user.id] = emoji

    # Update saved data (JSON needs string keys)
    users[str(user.id)] = emoji
    save_data(users)

    await interaction.response.send_message(
        f"✅ Will react to {user.mention} with {emoji}",
        ephemeral=True
    )

@client.tree.command(
    name="removeuser",
    description="Stop auto-reacting to a user",
    guild=discord.Object(id=GUILD_ID)
)
async def removeuser(interaction: discord.Interaction, user: discord.User):
    if user.id in AUTO_REACT_USERS:
        del AUTO_REACT_USERS[user.id]

        users.pop(str(user.id), None)
        save_data(users)

        await interaction.response.send_message(
            f"🗑 Removed {user.mention}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "⚠️ That user is not registered.",
            ephemeral=True
        )

@client.tree.command(
    name="listusers",
    description="List all auto-react users",
    guild=discord.Object(id=GUILD_ID)
)
async def listusers(interaction: discord.Interaction):
    if not AUTO_REACT_USERS:
        await interaction.response.send_message(
            "No users registered.",
            ephemeral=True
        )
        return

    text = "\n".join(
        f"<@{uid}> → {emoji}"
        for uid, emoji in AUTO_REACT_USERS.items()
    )

    await interaction.response.send_message(text, ephemeral=True)

client.run(TOKEN)
