import { config } from "dotenv";

config();

export const BOT_TOKEN = process.env.BOT_TOKEN;
export const API_BASE_URL = "https://api.telegram.org/bot" + BOT_TOKEN;
export const FILE_URL = "https://api.telegram.org/file/bot" + BOT_TOKEN;
