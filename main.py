import os
import time
import random
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks

MY_ID = 1337973255977570345
APPLICATION_ID = 1521150234024214718

banned_users = set()
muted_users = {}
ping_history = {}

bot = commands.Bot(command_prefix='.', self_bot=True, help_command=None)


def is_me():
    def predicate(ctx):
        return ctx.author.id == MY_ID
    return commands.check(predicate)


async def respond(ctx, content: str):
    """Edit own message, or reply if someone else used the command."""
    if ctx.author.id == bot.user.id:
        try:
            await ctx.message.edit(content=content)
            return
        except Exception:
            pass
    try:
        await ctx.message.reply(content, mention_author=False)
    except Exception:
        try:
            await ctx.send(content)
        except Exception:
            pass


@tasks.loop(minutes=5)
async def keep_presence_alive():
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name=".gg/36EAyW5Z4F",
        details="Read Bio",
        state="Germany",
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


# ── Public commands (everyone can use) ──────────────────────────────────────

@bot.command(aliases=["commands", "help"])
async def cmd(ctx):
    text = (
        "**Commands**\n"
        "`.ping` – Latency\n"
        "`.donate` – Crypto addresses\n"
        "`.cat` – Random cat image\n"
        "`.quote` / `.qoute` – Random quote\n"
        "`.joke` – Random joke\n"
        "`.rate [@user]` – Cuteness 0-100\n"
        "`.cmd` – This list\n\n"
        "**Owner only**\n"
        "`.ban @user` / `.unban @user`\n"
        "`.server <source_id>` – Clone roles & channels into current server"
    )
    await respond(ctx, text)


@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await respond(ctx, f"🏓 Pong! Latency: `{latency}ms`")


@bot.command()
async def donate(ctx):
    await respond(ctx, (
        "**Donate**\n"
        "Litecoin: `LSC6QoQ9MsQ4C9U2QbVCjh82xC1TCTmRo8`\n"
        "Bitcoin: `bc1qw8flzl8jgug7eqng5xp8zzv94ylpmnpf6v7g25`\n\n"
        "Thanks for any amount of donate!"
    ))


@bot.command()
async def cat(ctx):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                if resp.status != 200:
                    await respond(ctx, "😿 Couldn't fetch a cat right now.")
                    return
                data = await resp.json()
                url = data[0]["url"]
        await respond(ctx, url)
    except Exception:
        await respond(ctx, "😿 Something went wrong while fetching a cat.")


@bot.command(aliases=["qoute"])
async def quote(ctx):
    urls = [
        "https://zenquotes.io/api/random",
        "https://api.quotable.io/random",
    ]
    try:
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        if isinstance(data, list) and data:
                            text = data[0].get("q", "")
                            author = data[0].get("a", "Unknown")
                        else:
                            text = data.get("content", "")
                            author = data.get("author", "Unknown")
                        if text:
                            await respond(ctx, f'💭 "{text}"\n— **{author}**')
                            return
                except Exception:
                    continue
        await respond(ctx, "❌ Couldn't fetch a quote right now.")
    except Exception:
        await respond(ctx, "❌ Something went wrong while fetching a quote.")


@bot.command()
async def joke(ctx):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/random_joke") as resp:
                if resp.status != 200:
                    await respond(ctx, "❌ Couldn't fetch a joke.")
                    return
                data = await resp.json()
                setup = data.get("setup", "")
                punchline = data.get("punchline", "")
        await respond(ctx, f"😂 **{setup}**\n\n||{punchline}||")
    except Exception:
        await respond(ctx, "❌ Something went wrong while fetching a joke.")


@bot.command()
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
    await respond(ctx, f"✨ Cuteness rating for {target}: **{score}/100** — {comment}")


# ── Owner only ──────────────────────────────────────────────────────────────

@bot.command()
@is_me()
async def ban(ctx, user: discord.User):
    banned_users.add(user.id)
    await respond(ctx, f"🚫 Banned **{user.name}** from triggering the auto-responder.")


