import { Telegraf } from "telegraf";
import { BOT_TOKEN, API_BASE_URL, FILE_URL } from "./src/config";
import axios from "axios";
import { writeFile, unlink } from "node:fs/promises";

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

  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const fileInfo = await axios
    .post(API_BASE_URL + "/getFile", {
      file_id: doc.file_id,
    })
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return
    .then((res) => res.data)
    .catch((err) => console.error(err));

  console.log(fileInfo.result.file_path);

  const file = await axios.get(FILE_URL + "/" + fileInfo.result.file_path, {
    responseType: "arraybuffer",
    headers: {
      contentType: "application/octet-stream",
    },
  });

  console.log("file", file);

  // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
  await writeFile("test.xlsx", file.data);

  console.log("File saved!");

  await ctx.reply("Excel-filu");

  // eslint-disable-next-line @typescript-eslint/no-misused-promises
  setTimeout(async () => {
    console.log("Deleting file...");
    await unlink("test.xlsx");
    console.log("File deleted!");
  }, 5000);
});

bot.command("kuvaaja", async (ctx) => {
  await ctx.reply("insert kuvaaja");
});

void bot.launch();

process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
