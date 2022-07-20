import bot from "./src/bot";

bot.launch().catch((err) => console.error(err));

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
