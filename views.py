import math
import discord
import datetime

class ListView(discord.ui.View):
    embed: discord.Embed
    page = 1
    def __init__(self, embed: discord.Embed, context: discord.Interaction, listpos: list, page_len: int = 5):
        self.embed = embed
        self.listpos = listpos
        self.pages = math.ceil(len(listpos) / 5)
        self.page_len = page_len
        super().__init__(timeout=30)
        self.context = context
        if self.pages < 2:
            for child in self.children:
                if isinstance(child, discord.ui.Button) and (child.custom_id == "2" or child.custom_id == "3"):
                    child.disabled = True

    async def on_timeout(self):
        self.clear_items()
        await self.context.edit_original_response(embed=self.embed, view=None)
        return await super().on_timeout()

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏮", custom_id="0", disabled=True)
    async def all_front(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.context.user.id:
            await interaction.response.send_message(content="Only command invoker can use this!", ephemeral=True)
            return
        for child in self.children:
            if isinstance(child, discord.ui.Button) and (child.custom_id == "2" or child.custom_id == "3"):
                child.disabled = False
            if isinstance(child, discord.ui.Button) and (child.custom_id == "0" or child.custom_id == "1"):
                child.disabled = True
        self.page = 1

        offset = 0 + (self.page-1) * self.page_len

        board = ""
        for pos in self.listpos[(0+offset):(5+offset)]:
            board += f'{pos}\n'
        self.embed.description = board
        self.embed.set_footer(text=f"{self.page}/{self.pages}")
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏪", custom_id="1", disabled=True)
    async def one_front(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.context.user.id:
            await interaction.response.send_message(content="Only command invoker can use this!", ephemeral=True)
            return

        self.page -= 1
        for child in self.children:
            if isinstance(child, discord.ui.Button) and (child.custom_id == "2" or child.custom_id == "3"):
                child.disabled = False
            if self.page == 1:
                if isinstance(child, discord.ui.Button) and (child.custom_id == "0" or child.custom_id == "1"):
                    child.disabled = True

        offset = 0 + (self.page-1) * self.page_len

        board = ""
        for pos in self.listpos[(0+offset):(5+offset)]:
            board += f'{pos}\n'
        self.embed.description = board
        self.embed.set_footer(text=f"{self.page}/{self.pages}")
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏹", custom_id="stop")
    async def stopper(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.context.user.id:
            await interaction.response.send_message(content="Only command invoker can use this!", ephemeral=True)
            return
        self.clear_items()
        await interaction.response.edit_message(embed=self.embed, view=None)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏩", custom_id="2")
    async def one_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.context.user.id:
            await interaction.response.send_message(content="Only command invoker can use this!", ephemeral=True)
            return

        self.page += 1

        for child in self.children:
            if self.page == self.pages:
                if isinstance(child, discord.ui.Button) and (child.custom_id == "2" or child.custom_id == "3"):
                    child.disabled = True
            if isinstance(child, discord.ui.Button) and (child.custom_id == "0" or child.custom_id == "1"):
                child.disabled = False

        offset = 0 + (self.page-1) * self.page_len

        board = ""
        for pos in self.listpos[(0+offset):(5+offset)]:
            board += f'{pos}\n'
        self.embed.description = board
        self.embed.set_footer(text=f"{self.page}/{self.pages}")
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏭", custom_id="3")
    async def all_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.context.user.id:
            await interaction.response.send_message(content="Only command invoker can use this!", ephemeral=True)
            return
        if interaction.guild_id is None:
            return
        self.page = self.pages

        for child in self.children:
            if isinstance(child, discord.ui.Button) and (child.custom_id == "2" or child.custom_id == "3"):
                child.disabled = True
            if isinstance(child, discord.ui.Button) and (child.custom_id == "0" or child.custom_id == "1"):
                child.disabled = False

        offset = 0 + (self.page-1) * self.page_len

        board = ""
        for pos in self.listpos[(0+offset):(5+offset)]:
            board += f'{pos}\n'
        self.embed.description = board
        self.embed.set_footer(text=f"{self.page}/{self.pages}")
        await interaction.response.edit_message(embed=self.embed, view=self)
