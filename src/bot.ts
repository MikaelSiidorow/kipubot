import { Telegraf } from "telegraf";
import { BOT_TOKEN } from "./config";
import { writeFile, unlink } from "node:fs/promises";
import { getFile, downloadFile } from "./routes";

if (!BOT_TOKEN) {
  console.error("BOT_TOKEN is not set, quitting...");
  process.exit(1);
}

const bot = new Telegraf(BOT_TOKEN);

bot.start((ctx) => ctx.reply("Welcome!"));

bot.on("document", async (ctx) => {
  const doc = ctx.message.document;
  const excel_mime_type =
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

  if (doc.mime_type !== excel_mime_type) {
    await ctx.reply("Virhe: Lähetä Excel-tiedosto!");
    return;
  }

  const fileInfo = await getFile(doc.file_id);

  if (!fileInfo) {
    await ctx.reply("Virhe: Tiedostoa ei saatu noudettua!");
    return;
  }

  const file = await downloadFile(fileInfo.result.file_path);

  if (!file) {
    await ctx.reply("Virhe: Tiedostoa ei saatu ladattua!");
    return;
  }

  await writeFile("test.xlsx", file);

  console.log("File saved!");

  await ctx.reply("Excel-filu");

  console.log("Deleting file...");

  setTimeout(() => {
    unlink("test.xlsx")
      .then(() => console.log("File deleted!"))
      .catch((err) => console.error(err));
  }, 5000);
});

bot.command("kuvaaja", async (ctx) => {
  await ctx.reply("insert kuvaaja");
});

export default bot;
