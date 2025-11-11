import disnake
from disnake.ext import commands
import random

intents = disnake.Intents.none()
intents.guilds = True  
intents.messages = True  # Important: No need to turn on message content intent in discord bot settings.
client = disnake.Client(intents=intents)

# DEFAULT CONFIGURATION
chance = 100 # 1 in X chance that there will be a bomb (default and global chance)
timeout_in_seconds = 10  # How long will a mine time you out for in seconds (default and global chance)
max_bombs = 20 # How many mines can be planted in one command? (Keep low to reduce extreme loads)
Token = "" # Put token either here (not reccomended) or in .env file (preferred) if working with one and link it here.

#bombs - edit only if you want the bot to start while having bombs already planted
global_mines = 0
channel_mines: dict[int, list[dict[str, int]]] = {}

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True

bot = commands.Bot(
    command_prefix="!",
    test_guilds=[1437750462185996301],
    command_sync_flags=command_sync_flags,
    intents=intents
)


@bot.slash_command(description="Plant any number of landmines globally.", default_member_permissions=disnake.Permissions(moderate_members=True))
async def globalplant(
    inter: disnake.AppCmdInter,
    count: int = commands.Param(gt=0, lt=max_bombs)
):
    global global_mines
    global_mines += count
    if count == 1:
        await inter.response.send_message(
            "**" + str(count) + "** mine has been planted. Prepare for carnage.\n"
            "-# Chance of explosion is currently **1 in " + str(chance) + "**. "
            "Timeout for stepping on a landmine is **" + str(timeout_in_seconds) + "** seconds. "
            "Currently there are a total of " + str(global_mines) + " mines."
        )
    else:
        await inter.response.send_message(
            "**" + str(count) + "** mines have been planted. Prepare for carnage.\n"
            "-# Chance of explosion is currently **1 in " + str(chance) + "**. "
            "Timeout for stepping on a landmine is **" + str(timeout_in_seconds) + "** seconds. "
            "Currently there are a total of " + str(global_mines) + " mines."
        )


@bot.slash_command(description="Plant any number of landmines in this channel only.", default_member_permissions=disnake.Permissions(moderate_members=True))
async def plant(
    inter: disnake.AppCmdInter,
    count: int = commands.Param(gt=0, lt=max_bombs, description="Number of mines to plant"),
    chance: int = commands.Param(default=chance, gt=1, description="1 in X chance: Defaults to " + str(chance)),
    timeout: int = commands.Param(default=timeout_in_seconds, gt=0, description="Timeout in seconds: Defaults to " + str(timeout_in_seconds))
):
    ch_id = inter.channel_id

    if ch_id not in channel_mines:
        channel_mines[ch_id] = []

    for _ in range(count):
        channel_mines[ch_id].append({
            "chance": chance,
            "timeout": timeout
        })

    await inter.response.send_message(
        f"**{count}** mine{'s' if count != 1 else ''} have been planted in this channel.\n"
        f"-# Chance of explosion for these mines is **1 in {chance}**. "
        f"Timeout is **{timeout}** seconds. "
        f"Currently there are **{len(channel_mines[ch_id])}** mines in this channel."
    )


@bot.slash_command(description="List local mines in this channel.")
async def listmines(inter: disnake.AppCmdInter):
    ch_id = inter.channel_id
    mines = channel_mines.get(ch_id, [])
    if not mines:
        await inter.response.send_message("There are no mines in this channel.", ephemeral=True)
        return

    lines = []
    for i, m in enumerate(mines, start=1):
        lines.append(f"{i}. chance=1 in {m['chance']}, timeout={m['timeout']}s")

    await inter.response.send_message(
        "Local mines in this channel:\n" + "\n".join(lines), ephemeral=not(inter.channel.permissions_for(inter.author).moderate_members)
    )


@bot.event
async def on_message(message: disnake.Message):
    if message.author.bot:
        return

    global global_mines

    ch_id = message.channel.id
    local_list = channel_mines.get(ch_id, [])

    exploded = False

    if local_list:
        mine = random.choice(local_list)
        local_chance = mine["chance"]
        local_timeout = mine["timeout"]

        if random.randint(1, local_chance) == 1:
            local_list.pop(0)
            exploded = True
            await message.add_reaction("💥")
            perms = message.channel.permissions_for(message.author)
            if perms.moderate_members:
                await message.reply(
                    f"💥 {message.author.mention} stepped on a landmine! "
                    f"mod abuse.\n"
                    f"-# Mines Remaining in {message.channel.mention}: {len(local_list)}"
                )
            else:
                await message.reply(
                    f"💥 {message.author.mention} stepped on a landmine! "
                    f"They've been timed out for {local_timeout} seconds!\n"
                    f"-# Mines Remaining in {message.channel.mention}: {len(local_list)}"
                )
                try:
                    await message.author.timeout(
                        duration=local_timeout,
                        reason="Stepped on a landmine!"
                    )
                except Exception as e:
                    print("Couldn't timeout:", e)


    if not exploded and global_mines > 0:
        await message.add_reaction("💥")
        if random.randint(1, chance) == 1:
            global_mines -= 1

            await message.reply(
                f"💥 {message.author.mention} stepped on a landmine! "
                f"mod abuse.\n"
                f"-# Global Mines Remaining: {global_mines}"
            )
            try:
                await message.author.timeout(
                    duration=timeout_in_seconds,
                    reason="Stepped on a landmine!"
                )
            except Exception as e:
                print("Couldn't timeout:", e)

    await bot.process_commands(message)

@bot.slash_command(description="Destroy all mines, everywhere, immediately.", default_member_permissions=disnake.Permissions(moderate_members=True))
async def destroyallmines(inter: disnake.AppCmdInter):
    global channel_mines
    global global_mines
    channel_mines = {}
    global_mines = 0
    await inter.response.send_message(
        "ALL MINES CLEARED"
    )

@bot.slash_command(description="Information about the bot.")
async def info(inter: disnake.AppCmdInter):
    embed = disnake.Embed(title="Minefield Bot",
                        description="A simple bot, made for the WPlace Discord Server, that allows for mods to plant mines, either in a channel or globally, with a custom chance to explode and a custom timeout period. When a user sends a message, a mine has a random chance to go off (defined in either the config or the command)",
                        colour=0xc068f0)

    embed.set_author(name="See on Github",
                    url="https://github.com/lvlobjective/MinefieldDiscordBot",
                    icon_url="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png")

    embed.set_footer(text="Developed by @notaimingatall",
                    icon_url="https://cdn.discordapp.com/avatars/1160498462400462861/00bfb44563e8cad87fdbbb232bc33327.png?size=4096")

    await inter.response.send_message(
        embed=embed
    )

bot.run(Token)
