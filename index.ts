import { Telegraf } from "telegraf";
import { BOT_TOKEN } from "./src/config";

if (!BOT_TOKEN) {
  console.error("BOT_TOKEN is not set, quitting...");
  process.exit(1);
}

const bot = new Telegraf(BOT_TOKEN);

bot.start((ctx) => ctx.reply("Welcome!"));

bot.launch();

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
