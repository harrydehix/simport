import {
    ensureSimportInstalled,
    importSong,
    searchForSong,
} from "./dist/index.js";

await ensureSimportInstalled("./appdata", true);

console.log(await searchForSong({ query: "Bohemian Rhapsody" }));
console.log(
    await importSong({
        query: "Bohemian Rhapsody",
        file: "path/to/audio.mp3",
        output: "output.ass",
    }),
);
