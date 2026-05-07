import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

type SongSearchResult =
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

export async function searchForSong(options: {
    query?: string;
    artist?: string;
    title?: string;
}): Promise<SongSearchResult> {
    try {
        const args = ["search", "--json"];
        if (options.query) args.push("--query", options.query);
        if (options.artist) args.push("--artist", options.artist);
        if (options.title) args.push("--title", options.title);

        const { stdout } = await execFileAsync("simport", args);
        return JSON.parse(stdout.trim());
    } catch (error: any) {
        return {
            success: false,
            error:
                error.stderr?.trim() ||
                error.message ||
                "Failed to search for song",
        };
    }
}

type SongImportResult =
    | {
          success: true;
      }
    | {
          success: false;
          error: string;
      };

export async function importSong(options: {
    id?: number;
    query?: string;
    file: string;
    output: string;
    lang?: string;
    raw?: boolean;
}): Promise<SongImportResult> {
    try {
        const args = [
            "import",
            "--file",
            options.file,
            "--output",
            options.output,
            "--json",
        ];

        if (options.lang) args.push("--lang", options.lang);

        if (options.id !== undefined) {
            args.push("--id", options.id.toString());
        } else if (options.query) {
            args.push("--query", options.query);
        } else {
            return {
                success: false,
                error: "Either id or query must be provided",
            };
        }

        if (options.raw) args.push("--raw");

        const { stdout } = await execFileAsync("simport", args);

        return JSON.parse(stdout.trim());
    } catch (error: any) {
        return {
            success: false,
            error:
                error.stderr?.trim() ||
                error.message ||
                "Failed to import song",
        };
    }
}
