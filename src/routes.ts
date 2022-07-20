import { API_BASE_URL, FILE_URL } from "./config";
import axios from "axios";
import { FileResponse } from "./types";

export const getFile = async (file_id: string) => {
  return await axios
    .post<FileResponse>(API_BASE_URL + "/getFile", {
      file_id,
    })
    .then((res) => res.data)
    .catch((err) => console.error(err));
};

export const downloadFile = async (file_path: string) => {
  return await axios
    .get<DataView>(FILE_URL + "/" + file_path, {
      responseType: "arraybuffer",
      headers: {
        contentType: "application/octet-stream",
      },
    })
    .then((res) => res.data)
    .catch((err) => console.error(err));
};
