"""Clears all app commands of the bot."""

import os
import sys

import discord
from discord.ext.commands import Bot
from dotenv import load_dotenv


class TempBot(Bot):
    """Temporary bot to clear all commands."""

    async def setup_hook(self) -> None:
        """Set up the test bot."""
        if os.getenv("TEST_GUILD_ID"):
            guild = discord.Object(id=os.getenv("TEST_GUILD_ID"))
            self.tree.clear_commands(guild=guild)
            assert len(await self.tree.sync(guild=guild)) == 0  # noqa: S101


        self.tree.clear_commands(guild=None)
        assert len(await self.tree.sync()) == 0  # noqa: S101

        sys.exit(0)


if __name__ == "__main__":
    assert load_dotenv()  # noqa: S101

    bot = TempBot(command_prefix="!", intents=discord.Intents.all())
    bot.run(os.getenv("BOT_TOKEN"))
