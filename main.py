"""Uygulama giri? noktas?: Instagram DM otomasyonu."""

from channels.instagram.bot import InstagramBot


def main() -> None:
    bot = InstagramBot()
    bot.run()


if __name__ == "__main__":
    main()
