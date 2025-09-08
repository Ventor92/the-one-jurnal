import os

import discord
from discord import app_commands
from discord.ext import commands

from ai_svrc import answer_query

intents = discord.Intents.default()
intents.message_content = True

if "HANDBOOK_BOT_KEY" not in os.environ or not os.environ["HANDBOOK_BOT_KEY"]:
    print("Brak zmiennej środowiskowej HANDBOOK_BOT_KEY. Ustaw ją w systemie i uruchom ponownie.")
    exit(1)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()  # Synchronizacja slash commands
        print("Slash commands zsynchronizowane!")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

# 🔹 Komenda z parametrami
@bot.tree.command(name="powiedz", description="Bot powtórzy to, co napiszesz")
@app_commands.describe(
    tekst="Tekst, który bot ma powtórzyć",
    razy="Ile razy powtórzyć tekst (max 5)"
)
async def powiedz(interaction: discord.Interaction, tekst: str, razy: int = 1):
    if razy > 5:
        await interaction.response.send_message("❌ Maksymalnie mogę powtórzyć 5 razy!")
        return
    await interaction.response.send_message((tekst + " ") * razy)

# 🔹 Komenda z wyborem opcji
@bot.tree.command(name="kolor", description="Wybierz swój ulubiony kolor")
@app_commands.describe(kolor="Twój ulubiony kolor")
@app_commands.choices(kolor=[
    app_commands.Choice(name="Czerwony ❤️", value="Czerwony"),
    app_commands.Choice(name="Zielony 💚", value="Zielony"),
    app_commands.Choice(name="Niebieski 💙", value="Niebieski")
])
async def kolor(interaction: discord.Interaction, kolor: app_commands.Choice[str]):
    await interaction.response.send_message(f"Wybrałeś kolor: {kolor.name}")

@bot.tree.command(name="pytanie", description="Zadaj pytanie o podręcznik RPG")
@app_commands.describe(tekst="Twoje pytanie dotyczące zasad RPG")
@app_commands.choices(chunks=[
    app_commands.Choice(name="Pięć 5", value=5),
    app_commands.Choice(name="Dziesięć 10", value=10),
    app_commands.Choice(name="Dwadzieścia 20", value=20)
])
async def pytanie(interaction: discord.Interaction, tekst: str, chunks: app_commands.Choice[int]):
    await interaction.response.defer()
    try:
        reply = "Brak odpowiedzi"
        t = 0.0
        reply, srcs, t = answer_query(tekst, k=chunks.value, llm_model="gemini-2.5-flash", temperature=0.2)
        await interaction.followup.send(f"{reply.content} tr: {t}")
    except Exception as e:
        await interaction.followup.send(f"Wystąpił błąd: {e}")

    # await interaction.response.send_message(f"Twoje pytanie: {tekst}")

        # st.session_state.chat.append({"role": "user", "text": user_query.strip(), "sources": []})
        # st.session_state.chat.append({"role": "assistant", "text": reply, "sources": srcs, "time": t})

bot.run(os.environ["HANDBOOK_BOT_KEY"])
