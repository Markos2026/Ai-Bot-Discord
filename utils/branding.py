import discord

BRAND = {
    "bot_name": "AI Discord Bot",
    "powered_by": "يعمل بالذكاء الاصطناعي (OpenRouter)",
    "developer": "ELMINYAWE",
    "developer_discord": ".y31",
    "logo_url": "https://raw.githubusercontent.com/ELMINYAWE/assets/main/logo.png",
    "contact": "Discord: .y31",
    "rights": "© جميع الحقوق محفوظة للمطور ELMINYAWE"
}

def apply_branding(embed: discord.Embed) -> discord.Embed:
    try:
        if BRAND.get("logo_url"):
            embed.set_thumbnail(url=BRAND["logo_url"])
        footer_text = f"{BRAND['bot_name']} • {BRAND['rights']} • {BRAND['developer']} ({BRAND['developer_discord']})"
        embed.set_footer(text=footer_text)
    except Exception:
        pass
    return embed

