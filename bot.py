import discord
from discord.ext import commands, tasks
from discord import app_commands
#from dotenv import load_dotenv
import os
import random
import json
from datetime import datetime

# Helper function to get the current timestamp
def get_timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

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
            members_str = "\n".join([f"- {interaction.guild.get_member(int(member)).display_name if interaction.guild.get_member(int(member)) else member}" for member in members])
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

# Slash command: Assign a role to a user
@tree.command(name="assign_role", description="Assign a role to a user.")
@app_commands.default_permissions(manage_roles=True)  # Only users with Manage Roles permission can use this
async def assign_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    guild = interaction.guild
    if role not in guild.roles:
        await interaction.response.send_message(f"Role '{role.name}' does not exist in this server!", ephemeral=True)
        return

    await member.add_roles(role)
    await interaction.response.send_message(f"Role '{role.name}' has been assigned to {member.mention}!")

# Slash command: Remove a role from a user
@tree.command(name="remove_role", description="Remove a role from a user.")
@app_commands.default_permissions(manage_roles=True)  # Only users with Manage Roles permission can use this
async def remove_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    guild = interaction.guild
    if role not in guild.roles:
        await interaction.response.send_message(f"Role '{role.name}' does not exist in this server!", ephemeral=True)
        return

    await member.remove_roles(role)
    await interaction.response.send_message(f"Role '{role.name}' has been removed from {member.mention}!")

# Slash command: Distribute roles based on criteria
@tree.command(name="distribute_roles", description="Distribute roles to users based on criteria.")
@app_commands.default_permissions(manage_roles=True)  # Only users with Manage Roles permission can use this
async def distribute_roles(interaction: discord.Interaction, role: discord.Role, criterion: str):
    guild = interaction.guild

    if role not in guild.roles:
        await interaction.response.send_message(f"Role '{role.name}' does not exist in this server!", ephemeral=True)
        return

    # Example criterion: Assign role to all users in a specific team
    if criterion.startswith("team:"):
        team_name = criterion.split("team:")[1].strip()
        if team_name not in teams:
            await interaction.response.send_message(f"Team '{team_name}' does not exist!", ephemeral=True)
            return

        members_to_assign = teams[team_name]
        for member_id in members_to_assign:
            member = guild.get_member(int(member_id))
            if member:
                await member.add_roles(role)

        await interaction.response.send_message(f"Role '{role.name}' has been assigned to all members of team '{team_name}'!")

    else:
        await interaction.response.send_message(f"Unknown criterion: {criterion}", ephemeral=True)

# Slash command: List roles of a user
@tree.command(name="list_roles", description="List all roles of a user.")
async def list_roles(interaction: discord.Interaction, member: discord.Member):
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    roles_str = ", ".join(roles) if roles else "No roles assigned."
    await interaction.response.send_message(f"{member.mention} has the following roles: {roles_str}")

# Slash command: Set up automatic role distribution
@tree.command(name="setup_auto_roles", description="Set up automatic role distribution based on criteria.")
@app_commands.default_permissions(manage_roles=True)  # Only users with Manage Roles permission can use this
async def setup_auto_roles(interaction: discord.Interaction, role: discord.Role, criterion: str):
    global auto_role_criterion, auto_role
    guild = interaction.guild

    if role not in guild.roles:
        await interaction.response.send_message(f"Role '{role.name}' does not exist in this server!", ephemeral=True)
        return

    auto_role_criterion = criterion
    auto_role = role
    auto_role_distributor.start()  # Start the background task
    await interaction.response.send_message(f"Automatic role distribution set up for role '{role.name}' with criterion '{criterion}'!")

# Background task: Automatically distribute roles
@tasks.loop(minutes=10)  # Runs every 10 minutes
async def auto_role_distributor():
    guild = bot.guilds[0]  # Assuming the bot is in one guild
    if not auto_role or not auto_role_criterion:
        return

    # Example criterion: Assign role to all users in a specific team
    if auto_role_criterion.startswith("team:"):
        team_name = auto_role_criterion.split("team:")[1].strip()
        if team_name not in teams:
            print(f"Team '{team_name}' does not exist! Skipping auto role distribution.")
            return

        members_to_assign = teams[team_name]
        for member_id in members_to_assign:
            member = guild.get_member(int(member_id))
            if member and auto_role not in member.roles:
                await member.add_roles(auto_role)
                print(f"Assigned role '{auto_role.name}' to {member.display_name}.")

# Stop the background task when the bot shuts down
@bot.event
async def on_disconnect():
    auto_role_distributor.stop()

# Initialize global variables for auto role distribution
auto_role_criterion = None
auto_role = None

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    log_channel_id = 1363575519764938793  # Channel ID to send logs to
    log_channel = bot.get_channel(log_channel_id)

    if not log_channel:
        print(f"{get_timestamp()} Could not find channel with ID {log_channel_id} to send voice logs.")
        return

    # Determine the type of event (join, leave, or move)
    if before.channel is None and after.channel is not None:
        # User joined a voice channel
        message = f"{get_timestamp()} 🔊 {member.mention} (**{member.name}#{member.discriminator}**) joined voice channel {after.channel.mention}."
    elif before.channel is not None and after.channel is None:
        # User left a voice channel
        message = f"{get_timestamp()} 🔇 {member.mention} (**{member.name}#{member.discriminator}**) left voice channel {before.channel.mention}."
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        # User moved between voice channels
        message = f"{get_timestamp()} 🔄 {member.mention} (**{member.name}#{member.discriminator}**) moved from {before.channel.mention} to {after.channel.mention}."
    else:
        # No relevant change
        return

    # Send the log message to the specified channel
    try:
        await log_channel.send(message)
        print(f"{get_timestamp()} Sent voice log to channel {log_channel.name}: {message}")
    except discord.Forbidden:
        print(f"{get_timestamp()} Could not send message to channel {log_channel_id}. The bot might lack permissions.")
    except Exception as e:
        print(f"{get_timestamp()} An error occurred while sending a voice log: {e}")

# Run the bot using the token from the environment variable
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Error: DISCORD_TOKEN is not set in the environment variables.")

