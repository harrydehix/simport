import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

type SongSearchResult =
    | {
          success: true;
          results: {
              /** The ID of the song. */
              id: number;
              /** The name of the artist. */
              artistName: string;
              /** The name of the track. */
              trackName: string;
              /** The duration of the song in seconds. */
              duration: number;
          }[];
      }
    | {
          success: false;
          error: string;
      };

type SongSearchOptions = {
    /** A search query to find the song to import from `lrclib.net`. */
    query?: string;
    /** The artist name to search for. Optional, ignored if `query` is provided. */
    artist?: string;
    /** The track name to search for. Optional, ignored if `query` is provided. */
    title?: string;
};

/**
 * Searches for songs available on `lrclib.net` using either a general search query or specific artist and track name. Returns a list of matching songs with their IDs, artist names, track names and durations. The returned IDs can be used to import the song with the `importSong` function.
 */
export async function searchForSong(
    options: SongSearchOptions,
): Promise<SongSearchResult> {
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

type SongImportOptions = {
    /** The ID of the song to import from `lrclib.net`. If not provided, the `query` option will be used to search for the song. */
    id?: number;
    /** A search query to find the song to import from `lrclib.net`. Ignored if `id` is provided. */
    query?: string;
    /** Path to the audio file to synchronize the lyrics to. */
    file: string;
    /** Path to save the synchronized lyrics to. The output format is determined by the file extension, which can be either .srt, .vtt, .ass or .txt */
    output: string;
    /** The language of the lyrics to import. Optional, default is `en`. */
    lang?: string;
    /** Whether to import the raw line synchronized lyrics without word-level synchronization. */
    raw?: boolean;
};

/**
 * Gets the lyrics of a song, that is available on `lrclib.net` and optionally synchronizes it to the passed audio file. The synchronization
 * result is saved to the specified output file in either .srt, .vtt, .ass or .txt format.
 */
export async function importSong(
    options: SongImportOptions,
): Promise<SongImportResult> {
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
