import { Telegraf } from "telegraf";
import { BOT_TOKEN } from "./config";
import { writeFile } from "node:fs/promises";
import { getFile, downloadFile } from "./routes";
import * as XLSX from "xlsx";

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
});

bot.command("kuvaaja", async (ctx) => {
  const wb = XLSX.readFile("test.xlsx", { cellDates: true });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const data = XLSX.utils.sheet_to_json(ws, {
    header: ["date", "name", "msg", "amount"],
  });
  console.log(data);
  await ctx.reply("insert kuvaaja");
});

export default bot;
