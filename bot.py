import discord
from discord.ext import commands
from discord import app_commands
#from dotenv import load_dotenv
import os
import random
import json

# Uncomment the following lines if you want to use a .env file for storing the bot token
# from dotenv import load_dotenv
#load_dotenv()  # Load environment variables from a .env file
#BOT_TOKEN = os.getenv('DISCORD_TOKEN')  # Fetching from .env file

# Get the bot token from environment variables
BOT_TOKEN = os.environ.get("DISCORD_TOKEN")  # Fetching from system environment variables

# Create the bot instance
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree  # For slash commands

# In-memory storage for teams and tournaments
teams = {}  # {team_name: [member1, member2, ...]}
tournaments = {}  # {tournament_name: {"participants": [team1, team2, ...], "bracket": []}}

# JSON file paths
TEAMS_JSON = "teams.json"
TOURNAMENTS_JSON = "tournaments.json"

# Load data from JSON files
def load_data():
    global teams, tournaments
    try:
        with open(TEAMS_JSON, "r") as file:
            teams = json.load(file)
    except FileNotFoundError:
        teams = {}

    try:
        with open(TOURNAMENTS_JSON, "r") as file:
            tournaments = json.load(file)
    except FileNotFoundError:
        tournaments = {}

# Save data to JSON files
def save_data():
    with open(TEAMS_JSON, "w") as file:
        json.dump(teams, file, indent=4)

    with open(TOURNAMENTS_JSON, "w") as file:
        json.dump(tournaments, file, indent=4)

# Load data on startup
load_data()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
    try:
        synced = await tree.sync()  # Sync slash commands with Discord
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Slash command: Hello
@tree.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello there!")

# Slash command: Create a team
@tree.command(name="create_team", description="Create a new team.")
async def create_team(interaction: discord.Interaction, team_name: str):
    if team_name in teams:
        await interaction.response.send_message(f"A team with the name '{team_name}' already exists!")
    else:
        teams[team_name] = []
        save_data()
        await interaction.response.send_message(f"Team '{team_name}' has been created!")

# Slash command: Add a member to a team
@tree.command(name="add_member", description="Add a member to a team.")
async def add_member(interaction: discord.Interaction, team_name: str, member: discord.Member):
    if team_name not in teams:
        await interaction.response.send_message(f"Team '{team_name}' does not exist!")
    else:
        teams[team_name].append(str(member.id))  # Store member ID as a string
        save_data()
        await interaction.response.send_message(f"Member '{member.display_name}' has been added to team '{team_name}'!")

# Slash command: View team details
@tree.command(name="view_team", description="View details of a team.")
async def view_team(interaction: discord.Interaction, team_name: str):
    if team_name not in teams:
        await interaction.response.send_message(f"Team '{team_name}' does not exist!")
    else:
        members = teams[team_name]
        if members:
            members_str = "\n".join([f"- {member}" for member in members])
        else:
            members_str = "No members yet."
        await interaction.response.send_message(f"**Team '{team_name}':**\n**Members:**\n{members_str}")

# Slash command: Create a tournament
@tree.command(name="create_tournament", description="Create a new tournament.")
async def create_tournament(interaction: discord.Interaction, name: str):
    if name in tournaments:
        await interaction.response.send_message(f"A tournament with the name '{name}' already exists!")
    else:
        tournaments[name] = {"participants": [], "bracket": []}
        save_data()
        await interaction.response.send_message(f"Tournament '{name}' has been created!")

# Slash command: Add a team to a tournament
@tree.command(name="add_team", description="Add a team to a tournament.")
async def add_team(interaction: discord.Interaction, tournament_name: str, team_name: str):
    if tournament_name not in tournaments:
        await interaction.response.send_message(f"Tournament '{tournament_name}' does not exist!")
        return

    if team_name not in teams:
        await interaction.response.send_message(f"Team '{team_name}' does not exist!")
        return

    tournaments[tournament_name]["participants"].append(team_name)
    save_data()
    await interaction.response.send_message(f"Team '{team_name}' has been added to tournament '{tournament_name}'!")

# Slash command: View tournament details with embed
@tree.command(name="view_tournament", description="View details of a tournament.")
async def view_tournament(interaction: discord.Interaction, tournament_name: str):
    if tournament_name not in tournaments:
        await interaction.response.send_message(f"Tournament '{tournament_name}' does not exist!")
    else:
        tournament = tournaments[tournament_name]
        participants = tournament["participants"]

        embed = discord.Embed(title=f"Tournament: {tournament_name}", color=discord.Color.blue())
        if not participants:
            embed.add_field(name="Participants", value="No participants yet.", inline=False)
        else:
            for team_name in participants:
                if team_name in teams:
                    members = teams[team_name]
                    if members:
                        members_str = "\n".join([f"- <@{member_id}>" for member_id in members])  # Mention users
                    else:
                        members_str = "No members yet."
                    embed.add_field(name=f"Team: {team_name}", value=members_str, inline=False)
                else:
                    embed.add_field(name=f"Team: {team_name}", value="Team does not exist in the system.", inline=False)

        await interaction.response.send_message(embed=embed)

# Slash command: Generate a single-elimination bracket with embed
@tree.command(name="generate_bracket", description="Generate a single-elimination bracket for a tournament.")
async def generate_bracket(interaction: discord.Interaction, tournament_name: str):
    if tournament_name not in tournaments:
        await interaction.response.send_message(f"Tournament '{tournament_name}' does not exist!")
        return

    participants = tournaments[tournament_name]["participants"]
    if len(participants) < 2:
        await interaction.response.send_message("Not enough participants to generate a bracket. Add more participants!")
        return

    # Work with a copy of the participants list to preserve the original
    participants_copy = participants[:]
    random.shuffle(participants_copy)
    bracket = []
    while len(participants_copy) > 1:
        match = (participants_copy.pop(), participants_copy.pop())
        bracket.append(match)
    if participants_copy:  # Handle odd number of participants
        bracket.append((participants_copy.pop(), "BYE"))
    tournaments[tournament_name]["bracket"] = bracket
    save_data()

    embed = discord.Embed(title=f"Bracket for Tournament: {tournament_name}", color=discord.Color.green())
    for i, match in enumerate(bracket, 1):
        embed.add_field(name=f"Round {i}", value=f"{match[0]} ⚔️ {match[1]}", inline=False)  # Changed emoji to ⚔️

    await interaction.response.send_message(embed=embed)

# Run the bot using the token from the environment variable
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Error: DISCORD_TOKEN is not set in the environment variables.")