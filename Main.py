import os
import discord

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

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="Dev BY zuzie.1"))
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

    elif message.content.startswith('!createrole'):
        args = message.content.split()[1:]
        role_name = args[0]
        preset = args[1] if len(args) > 1 else "usuarios"
        color = discord.Color(int(args[2][1:], 16)) if len(args) > 2 and args[2].startswith('#') else None
        position = int(args[3]) if len(args) > 3 else None

        guild = message.guild

        if preset in preset_permissions:
            new_role = await guild.create_role(name=role_name, color=color, permissions=preset_permissions[preset])
            await message.channel.send(f'Created a new role with the name {role_name} and assigned preset permissions for {preset}.')
            if position is not None:

                roles = guild.roles
                reference_role = roles[position]

                await new_role.edit(position=reference_role.position - 1)
        else:
            await message.channel.send(f'Invalid preset: {preset}. Please choose from admin, mod, or usuarios.')

    elif message.content.startswith('!editrole'):
        args = message.content.split()[1:]
        role_name = args[0]
        permissions = discord.Permissions()
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
            await role.edit(permissions=permissions, color=color if 'color' in locals() else None)
            await message.channel.send(f'Edited role {role_name} successfully.')
            if position is not None:
                roles = guild.roles
                role_position = len(roles) - position
                await role.edit(position=role_position)
        else:
            await message.channel.send(f'Role {role_name} not found.')

    elif message.content.startswith('!ban'):
        if message.author.guild_permissions.ban_members:
            user_message = message.content.split(' ')
            if len(user_message) >= 3:
                if message.mentions:
                    user_to_ban = message.mentions[0]
                    reason = ' '.join(user_message[2:])
                    await message.guild.ban(user_to_ban, reason=reason)
                    await message.channel.send(f'{user_to_ban} has been banned for {reason}.')
                else:
                    await message.channel.send("Please mention the user to ban.")
            elif len(user_message) == 2:
                if message.mentions:
                    user_to_ban = message.mentions[0]
                    await message.guild.ban(user_to_ban)
                    await message.channel.send(f'{user_to_ban} has been banned.')
                else:
                    await message.channel.send("Please mention the user to ban.")
            else:
                await message.channel.send("Please mention the user to ban and provide a reason.")

    elif message.content.startswith('!purge'):
        if message.author.guild_permissions.manage_messages:
            try:
                amount = int(message.content.split(' ')[1])
                await message.channel.purge(limit=amount + 1)

                await message.channel.send(f'Successfully purged {amount} messages.', delete_after=5)

            except IndexError:
                await message.channel.send('Please specify the number of messages to purge.')
            except ValueError:
                await message.channel.send('Invalid amount. Please specify a valid number.')
        else:
            await message.channel.send("You don't have permission to manage messages.")

    try:
        await message.delete()
    except discord.errors.NotFound:
        pass

    async for msg in message.channel.history(limit=1):
        if msg.author == client.user:
            try:
                await msg.delete()
            except discord.errors.NotFound:
                pass

try:
  
  token = "TOKEN!"
  if token == "":
      raise Exception("Please add your token.")
  client.run(token)
except discord.HTTPException as e:
  if e.status == 429:
      raise e  
    
except Exception as ex:
  print(f"An error occurred: {ex}")