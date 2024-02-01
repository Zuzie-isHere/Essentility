# Discord Bot Script
# Author: Zuzie
# Date: January 31, 2024 (added !Mute | !Unmute)


import os
import discord
import asyncio

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

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

async def unmute_after_delay(member, muted_role, delay):
    await asyncio.sleep(delay)
    await member.remove_roles(muted_role)
    unmute_message = await member.guild.get_channel(member.guild.system_channel.id).send(f'{member} has been unmuted after {delay} seconds.')
    await delete_message_after_delay(unmute_message, delay=5)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="Dev BY zuzie"))
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    lowercased_content = message.content.lower()

    if lowercased_content.startswith('!banlist'):
        print("Executing !banlist block")
        print(f"Message content: {message.content}")
        if message.author.guild_permissions.ban_members:
            bans = await message.guild.bans()

            ban_list = []
            async for ban_entry in bans:
                ban_list.append(f"{ban_entry.user.name}: {ban_entry.reason or 'No reason provided'} ({ban_entry.created_at}) {ban_entry.user.id}")

            if ban_list:
                banlist_message = "Banned Users:\n"
                banlist_message += "\n".join(ban_list)
                await message.channel.send(banlist_message)
            else:
                await message.channel.send("The ban list is empty.")
        else:
            permission_message = await message.channel.send("You don't have permission to view the ban list.")
            await delete_message_after_delay(permission_message, delay=5)

    elif lowercased_content.startswith('!createrole'):
        args = message.content.split()[1:]
        role_name = args[0]
        preset = args[1] if len(args) > 1 else "usuarios"
        color = discord.Color(int(args[2][1:], 16)) if len(args) > 2 and args[2].startswith('#') else None
        position = int(args[3]) if len(args) > 3 else None

        guild = message.guild

        if preset in preset_permissions:
            new_role = await guild.create_role(name=role_name, color=color, permissions=preset_permissions[preset])
            created_message = await message.channel.send(f'Created a new role with the name {role_name} and assigned preset permissions for {preset}.')
            await delete_message_after_delay(created_message, delay=5)
            if position is not None:
                roles = guild.roles
                reference_role = roles[position]
                await new_role.edit(position=reference_role.position - 1)
        else:
            invalid_message = await message.channel.send(f'Invalid preset: {preset}. Please choose from admin, mod, or usuarios.')
            await delete_message_after_delay(invalid_message, delay=5)

        await delete_message_after_delay(message, delay=5)

    elif lowercased_content.startswith('!editrole'):
        args = message.content.split()[1:]

        if len(args) < 1:
            await message.channel.send("Please provide the role name for editing.")
            return

        role_name = args[0]

        if len(args) < 2:
            await message.channel.send(f"Please provide at least one permission to edit for the role {role_name}.")
            return

        permissions = discord.Permissions()
        color = None
        position = None

        for perm in args[1:]:
            if perm.startswith("color="):
                color = discord.Color(int(perm.split('=')[1][1:], 16)) if perm.split('=')[1].startswith('#') else None
            elif perm.isdigit():
                position = int(perm)
            else:
                if perm.startswith("-"):
                    setattr(permissions, perm[1:], False)
                else:
                    setattr(permissions, perm, True)

        guild = message.guild
        role = discord.utils.get(guild.roles, name=role_name)

        if role:
            await role.edit(permissions=permissions, color=color)
            edited_message = await message.channel.send(f'Edited role {role_name} successfully.')
            await delete_message_after_delay(edited_message, delay=5)

            if position is not None:
                roles = guild.roles
                role_position = len(roles) - position
                await role.edit(position=role_position)
        else:
            not_found_message = await message.channel.send(f'Role {role_name} not found.')
            await delete_message_after_delay(not_found_message, delay=5)

        await delete_message_after_delay(message, delay=5)

    elif lowercased_content.startswith('!ban'):
        print("Executing !ban block")
        print(f"Message content: {message.content}")
        if message.author.guild_permissions.ban_members:
            user_message = message.content.split(' ')
            if len(user_message) >= 3:
                if message.mentions:
                    user_to_ban = message.mentions[0]
                    reason = ' '.join(user_message[2:])
                    await message.guild.ban(user_to_ban, reason=reason)
                    await user_to_ban.send(f'You have been banned from {message.guild.name} for the following reason: {reason}')
                    banned_message = await message.channel.send(f'{user_to_ban} has been banned for {reason}.')
                    await delete_message_after_delay(banned_message, delay=5)
                else:
                    mention_message = await message.channel.send("Please mention the user to ban.")
                    await delete_message_after_delay(mention_message, delay=5)
            elif len(user_message) == 2:
                if message.mentions:
                    user_to_ban = message.mentions[0]
                    await message.guild.ban(user_to_ban)
                    await user_to_ban.send(f'You have been banned from {message.guild.name}.')
                    banned_message = await message.channel.send(f'{user_to_ban} has been banned.')
                    await delete_message_after_delay(banned_message, delay=5)
                else:
                    mention_message = await message.channel.send("Please mention the user to ban.")
                    await delete_message_after_delay(mention_message, delay=5)
            else:
                mention_message = await message.channel.send("Please mention the user to ban and provide a reason.")
                await delete_message_after_delay(mention_message, delay=5)

            await delete_message_after_delay(message, delay=5)

    elif lowercased_content.startswith('!kick'):
        if message.author.guild_permissions.kick_members:
            user_message = message.content.split(' ')
            if len(user_message) >= 2:
                if message.mentions:
                    user_to_kick = message.mentions[0]
                    reason = ' '.join(user_message[2:])
                    await user_to_kick.send(f'You have been kicked from {message.guild.name} for the following reason: {reason}')
                    await user_to_kick.kick(reason=reason)
                    kicked_message = await message.channel.send(f'{user_to_kick} has been kicked for {reason}.')
                    await delete_message_after_delay(kicked_message, delay=5)
                else:
                    mention_message = await message.channel.send("Please mention the user to kick.")
                    await delete_message_after_delay(mention_message, delay=5)
            else:
                mention_message = await message.channel.send("Please mention the user to kick and provide a reason.")
                await delete_message_after_delay(mention_message, delay=5)
        else:
            permission_message = await message.channel.send("You don't have permission to kick members.")
            await delete_message_after_delay(permission_message, delay=5)

        await delete_message_after_delay(message, delay=5)

    elif lowercased_content.startswith('!purge'):
        if message.author.guild_permissions.manage_messages:
            try:
                amount = int(message.content.split(' ')[1])
                deleted_messages = await message.channel.purge(limit=amount + 1)
                purge_message = await message.channel.send(f'Successfully purged {amount} messages.')
                await delete_message_after_delay(purge_message, delay=5)
            except IndexError:
                await message.channel.send('Please specify the number of messages to purge.')
            except ValueError:
                await message.channel.send('Invalid amount. Please specify a valid number.')
        else:
            permission_message = await message.channel.send("You don't have permission to manage messages.")
            await delete_message_after_delay(permission_message, delay=5)

        await delete_message_after_delay(message, delay=5)

    elif lowercased_content.startswith('!mute'):
        if message.author.guild_permissions.manage_roles:
            if message.mentions:
                member_to_mute = message.mentions[0]
                muted_role = discord.utils.get(message.guild.roles, name="Muted")

                if not muted_role:
                    muted_role = await message.guild.create_role(name="Muted", permissions=discord.Permissions(send_messages=False))
                    for channel in message.guild.channels:
                        await channel.set_permissions(muted_role, send_messages=False)

                await member_to_mute.add_roles(muted_role)
                mute_message = await message.channel.send(f'{member_to_mute} has been muted.')
                await delete_message_after_delay(mute_message, delay=5)

                mute_time = None
                if len(message.content.split()) > 2 and message.content.split()[2].isdigit():
                    mute_time = int(message.content.split()[2])

                if mute_time:
                    asyncio.create_task(unmute_after_delay(member_to_mute, muted_role, mute_time))
        else:
            permission_message = await message.channel.send("You don't have permission to manage roles.")
            await delete_message_after_delay(permission_message, delay=5)

        await delete_message_after_delay(message, delay=5)

    elif lowercased_content.startswith('!unmute'):
        if message.author.guild_permissions.manage_roles:
            if message.mentions:
                member_to_unmute = message.mentions[0]
                muted_role = discord.utils.get(message.guild.roles, name="Muted")

                if muted_role in member_to_unmute.roles:
                    await member_to_unmute.remove_roles(muted_role)
                    unmute_message = await message.channel.send(f'{member_to_unmute} has been unmuted.')
                    await delete_message_after_delay(unmute_message, delay=5)
                else:
                    unmute_message = await message.channel.send(f'{member_to_unmute} is not muted.')
                    await delete_message_after_delay(unmute_message, delay=5)
            else:
                mention_message = await message.channel.send("Please mention the user to unmute.")
                await delete_message_after_delay(mention_message, delay=5)
        else:
            permission_message = await message.channel.send("You don't have permission to manage roles.")
            await delete_message_after_delay(permission_message, delay=5)

        await delete_message_after_delay(message, delay=5)

    elif lowercased_content.startswith('!unban'):
        if message.author.guild_permissions.ban_members:
            user_message = message.content.split(' ')
            if len(user_message) >= 2:
                user_id = user_message[1]

                try:
                    user_to_unban = await client.fetch_user(user_id)
                    await message.guild.unban(user_to_unban)
                    unban_message = await message.channel.send(f'{user_to_unban} has been unbanned.')
                    await delete_message_after_delay(unban_message, delay=5)
                except discord.NotFound:
                    not_found_message = await message.channel.send(f'User with ID {user_id} not found or not banned.')
                    await delete_message_after_delay(not_found_message, delay=5)
            else:
                mention_message = await message.channel.send("Please provide the user ID to unban.")
                await delete_message_after_delay(mention_message, delay=5)
        else:
            permission_message = await message.channel.send("You don't have permission to unban members.")
            await delete_message_after_delay(permission_message, delay=5)

        await delete_message_after_delay(message, delay=5)

try:
    token = "YOUR_TOKEN_HERE HEHE"
    if token == "":
        raise Exception("Please add your token.")
    client.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        raise e
except Exception as ex:
    print(f"An error occurred: {ex}")
