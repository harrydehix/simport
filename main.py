from vibes_song_importer.videotitle import get_song_info_from_title

if __name__ == "__main__":
    titles = ["Queen - Bohemian Rhapsody (Official Video Remastered)", "makko x Miksu/Macloud - \"STREIT\"", "Paula Hartmann - sag was (feat. t-low) (visualizer)"]
    for title in titles:
        song_info = get_song_info_from_title(title)
        if song_info:
            print(f"Interpret: {song_info.interpret}, Song Name: {song_info.song_name}")
        else:
            print("Could not extract song info from the title.")