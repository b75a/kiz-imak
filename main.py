import os
import time
import random
import aiohttp
import discord
from discord.ext import commands, tasks

MY_ID = 1337973255977570345
APPLICATION_ID = 1495797765027008533

banned_users = set()
muted_users = {}
ping_history = {}

bot = commands.Bot(command_prefix='.', self_bot=True, help_command=None)

def is_me():
    def predicate(ctx):
        return ctx.author.id == MY_ID
    return commands.check(predicate)

@tasks.loop(minutes=5)
async def keep_presence_alive():
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name="love her.",
        details="I love sleeping",
        state="sleeping",
        application_id=APPLICATION_ID,
        buttons=[
            discord.ActivityButton("dc", "https://discord.gg/36EAyW5Z4F"),
            discord.ActivityButton("guns", "https://guns.lol/tpa"),
        ]
    )
    await bot.change_presence(status=discord.Status.dnd, activity=activity)

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user} (ID: {bot.user.id})")
    
    if not keep_presence_alive.is_running():
        keep_presence_alive.start()
        
    print("Rich Presence loop initialized.")

@bot.command()
@is_me()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.message.edit(content=f"🏓 Pong! Latency: `{latency}ms`")

@bot.command()
@is_me()
async def ban(ctx, user: discord.User):
    banned_users.add(user.id)
    await ctx.message.edit(content=f"🚫 Banned **{user.name}** from triggering the auto-responder.")

@bot.command()
@is_me()
async def unban(ctx, user: discord.User):
    if user.id in banned_users:
        banned_users.remove(user.id)
        await ctx.message.edit(content=f"✅ Unbanned **{user.name}**.")
    else:
        await ctx.message.edit(content=f"⚠️ **{user.name}** is not banned.")

@bot.command()
@is_me()
async def donate(ctx):
    await ctx.message.edit(content=(
        "**Donate**\n"
        "Litecoin: `LSC6QoQ9MsQ4C9U2QbVCjh82xC1TCTmRo8`\n"
        "Bitcoin: `bc1qw8flzl8jgug7eqng5xp8zzv94ylpmnpf6v7g25`\n\n"
        "Thanks for any amount of donate!"
    ))

@bot.command()
@is_me()
async def cat(ctx):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                if resp.status != 200:
                    await ctx.message.edit(content="😿 Couldn't fetch a cat right now.")
                    return
                data = await resp.json()
                url = data[0]["url"]
        await ctx.message.edit(content=url)
    except Exception:
        await ctx.message.edit(content="😿 Something went wrong while fetching a cat.")

@bot.command(aliases=["qoute"])
@is_me()
async def quote(ctx):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.quotable.io/random") as resp:
                if resp.status != 200:
                    await ctx.message.edit(content="❌ Couldn't fetch a quote.")
                    return
                data = await resp.json()
                text = data.get("content", "")
                author = data.get("author", "Unknown")
        await ctx.message.edit(content=f'💭 "{text}"\n— **{author}**')
    except Exception:
        await ctx.message.edit(content="❌ Something went wrong while fetching a quote.")

@bot.command()
@is_me()
async def joke(ctx):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/random_joke") as resp:
                if resp.status != 200:
                    await ctx.message.edit(content="❌ Couldn't fetch a joke.")
                    return
                data = await resp.json()
                setup = data.get("setup", "")
                punchline = data.get("punchline", "")
        await ctx.message.edit(content=f"😂 **{setup}**\n\n||{punchline}||")
    except Exception:
        await ctx.message.edit(content="❌ Something went wrong while fetching a joke.")

@bot.command()
@is_me()
async def rate(ctx, user: discord.User = None):
    score = random.randint(0, 100)
    target = user.mention if user else "you"
    if score >= 90:
        comment = "extremely cute 💖"
    elif score >= 70:
        comment = "very cute 🥰"
    elif score >= 50:
        comment = "pretty cute 😊"
    elif score >= 30:
        comment = "kinda cute 🤔"
    else:
        comment = "needs more cuteness 😢"
    await ctx.message.edit(content=f"✨ Cuteness rating for {target}: **{score}/100** — {comment}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.id == bot.user.id:
        return

    if message.author.id in banned_users:
        return

    if bot.user.mentioned_in(message):
        now = time.time()
        user_id = message.author.id

        if user_id in muted_users:
            if now < muted_users[user_id]:
                return  
            else:
                del muted_users[user_id]  

        if user_id not in ping_history:
            ping_history[user_id] = []
        
        ping_history[user_id].append(now)
        ping_history[user_id] = [t for t in ping_history[user_id] if now - t <= 10]

        if len(ping_history[user_id]) >= 3:
            muted_users[user_id] = now + 30 
            try:
                await message.reply("You are spamming. The auto-responder is ignoring you for 30 seconds.", mention_author=False)
            except discord.HTTPException:
                pass
            return

        try:
            await message.reply("this user is not awake, try it later.", mention_author=False)
        except discord.HTTPException:
            pass

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("ERROR: DISCORD_TOKEN variable is missing from environment variables.")
        exit(1)
        
    bot.run(token)