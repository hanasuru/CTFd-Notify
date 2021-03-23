from dotenv import load_dotenv
load_dotenv()

from discord.ext import commands
from discord.ext import tasks
from discord import Game
from discord import Status

import database
import utils

import time
import os

sessions = utils.get_session()
client = commands.Bot(
    command_prefix='.'
)


@client.event
async def on_ready():
    on_challenge_update.start()
    on_submission_update.start()

    sessions.get_teams()

    await client.change_presence(
        status = Status.online,
        activity = Game(os.getenv('STATUS'))
    )

    print('[+] Bot is ready to start')

@client.command('flag')
async def flag(ctx):
    flag = os.getenv('FLAG')
    await ctx.message.delete()
    await ctx.author.send(flag)

@client.command('scoreboard')
async def scoreboard(ctx):
    scoreboard_data = sessions.get_scoreboards()
    response = '== Scoreboard ==\n'

    for data in scoreboard_data:
        rank = data.get('rank')
        team = data.get('team_name')
        score = data.get('score')
        
        response += f'{rank}. {team} [{score} pts]\n'

    await ctx.send(f'```{response}```')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('All required arguments not passed')
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send('Arguments sent not correct')
        return

    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command does not exist')
        return

    if isinstance(error, commands.CommandInvokeError):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You don\' have enough permissions to perform the task')
        return

@tasks.loop(seconds=10)
async def on_challenge_update():
    print('[~] Updating challenge')

    update_challenge = sessions.get_update_challenges()
    channel = client.get_channel(int(os.getenv('CHANNEL_ID')))

    for challenge in update_challenge.values():
        print(f'   * Added {challenge} challenges')
        response = f':zap: New {challenge} :zap:'

        await channel.send(response)

@tasks.loop(seconds=5)
async def on_submission_update():
    print('[#] Checking submission')
    channel = client.get_channel(int(os.getenv('CHANNEL_ID')))
    sessions.get_submissions()

    for submissions in sessions.current_submission.values():
        for submission in submissions:
            team_name = submission.get('team_name')
            challenge_name = submission.get('challenge_name')
            first_blood_status = submission.get('first_blood_status')

            if first_blood_status:
                response = f':drop_of_blood: First blood for **{challenge_name}** goes to `{team_name}`'
            else:
                response = f':fire: `{team_name}` has solved **{challenge_name}**'
            
            print(f'   {response}')
            await channel.send(response)

    sessions.current_submission = {}

if __name__ == '__main__':
    database.migrate()
    client.run(os.getenv('TOKEN'))
    