@bot.command()
@is_me()
async def unban(ctx, user: discord.User):
    if user.id in banned_users:
        banned_users.remove(user.id)
        await respond(ctx, f"✅ Unbanned **{user.name}**.")
    else:
        await respond(ctx, f"⚠️ **{user.name}** is not banned.")


@bot.command()
@is_me()
async def server(ctx, source_id: int):
    """Clone roles + channels from source guild into the current guild.
    Usage: .server <source_guild_id>
    Run this INSIDE the target (new) server.
    """
    target = ctx.guild
    if target is None:
        await respond(ctx, "❌ Use this command inside a server.")
        return

    source = bot.get_guild(source_id)
    if source is None:
        await respond(ctx, "❌ Source server not found (you must be in both servers).")
        return

    await respond(ctx, f"⏳ Cloning from **{source.name}** → **{target.name}** ...\nThis can take a while.")

    role_map = {}
    created_roles = 0
    created_channels = 0

    try:
        roles = sorted(
            [r for r in source.roles if r.name != "@everyone"],
            key=lambda r: r.position
        )
        for role in roles:
            try:
                new_role = await target.create_role(
                    name=role.name,
                    permissions=role.permissions,
                    colour=role.colour,
                    hoist=role.hoist,
                    mentionable=role.mentionable,
                    reason="Server clone"
                )
                role_map[role.id] = new_role
                created_roles += 1
                await asyncio.sleep(0.8)
            except Exception as e:
                print(f"Role fail {role.name}: {e}")

        cat_map = {}
        categories = sorted(source.categories, key=lambda c: c.position)
        for cat in categories:
            try:
                overwrites = {}
                for target_obj, ow in cat.overwrites.items():
                    if isinstance(target_obj, discord.Role) and target_obj.id in role_map:
                        overwrites[role_map[target_obj.id]] = ow
                    elif isinstance(target_obj, discord.Role) and target_obj.name == "@everyone":
                        overwrites[target.default_role] = ow
                new_cat = await target.create_category(
                    name=cat.name,
                    overwrites=overwrites or None,
                    reason="Server clone"
                )
                cat_map[cat.id] = new_cat
                created_channels += 1
                await asyncio.sleep(0.8)
            except Exception as e:
                print(f"Category fail {cat.name}: {e}")

        channels = sorted(
            [c for c in source.channels if not isinstance(c, discord.CategoryChannel)],
            key=lambda c: c.position
        )
        for ch in channels:
            try:
                overwrites = {}
                for target_obj, ow in ch.overwrites.items():
                    if isinstance(target_obj, discord.Role) and target_obj.id in role_map:
                        overwrites[role_map[target_obj.id]] = ow
                    elif isinstance(target_obj, discord.Role) and target_obj.name == "@everyone":
                        overwrites[target.default_role] = ow

                parent = cat_map.get(ch.category_id) if ch.category_id else None

                if isinstance(ch, discord.TextChannel):
                    await target.create_text_channel(
                        name=ch.name,
                        topic=ch.topic,
                        slowmode_delay=ch.slowmode_delay,
                        nsfw=ch.nsfw,
                        category=parent,
                        overwrites=overwrites or None,
                        reason="Server clone"
                    )
                elif isinstance(ch, discord.VoiceChannel):
                    await target.create_voice_channel(
                        name=ch.name,
                        bitrate=min(ch.bitrate, target.bitrate_limit),
                        user_limit=ch.user_limit,
                        category=parent,
                        overwrites=overwrites or None,
                        reason="Server clone"
                    )
                created_channels += 1
                await asyncio.sleep(0.8)
            except Exception as e:
                print(f"Channel fail {ch.name}: {e}")

        await respond(
            ctx,
            f"✅ Clone finished!\n"
            f"Roles created: **{created_roles}**\n"
            f"Channels/Categories created: **{created_channels}**\n"
            f"From: `{source.name}` → `{target.name}`"
        )
    except Exception as e:
        await respond(ctx, f"❌ Clone failed: `{e}`")


# ── Auto-responder ──────────────────────────────────────────────────────────

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
                await message.reply(
                    "You are spamming. The auto-responder is ignoring you for 30 seconds.",
                    mention_author=False
                )
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
