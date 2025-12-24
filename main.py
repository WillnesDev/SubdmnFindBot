import logging
import requests
import telebot
import io

# ================= CONFIG =================

BOT_TOKEN = "8502713384:AAH8-X6rwv_fo5jldQyHelalAkoNub1zQO4"
ADMIN_CONTACT = "t.me/yunusbeckk"

# =========================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)


# ================= SUBDOMAIN FINDER =================

class SubdomainFinder:
    """Reliable subdomain enumeration with fallback"""

    @staticmethod
    def search_subdomains(domain):
        try:
            return SubdomainFinder._from_crtsh(domain)
        except Exception as e:
            logger.warning(f"crt.sh failed: {e}")
            return SubdomainFinder._from_hackertarget(domain)

    @staticmethod
    def _from_crtsh(domain):
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        response = requests.get(
            url,
            timeout=(10, 60),
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        data = response.json()
        subdomains = set()

        for entry in data:
            for sub in entry.get("name_value", "").split("\n"):
                sub = sub.strip().lower()
                if sub.endswith(domain):
                    subdomains.add(sub)

        if not subdomains:
            raise Exception("No result from crt.sh")

        return sorted(subdomains)

    @staticmethod
    def _from_hackertarget(domain):
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        subdomains = set()
        for line in response.text.splitlines():
            if "," in line:
                sub = line.split(",")[0].strip().lower()
                if sub.endswith(domain):
                    subdomains.add(sub)

        if not subdomains:
            raise Exception("No result from hackertarget")

        return sorted(subdomains)


# ================= BOT COMMANDS =================

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "🔍 *Subdomain Finder Bot*\n\n"
        "Send me a domain name:\n"
        "`example.com`\n\n"
        "• ≤20 results → message\n"
        "• >20 results → TXT file\n\n"
        "/help | /contact",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(
        message,
        "🆘 *Help*\n\n"
        "1️⃣ Send domain (google.com)\n"
        "2️⃣ Wait for results\n\n"
        "❗ No http / https",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["contact"])
def contact_cmd(message):
    bot.reply_to(
        message,
        f"📞 *Admin*\n{ADMIN_CONTACT}",
        parse_mode="Markdown"
    )


# ================= DOMAIN HANDLER =================

@bot.message_handler(func=lambda message: True)
def handle_domain(message):
    domain = message.text.strip().lower()

    if " " in domain or "." not in domain:
        bot.reply_to(
            message,
            "❌ Send valid domain:\n`example.com`",
            parse_mode="Markdown"
        )
        return

    domain = domain.replace("http://", "").replace("https://", "")
    domain = domain.replace("www.", "").split("/")[0]

    status_msg = bot.send_message(
        message.chat.id,
        f"🔎 Searching subdomains for *{domain}*...",
        parse_mode="Markdown"
    )

    try:
        subdomains = SubdomainFinder.search_subdomains(domain)

        count = len(subdomains)

        if count <= 20:
            result = "\n".join(f"• `{s}`" for s in subdomains)
            bot.edit_message_text(
                f"✅ *Found {count} subdomains:*\n\n{result}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode="Markdown"
            )
        else:
            text = (
                f"Subdomains for {domain}\n"
                f"Total: {count}\n"
                + "=" * 30 + "\n"
                + "\n".join(subdomains)
            )
            file = io.BytesIO(text.encode("utf-8"))
            file.name = f"{domain}_subdomains.txt"

            bot.send_document(
                message.chat.id,
                file,
                caption=f"✅ Found {count} subdomains"
            )
            bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception:
        bot.edit_message_text(
            "⚠️ *Error*\nServer vaqtincha javob bermayapti.\n"
            "🔁 Keyinroq urinib ko‘ring.",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )


# ================= RUN =================

if __name__ == "__main__":
    print("🤖 Bot running...")
    bot.infinity_polling()
