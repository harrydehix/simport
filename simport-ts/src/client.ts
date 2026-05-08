import { io, Socket } from "socket.io-client";

const DEFAULT_DAEMON_URL =
    process.env.SIMPORT_DAEMON_URL || "http://127.0.0.1:8000";

export type SongSearchResult =
    | {
          success: true;
          results: {
              id: number;
              artistName: string;
              trackName: string;
              duration: number;
          }[];
      }
    | {
          success: false;
          error: string;
      };

export type SongSearchOptions = {
    query?: string;
    artist?: string;
    title?: string;
    daemonUrl?: string;
};

export async function searchForSong(
    options: SongSearchOptions,
): Promise<SongSearchResult> {
    return new Promise((resolve) => {
        const socket = io(options.daemonUrl || DEFAULT_DAEMON_URL);

        socket.on("connect_error", (err) => {
            socket.disconnect();
            resolve({
                success: false,
                error: "Connection to daemon failed: " + err.message,
            });
        });

        socket.on("search:result", (data) => {
            socket.disconnect();
            resolve(data);
        });

        socket.on("search:error", (data) => {
            socket.disconnect();
            resolve(data);
        });

        socket.emit("search", {
            artist: options.artist,
            title: options.title,
            query: options.query,
        });
    });
}

export type SongImportResult =
    | {
          success: true;
          output: string;
      }
    | {
          success: false;
          error: string;
      };

export type ProgressEvent = {
    step: string;
    message: string;
    percent?: number;
};

export type SongImportOptions = {
    id?: number;
    query?: string;
    file: string;
    output: string;
    lang?: string;
    raw?: boolean;
    offset_fix?: boolean;
    daemonUrl?: string;
    onProgress?: (progress: ProgressEvent) => void;
};

export async function transcribeSong(
    options: SongImportOptions,
): Promise<SongImportResult> {
    return new Promise((resolve) => {
        const socket = io(options.daemonUrl || DEFAULT_DAEMON_URL);

        socket.on("connect_error", (err) => {
            socket.disconnect();
            resolve({
                success: false,
                error: "Connection to daemon failed: " + err.message,
            });
        });

        socket.on("transcribe:progress", (data: ProgressEvent) => {
            if (options.onProgress) {
                options.onProgress(data);
            }
        });

        socket.on("transcribe:result", (data) => {
            socket.disconnect();
            resolve(data);
        });

        socket.on("transcribe:error", (data) => {
            socket.disconnect();
            resolve(data);
        });

        socket.emit("transcribe", {
            id: options.id,
            query: options.query,
            file: options.file,
            output: options.output,
            lang: options.lang,
            raw: options.raw,
            offset_fix: options.offset_fix,
        });
    });
}

export type VibesImportOptions = {
    youtube: string;
    output: string;
    lang?: string;
    infer_lang?: boolean;
    offset_fix?: boolean;
    gemini_api_key?: string;
    raw?: boolean;
    daemonUrl?: string;
    onProgress?: (progress: ProgressEvent) => void;
};

export async function importSongForVibes(
    options: VibesImportOptions,
): Promise<SongImportResult> {
    return new Promise((resolve) => {
        const socket = io(options.daemonUrl || DEFAULT_DAEMON_URL);

        socket.on("connect_error", (err) => {
            socket.disconnect();
            resolve({
                success: false,
                error: "Connection to daemon failed: " + err.message,
            });
        });

        socket.on("vimport:progress", (data: ProgressEvent) => {
            if (options.onProgress) {
                options.onProgress(data);
            }
        });

        socket.on("vimport:result", (data) => {
            socket.disconnect();
            resolve(data);
        });

        socket.on("vimport:error", (data) => {
            socket.disconnect();
            resolve(data);
        });

        socket.emit("vimport", {
            youtube: options.youtube,
            output: options.output,
            lang: options.lang,
            infer_lang: options.infer_lang,
            offset_fix: options.offset_fix,
            gemini_api_key: options.gemini_api_key,
            raw: options.raw,
        });
    });
}
