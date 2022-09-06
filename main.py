import asyncio
import random
import re
import string

import discord
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
from discord import Option
from discord.types.channel import ChannelType

import languages

token = "OTc1NzA2ODczMzcyMjI5NjM0.G-070w.pCQwJN_bkN06-h3yWhcafHYaQ7HEG_BWOleHKU"
can_use_learning_command = [349381131197480962,]

# Create a new chat bot named Charlie
intents = discord.Intents.default()
intents.message_content = True
discordbot = discord.Bot(intents=intents)
chatbot = ChatBot(
    name="bot",
    tagger_language=languages.JPN
)

typing = False

list_trainer = ListTrainer(chatbot)


# Get a response to the input text 'I would like to book a flight.'

async def get_respond(message, author, guild=None):
    try:
        response = chatbot.get_response(message)
        print('{}: {}'.format(author.name, message))
        print('{}: {}'.format(chatbot.name, response))

        # メンション削除
        pattern = r'<@!?(\d+)>'
        match = re.findall(pattern, str(response))
        for user_id in match:
            user = await discordbot.fetch_user(user_id)
            user_name = f'、{user.name}'
            response = re.sub(rf'<@!?{user_id}>', user_name, str(response))
        pattern = r'<@&(\d+)>'
        match = re.findall(pattern, str(response))
        for role_id in match and guild is not None:
            role = guild.get_role(int(role_id))
            role_name = f'、{role.name}'
            response = re.sub(f'<@&{role_id}>', role_name, str(response))

        if response is not None:
            return response
        return ""

    except(KeyboardInterrupt, EOFError, SystemExit, discord.errors.HTTPException):
        return "エラーが発生しました"

@discordbot.event
async def on_message(message):
    global typing
    if typing:
        return
    if message.author == discordbot.user:
        return
    if message.channel.type != discord.ChannelType.private:
        return

    typing = True
    response = await get_respond(message.content, message.author, message.guild)
    async with message.channel.typing():
        typing = False
        await asyncio.sleep(2)


    await message.reply(response)

    typing = False

@discordbot.slash_command()
async def talk(ctx, target: Option(str, "メッセージ", required=True)):
    message = await ctx.respond('考え中...')
    response = await get_respond(target, ctx.author, ctx.guild)
    await message.edit_original_message(content=target)
    await message.channel.send(content=response)



@discordbot.slash_command()
async def learning(ctx,
                   target: Option(discord.Member, "メンバー", required=False)):
    if ctx.author.id not in can_use_learning_command:
        await ctx.respond("許可されたユーザーのみが使用できます")
        return
    await ctx.respond("完了しました")
    async for searchmessage in ctx.channel.history(limit=None):
        print(searchmessage.content)

        if target is not None and searchmessage.author.id != target.id:
            continue

        iscancel = False

        # 対象者のメッセージが連続
        for message in await searchmessage.channel.history(limit=1, after=searchmessage).flatten():
            if message.author.id == searchmessage.author.id:
                iscancel = True
                break
        if iscancel:
            continue

        last_searchmessage = searchmessage.content

        # 返信先
        if searchmessage.reference is None:
            for message in await searchmessage.channel.history(limit=10, before=searchmessage).flatten():
                if message.author.id == searchmessage.author.id:
                    last_searchmessage += message.content
                    continue
                replied_message = message
                break
        else:
            try:
                replied_message = await searchmessage.channel.fetch_message(searchmessage.reference.message_id)
            except discord.NotFound:
                print("削除済み")

        if len(replied_message.content) < 1:
            continue
        print(replied_message.content + "->" + last_searchmessage)
        list_trainer.train([replied_message.content, last_searchmessage])


discordbot.run(token)
