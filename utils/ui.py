"""
Provides list of ui elements

classes:
    Confirm
    LanguageSelect
"""
import os
from typing import Union, Optional, Type, Coroutine, Any

import discord
from discord import SelectOption, Interaction, Locale
from discord.app_commands import Command, Group

from utils.constants import languages
from utils.templates import info, success
from utils.translator import Localization, Language, DEFAULT_LANGUAGE


class Confirm(discord.ui.View):
    """
    Buttons for confirmation
    """

    def __init__(self, confirmed_message: str, cancelled_message: str, locale: Locale):
        """
        View to get a confirmation from a user. When the confirm button is pressed, set the is_confirmed to `True` and
        stop the View from listening to more input
        :param confirmed_message: A message to send when the user confirmed
        :param cancelled_message: A message to send when the user cancelled
        """
        super().__init__()

        self._loc = Localization(locale, [os.path.join("utils", "ui.ftl")])

        self._confirmed_message = success(confirmed_message)
        self._cancelled_message = info(cancelled_message)

        self.confirm.label = self._loc.format_value("confirm")
        self.cancel.label = self._loc.format_value("cancel")

        self.is_confirmed = None
        """
        None: The user didn't respond\n
        True: The user confirmed\n
        False: The user cancelled
        """

    @discord.ui.button(style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        """
        Confirm when pressed
        """
        self.is_confirmed = True
        await interaction.response.send_message(self._confirmed_message, ephemeral=True)
        self.stop()
        self.clear_items()

    @discord.ui.button(style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        """
        Cancel when pressed
        """
        self.is_confirmed = False
        await interaction.response.send_message(self._cancelled_message, ephemeral=True)
        self.stop()
        self.clear_items()


class LanguageSelect(discord.ui.Select):
    """
    Select UI to select available languages for a user
    """

    def __init__(self, placeholder: Coroutine[Any, Any, str], locale: Locale, max_values: int = None, **kwargs):
        self._placeholder = placeholder
        self._locale = locale
        self._max_values = max_values
        self._kwargs = kwargs

        super().__init__(placeholder="Not initialized. Call init() method first")

    async def init(self):
        """
        Initialize this select
        """

        loc = Localization(self._locale)

        options = [SelectOption(label=await loc.format_value_or_translate(code), value=code) for code in languages]
        super().__init__(placeholder=await self._placeholder, max_values=len(options),
                         options=sorted(options, key=lambda option: option.label.lower()),
                         **self._kwargs)

        return self

    async def callback(self, interaction: Interaction):
        raise NotImplementedError("This method should be overridden in a subclass")


class CommandSelect(discord.ui.Select):
    """
    Select UI to select a command
    """

    def __init__(self, interaction: Interaction, hidden: Optional[set[Type[Union[Command, Group]]]] = None,
                 placeholder: Coroutine[Any, Any, str] = None, **kwargs):
        self._interaction = interaction
        self._hidden = hidden
        self._placeholder = placeholder
        self._kwargs = kwargs
        super().__init__(placeholder="Not initialized. Call init() method first")

    async def init(self) -> "CommandSelect":
        """
        Initialize this select
        """

        super().__init__(placeholder=await self._placeholder if self._placeholder else None,
                         options=await self._get_options(self._interaction, self._hidden), **self._kwargs)
        return self

    @staticmethod
    async def _get_options(interaction: Interaction, hidden: Optional[set[Type[Union[Command, Group]]]] = None) \
            -> list[SelectOption]:
        from main import bot  # pylint: disable=import-outside-toplevel

        language = Language(str(interaction.locale))

        if language == DEFAULT_LANGUAGE:
            options = [SelectOption(label=command.qualified_name) for command in bot.tree.walk_commands()
                       if command not in hidden]
        else:
            options = []
            localize = Localization.has(language.code)

            for command in bot.tree.walk_commands():
                if not isinstance(command, Command) or command.root_parent.__class__ in hidden:
                    continue

                if language == DEFAULT_LANGUAGE:
                    options.append(SelectOption(label=command.qualified_name))
                    continue

                translated_name = command.qualified_name.split(" ")
                root_name = translated_name[0]
                for i, name in enumerate(translated_name):
                    if localize:
                        loc = Localization(language, [os.path.join("commands", f"{root_name}.ftl")])
                        translated_name[i] = loc.format_value(f"{name.lower().replace('_', '-')}-name")
                    else:
                        translated_name[i] = await interaction.translate(name)

                options.append(SelectOption(label=" ".join(translated_name), value=command.qualified_name))

        return options

    async def callback(self, interaction: Interaction):
        raise NotImplementedError("This method should be overridden in a subclass")
