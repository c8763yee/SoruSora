import asyncio
import datetime

import discord
from discord import ui, app_commands, Interaction

import templates
from commands import Confirm

EMPTY_TEXT = "Empty"

LINK_PLAY_LIFESPAN = datetime.timedelta(minutes=30)


class LinkPlayView(ui.View):

    def __init__(self):
        super().__init__(timeout=False)

    async def on_timeout(self) -> None:
        raise RuntimeError("Buttons are timed out and their interactions will fail")

    @ui.button(label="Join", custom_id="linkview-join-button", style=discord.ButtonStyle.primary)
    async def join(self, interaction: Interaction, button: ui.Button):
        embed = interaction.message.embeds[0]
        user = interaction.user

        if self._is_joined(embed, user):
            await interaction.response.send_message("You've already joined the Link Play", ephemeral=True)
            return

        if self._is_full(embed):
            await interaction.response.send_message("There are no more slots available", ephemeral=True)
            return

        coroutines = [self._alert_others(interaction.guild, embed, user, f"{user.mention} has joined the Link Play!")]

        for i in range(0, len(embed.fields)):
            if embed.fields[i].value == EMPTY_TEXT:
                embed.set_field_at(index=i, name=embed.fields[i].name, value=user.mention)
                coroutines.append(interaction.message.edit(embed=embed))

                coroutines.append(interaction.response.send_message("Joined!", ephemeral=True))
                return

        tasks = [asyncio.ensure_future(coro()) for coro in coroutines]
        await asyncio.wait(tasks)

    def _is_joined(self, embed: discord.Embed, user: discord.User) -> bool:
        for field in embed.fields:
            if field.value == user.mention:
                return True

        return False

    def _is_full(self, embed: discord.Embed) -> bool:
        for field in embed.fields:
            if field.value == EMPTY_TEXT:
                return False

        return True

    async def _alert_others(self, guild: discord.Guild, embed: discord.Embed, interacted_user: discord.User,
                            message: str) -> None:

        for field in embed.fields:
            if field.value in (EMPTY_TEXT, interacted_user.mention):
                continue

            user = guild.get_member(int(field.value.removeprefix("<@").removesuffix(">")))
            await user.send(message)

    @ui.button(label="Leave", custom_id="linkview-leave-button")
    async def leave(self, interaction: Interaction,button: ui.Button):
        embed = interaction.message.embeds[0]
        user = interaction.user

        if not self._is_joined(embed, user):
            await interaction.response.send_message("You haven't joined the Link Play", ephemeral=True)
            return

        for i in range(0, len(embed.fields)):
            if embed.fields[i].value != user.mention:
                continue

            lead_user_mention = embed.fields[0].value
            if user.mention == lead_user_mention:
                confirm_view = Confirm(confirmed_message="Deleted")
                await interaction.response.send_message("You're about to delete the Link Play you created. Do you "
                                                        "want to continue?", view=confirm_view, ephemeral=True)
                await confirm_view.wait()

                if confirm_view.is_confirmed:
                    await interaction.message.delete()
            else:
                await self._alert_others(interaction.guild, embed, user, f"{user.mention} has left the Link Play")

                embed.set_field_at(index=i, name=embed.fields[i].name, value=EMPTY_TEXT)
                await interaction.message.edit(embed=embed)
                await interaction.response.send_message("You've left the Link Play", ephemeral=True)

            return


class Arcaea(app_commands.Group):
    """
    Commands related to Arcaea
    """

    @app_commands.command()
    async def linkplay(self, interaction: Interaction, roomcode: str):
        """
        Create an embed to invite people to your Link Play. It will last for 30 minutes
        """

        user = interaction.user

        embed = discord.Embed(color=templates.color,
                              title="Arcaea Link Play",
                              description=f"{user.mention} is waiting for players to join")

        embed.add_field(name="Lead", value=user.mention)

        num_players = 3
        for i in range(0, num_players):
            embed.add_field(name="Player", value=EMPTY_TEXT)

        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.set_footer(text=f"Room code: {roomcode}")

        embed.set_thumbnail(url="https://user-images.githubusercontent.com/48105703/182501819-502dc5f2-c831-4ce4-8300-78ecc5797b89.png")

        await interaction.response.send_message(embed=embed, view=LinkPlayView())
        message = await interaction.original_message()

        await message.delete(delay=LINK_PLAY_LIFESPAN.total_seconds())
