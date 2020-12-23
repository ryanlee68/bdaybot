import discord
import datetime
import traceback
from discord.ext import commands

def fake_ctx(bot, command, guild):
    # Used to so that we can call command
    # from within the bot itself
    if isinstance(command, str):
        command = bot.get_command(command)
    if not isinstance(command, commands.Command):
        raise ValueError(f'command must be either a str or Commmand type, not {type(command)}')
    stringview = commands.view.StringView(f'{bot.parsed_command_prefix}{command.name}')
    message_dict = {
        'id': 0,
        'attachments': [],
        'embeds': [],
        'edited_timestamp': None,
        'type': None,
        'pinned': False,
        'mention_everyone': False,
        'tts': False
    }
    message_dict['content'] = f'{bot.parsed_command_prefix}{command.name}'
    message = discord.message.Message(state='lol', channel=guild.text_channels[0], data=message_dict)
    return commands.Context(message=message, bot=bot, prefix=bot.parsed_command_prefix,
                            invoked_with=command.name, view=stringview, command=command)

def apostrophe(name):
    return "'" if name[-1] == "s" else "'s"

def format_iterable(iterable,
                    apos=True,
                    separator=',',
                    conjunction='and',
                    get_str=lambda ref, index: ref[index]):
    if not hasattr(iterable, '__len__'):
        iterable = list(iterable)

    if len(iterable) == 1:
        result = get_str(iterable, 0)
        return f"{result}{apostrophe(result) if apos else ''}"
    elif len(iterable) == 2:
        result1 = get_str(iterable, 0)
        result2 = get_str(iterable, 1)
        return f"{result1} {last} {result2}{apostrophe(result2) if apos else ''}"

    returning = ''
    for counter in range(len(iterable)):
        result = get_str(iterable, counter)
        returning += f"{last} {result}{apostrophe(result) if apos else ''}" if counter == len(iterable) - 1 \
                     else f'{result}, '
    return returning

def get_bday_names(apos=True):
    # DEBUG: DO NOT move this import!
    # It is here to avoid circular import issues.
    from . import values
    def df_get_str(iterable, index):
        return iterable.iloc[index]['FirstName'] + ' ' + iterable.iloc[index]['LastName']
    return format_iterable(values.today_df,
                           apos=apos,
                           get_str=df_get_str,
                           iterr_func=lambda df: df.iterrows())

def maybe_mention(ctx):
    return f'{ctx.author.mention} ' if ctx.guild else ''

def find_ann_channel(guild):
    bday_channels = list(filter(lambda channel: 'bday' in channel.name.lower(), guild.text_channels))
    ann_channels = list(filter(lambda channel: 'announcement' in channel.name.lower(), guild.text_channels))
    if bday_channels:
        return bday_channels[0]
    elif ann_channels:
        return ann_channels[0]
    return None

def permissions(channel, member, permissions, condition='all'):
    if channel is None:
        return True
    condition = condition.lower()
    perms = channel.permissions_for(member)
    if isinstance(permissions, (list, tuple)):
        if condition == 'all':
            return all([getattr(perms, perm) for perm in permissions])
        elif condition == 'any':
            return any([getattr(perms, perm) for perm in permissions])
        else:
            raise ValueError((f"'{condition}' is not an acceptable condition. "
                               "The acceptable conditions are 'all' or 'any'."))
    else:
        return getattr(perms, permissions)

async def ping_devs(error, command, ctx=None, bot=None):
    # DEBUG: DO NOT move this import!
    # It is here to avoid circular import issues.
    from . import config
    if ctx is None:
        assert bot is not None, 'bot not be None if ctx is None'
    else:
        bot = ctx.bot
        discord_location = ctx.guild if ctx.guild else 'a DM message'
    error_message = traceback.format_exc()
    if error_message == 'NoneType: None\n':
        error_message = repr(error)
    devs = {
        'Andres': [await bot.get_user(388899325885022211), config.andres],
        'Elliot': [await bot.get_user(349319578419068940), config.elliot],
        'Ryan': [await bot.get_user(262676325846876161), config.ryan]
    }

    for name, (dev, sending) in devs.items():
        if sending:

            if hasattr(ctx, 'author'):
                await dev.send((f"{ctx.author.mention} caused the following error with `{command.name}` in "
                                f"**{discord_location}**, on {format(datetime.datetime.today(), '%b %d at %I:%M %p')}"
                                f":\n```\n{error_message}```"))
                await dev.send(f"The message that caused the error is the following:\n**{ctx.message.content}**")
            elif ctx is None:
                await dev.send((f"The following error occured with the `{command}` task, on "
                                f"{format(datetime.datetime.today(), '%b %d at %I:%M %p')}:"
                                f"\n```\n{error_message}```"))
            else:
                await dev.send((f"The following error occured with `{command.name}` in **{discord_location}**, "
                                f"on {format(datetime.datetime.today(), '%b %d at %I:%M %p')}:"
                                f"\n```\n{error_message}```"))

    if ctx and ctx.guild and hasattr(ctx, 'author'):
        # NOTE: Might want this to conform to config values
        devs_ping_channel = format_iterable(devs,
                                            apos=False, conjunction='or',
                                            get_str=lambda devs, index: devs[list(devs)[index]][0].mention)
        await ctx.send(f"{devs_ping_channel} fix this!")

class classproperty:
    # NOTE: The `classproperty` class
    # is NOT my (@Ahsoka's) code. See reference below
    # for original source
    # Reference: https://stackoverflow.com/questions/128573/using-property-on-classmethods/13624858#13624858
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)