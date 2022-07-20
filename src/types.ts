export interface FileResponse {
  ok: boolean;
  result: {
    file_id: string;
    file_size: number;
    file_path: string;
  };
}
