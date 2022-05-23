import asyncio
import random
import re

import discord
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
from discord import Option

import languages

token = "token"
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

@discordbot.event
async def on_message(message):
    global typing
    if typing:
        return
    if message.author == discordbot.user:
        return

    typing = True
    try:

        # 待機
        async with message.channel.typing():
            await asyncio.sleep(8)
        typing = False
        response = chatbot.get_response(message.content)
        print('{}: {}'.format(chatbot.name, response))

        # メンション削除
        pattern = r'<@!?(\d+)>'
        match = re.findall(pattern, str(response))
        for user_id in match:
            user = await discordbot.fetch_user(user_id)
            user_name = f'、{user.name}'
            response = re.sub(rf'<@!?{user_id}>', user_name, response)
        pattern = r'<@&(\d+)>'
        match = re.findall(pattern, str(response))
        for role_id in match:
            role = message.guild.get_role(int(role_id))
            role_name = f'、{role.name}'
            response = re.sub(f'<@&{role_id}>', role_name, response)

        if response is not None:
            await message.reply(response)
    except(KeyboardInterrupt, EOFError, SystemExit, discord.errors.HTTPException):
        print("返答不可")
    typing = False


@discordbot.slash_command()
async def learning(ctx,
                   target: Option(discord.Member, "メンバー", required=False)):
    if can_use_learning_command not in ctx.author.id:
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
