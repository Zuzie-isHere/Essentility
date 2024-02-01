# Discord Bot Script
# Author: Zuzie
# Date: January 31, 2024 

import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

preset_permissions = {
    "admin": discord.Permissions(
        administrator=True,
        manage_channels=True,
        manage_guild=True,
        kick_members=True,
        ban_members=True,
        manage_messages=True,
        manage_roles=True,
    ),
    "mod": discord.Permissions(
        kick_members=True,
        manage_messages=True,
        manage_roles=True,
    ),
    "usuarios": discord.Permissions(
        send_messages=True,
        read_messages=True,
    )
}

async def delete_message_after_delay(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except discord.errors.NotFound:
        pass

async def send_and_delete(ctx, content, delay=5):
    message = await ctx.send(content)
    await delete_message_after_delay(message, delay)

async def unmute_after_delay(member, muted_role, delay):
    await asyncio.sleep(delay)
    await member.remove_roles(muted_role)
    unmute_message = await member.guild.get_channel(member.guild.system_channel.id).send(f'{member} has been unmuted after {delay} seconds.')
    await delete_message_after_delay(unmute_message, delay=5)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Dev BY zuzie"))
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await send_and_delete(ctx, "Invalid command. Type `!help` for a list of commands.")
    elif isinstance(error, commands.MissingPermissions):
        await send_and_delete(ctx, "You don't have permission to use this command.")
    else:
        print(f"An error occurred: {error}")

@bot.command(name='banlist')
async def banlist(ctx):
    if ctx.author.guild_permissions.ban_members:
        bans = await ctx.guild.bans()

        ban_list = []
        async for ban_entry in bans:
            ban_list.append(f"{ban_entry.user.name}: {ban_entry.reason or 'No reason provided'} ({ban_entry.created_at}) {ban_entry.user.id}")

        if ban_list:
            banlist_message = "Banned Users:\n"
            banlist_message += "\n".join(ban_list)
            await ctx.send(banlist_message)
        else:
            await ctx.send("The ban list is empty.")
    else:
        await send_and_delete(ctx, "You don't have permission to view the ban list.")

@bot.command(name='createrole')
async def create_role(ctx, role_name, preset="usuarios", color=None, position=None):
    guild = ctx.guild

    if preset in preset_permissions:
        new_role = await guild.create_role(name=role_name, color=color, permissions=preset_permissions[preset])
        await send_and_delete(ctx, f'Created a new role with the name {role_name} and assigned preset permissions for {preset}.', delay=5)

        if position is not None:
            reference_role = guild.roles[position]
            await new_role.edit(position=reference_role.position - 1)
    else:
        await send_and_delete(ctx, f'Invalid preset: {preset}. Please choose from admin, mod, or usuarios.', delay=5)

    await send_and_delete(ctx, "", delay=5)  # Vacío para borrar el mensaje de comando original

@bot.command(name='kick')
async def kick(ctx, member: discord.Member, *, reason=None):
    if ctx.author.guild_permissions.kick_members:
        await member.send(f'You have been kicked from {ctx.guild.name} for the following reason: {reason}')
        await member.kick(reason=reason)
        await send_and_delete(ctx, f'{member} has been kicked for {reason}.')
    else:
        await send_and_delete(ctx, "You don't have permission to kick members.")

@bot.command(name='ban')
async def ban(ctx, member: discord.Member, *, reason=None):
    if ctx.author.guild_permissions.ban_members:
        await member.send(f'You have been banned from {ctx.guild.name} for the following reason: {reason}')
        await member.ban(reason=reason)
        await send_and_delete(ctx, f'{member} has been banned for {reason}.')
    else:
        await send_and_delete(ctx, "You don't have permission to ban members.")

@bot.command(name='purge')
async def purge(ctx, amount: int):
    if ctx.author.guild_permissions.manage_messages:
        deleted_messages = await ctx.channel.purge(limit=amount + 1)
        await send_and_delete(ctx, f'Successfully purged {len(deleted_messages) - 1} messages.')
    else:
        await send_and_delete(ctx, "You don't have permission to manage messages.")

@bot.command(name='mute')
async def mute(ctx, member: discord.Member, mute_time: int = None):
    if ctx.author.guild_permissions.manage_roles:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", permissions=discord.Permissions(send_messages=False))
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False)

        await member.add_roles(muted_role)
        await send_and_delete(ctx, f'{member} has been muted.')

        if mute_time:
            asyncio.create_task(unmute_after_delay(member, muted_role, mute_time))
    else:
        await send_and_delete(ctx, "You don't have permission to manage roles.")

@bot.command(name='unmute')
async def unmute(ctx, member: discord.Member):
    if ctx.author.guild_permissions.manage_roles:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            await send_and_delete(ctx, f'{member} has been unmuted.')
        else:
            await send_and_delete(ctx, f'{member} is not muted.')
    else:
        await send_and_delete(ctx, "You don't have permission to manage roles.")

@bot.command(name='unban')
async def unban(ctx, user_id: int):
    if ctx.author.guild_permissions.ban_members:
        try:
            user_to_unban = await bot.fetch_user(user_id)
            await ctx.guild.unban(user_to_unban)
            await send_and_delete(ctx, f'{user_to_unban} has been unbanned.')
        except discord.NotFound:
            await send_and_delete(ctx, f'User with ID {user_id} not found or not banned.')
    else:
        await send_and_delete(ctx, "You don't have permission to unban members.")

@bot.command(name='editrole')
async def edit_role(ctx, role_name, *permissions):
    if ctx.author.guild_permissions.manage_roles:
        permissions = discord.Permissions()
        color = None
        position = None

        for perm in permissions:
            if perm.startswith("color="):
                color = discord.Color(int(perm.split('=')[1][1:], 16)) if perm.split('=')[1].startswith('#') else None
            elif perm.isdigit():
                position = int(perm)
            else:
                if perm.startswith("-"):
                    setattr(permissions, perm[1:], False)
                else:
                    setattr(permissions, perm, True)

        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=role_name)

        if role:
            await role.edit(permissions=permissions, color=color)
            await send_and_delete(ctx, f'Edited role {role_name} successfully.', delay=5)

            if position is not None:
                roles = guild.roles
                role_position = len(roles) - position
                await role.edit(position=role_position)
        else:
            await send_and_delete(ctx, f'Role {role_name} not found.', delay=5)
    else:
        await send_and_delete(ctx, "You don't have permission to manage roles.", delay=5)

try:
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise Exception("Please set the DISCORD_TOKEN environment variable.")
    bot.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        raise e
except Exception as ex:
    print(f"An error occurred: {ex}")
