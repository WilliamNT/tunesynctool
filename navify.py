from typing import Optional, Self, List
from enum import Enum
from os import environ as env
from difflib import SequenceMatcher

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm
from dotenv import load_dotenv
from libsonic import connection
import musicbrainzngs
from thefuzz import fuzz

load_dotenv()

spotify_client_id = env.get('SPOTIFY_CLIENT_ID')
spotify_client_secret = env.get('SPOTIFY_CLIENT_SECRET')
spotify_redirect_uri = env.get('SPOTIFY_REDIRECT_URI')
subsonic_base_url = env.get('SUBSONIC_BASE_URL')
subsonic_port = env.get('SUBSONIC_PORT')
subsonic_username = env.get('SUBSONIC_USERNAME')
subsonic_password = env.get('SUBSONIC_PASSWORD')
spotify_scope = "user-library-read,playlist-read-private,playlist-read-collaborative"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

class Service(Enum):
    SPOTIFY = 1
    SUBSONIC = 2

class Song:
    def __init__(
        self,
        service: Service,
        service_id: str,
        title: str,
        album_name: Optional[str],
        primary_artist: Optional[str],
        duration: int,
        track_number: Optional[int],
        cover_url: Optional[str] = None,
        isrc: Optional[str] = None,
        musicbrainz_id: Optional[str] = None,
        additional_artists: Optional[List[str]] = None,
        year: Optional[int] = None,
    ):
        self.service = service
        self.service_id = service_id
        self.title = title
        self.album_name = album_name
        self.primary_artist = primary_artist
        self.duration = duration
        self.cover_url = cover_url
        self.other_service_id = Service.SPOTIFY if service == Service.SUBSONIC else Service.SUBSONIC
        self.isrc = isrc
        self.musicbrainz_id = musicbrainz_id
        self.track_number = track_number
        self.additional_artists = additional_artists if additional_artists is not None else []
        self.year = year

    def __str__(self) -> str:
        return f'#{self.service_id} - {self.title} by {self.primary_artist}'
    
    def __repr__(self) -> str:
        return self.__str__()
    
class Playlist:
    def __init__(self, service: Service, service_id: str, title: str, cover_url: Optional[str], songs: List[Song], description: Optional[str]):
        self.service = service
        self.service_id = service_id
        self.title = title
        self.songs = songs
        self.cover_url = cover_url
        self.other_service_id = other_service_id = Service.SPOTIFY if service == Service.SUBSONIC else Service.SUBSONIC
        self.description = description

    def __str__(self) -> str:
        return f'#{self.service_id} - {self.title} ({len(self.songs)} songs)'
    
    def __repr__(self) -> str:
        return self.__str__()

auth_manager = SpotifyOAuth(
    scope=spotify_scope,
    client_id=spotify_client_id,
    client_secret=spotify_client_secret,
    redirect_uri=spotify_redirect_uri
)
spotify = spotipy.Spotify(auth_manager=auth_manager)
subsonic = connection.Connection(
    baseUrl=subsonic_base_url,
    port=subsonic_port,
    username=subsonic_username,
    password=subsonic_password
)
musicbrainzngs.set_useragent("Navify-Song-Sync-Tool", "0.1", "https://github.com/WilliamNT")

def get_spotify_playlists(limit: int = 50, whitelist_ids: List[str] = []) -> List[Playlist]:
    spotify_playlists = spotify.current_user_playlists(limit)
    mapped_playlists = []

    for playlist in tqdm(spotify_playlists['items'], desc='Fetching Spotify Playlists', colour='blue'):
        playlist_Id = playlist['id']
        if not playlist_Id in whitelist_ids:
            tqdm.write(f'{YELLOW}Ignoring playlist "{playlist["name"]}" as it is not whitelisted.{RESET}')
            continue

        playlist_title = playlist['name']
        playlist_description = playlist['description']

        if playlist['images'] and len(playlist['images']) > 0:
            playlist_cover_url = playlist['images'][0]['url']
        else:
            playlist_cover_url = None

        playlist_songs = spotify.playlist_tracks(playlist_Id)
        songs = []

        for song in playlist_songs['items']:
            song_id = song['track']['id']
            song_title = song['track']['name']
            song_album = song['track']['album']['name']
            song_artist = song['track']['artists'][0]['name']
            song_cover_url = song['track']['album']['images'][0]['url']
            isrc = song['track']['external_ids'].get('isrc', None)
            track_number = song['track']['track_number']
            additional_artists = [artist['name'] for artist in song['track']['artists'][1:]]
            duration = int(song['track']['duration_ms']) / 1000 if song['track']['duration_ms'] else None
            year = int(song['track']['album']['release_date'][:4]) if song['track']['album']['release_date'] else None 

            songs.append(Song(
                service=Service.SPOTIFY,
                service_id=song_id,
                title=song_title,
                album_name=song_album,
                primary_artist=song_artist,
                cover_url=song_cover_url,
                isrc=isrc,
                track_number=int(track_number) if track_number else None,
                additional_artists=additional_artists,
                duration=duration,
                year=year
            ))

        mapped_playlists.append(Playlist(
            service=Service.SPOTIFY,
            service_id=playlist_Id,
            title=playlist_title,
            cover_url=playlist_cover_url,
            songs=songs,
            description=playlist_description
        ))

    return mapped_playlists

def get_subsonic_playlists() -> List[Playlist]:
    subsonic_playlists = subsonic.getPlaylists()
    mapped_playlists = []
    
    # If there are no playlists, return an empty list
    if not 'playlist' in subsonic_playlists['playlists']:
        return []

    subsonic_playlists = subsonic_playlists['playlists']['playlist'] if isinstance(subsonic_playlists, dict) else subsonic_playlists

    for playlist in tqdm(subsonic_playlists, desc='Fetching Subsonic Playlists', colour='blue'):
        playlist = subsonic.getPlaylist(playlist['id'])['playlist']
        playlist_id = playlist['id']
        playlist_title = playlist['name']
        playlist_description = playlist.get('comment', None)
        playlist_cover_url = None
        playlist_songs = subsonic.getPlaylist(playlist_id)
        songs = []

        if 'entry' in playlist_songs['playlist']:
            for song in playlist_songs['playlist']['entry']:
                song_id = song['id']
                song_title = song['title']
                song_album = song['album']
                song_artist = song['artist']
                song_duration = song['duration']
                song_cover_url = subsonic.getCoverArt(song_id, size=300)
                song_muscbrainz_id = song['musicBrainzId']
                track_number = song['track']
                year = song['year']
                songs.append(Song(
                    service=Service.SUBSONIC,
                    service_id=song_id,
                    title=song_title,
                    album_name=song_album,
                    primary_artist=song_artist,
                    duration=song_duration,
                    cover_url=song_cover_url,
                    isrc=None,
                    musicbrainz_id=song_muscbrainz_id,
                    track_number=int(track_number) if track_number else None,
                    year=int(year) if year else None,
                ))

        mapped_playlists.append(Playlist(
            service=Service.SUBSONIC,
            service_id=playlist_id,
            title=playlist_title,
            cover_url=playlist_cover_url,
            songs=songs,
            description=playlist_description
        ))

    return mapped_playlists    

def get_musicbrainz_id_from_isrc(isrc: str) -> Optional[str]:
    try:
        result = musicbrainzngs.search_recordings(isrc=isrc)
        return result['recording-list'][0]['id']
    except:
        return None

def get_musicbrainz_id_from_complex_query(song: Song) -> Optional[str]:
    try:
        result = musicbrainzngs.search_recordings(
            query=f'{clean_str(song.primary_artist)} {clean_str(song.title)}',
            artist=song.primary_artist,
            date=song.year,
            track=song.title,
            isrc=song.isrc
        )
        return result['recording-list'][0]['id']
    except:
        return None

def search_subsonic_for_match(query: str) -> Optional[Song]:
    result = subsonic.search2(query=query, artistCount=0, albumCount=0, songCount=1)

    if 'song' in result['searchResult2']:
        song = result['searchResult2']['song'][0]
        song_id = song['id']
        song_title = song['title']
        song_album = song['album']
        song_artist = song['artist']
        song_duration = song['duration']
        song_cover_url = subsonic.getCoverArt(song_id, size=300)
        song_muscbrainz_id = song['musicBrainzId']
        track_number = song['track']
        year = song['year']
        return Song(
            service=Service.SUBSONIC,
            service_id=song_id,
            title=song_title,
            album_name=song_album,
            primary_artist=song_artist,
            duration=song_duration,
            cover_url=song_cover_url,
            isrc=None,
            musicbrainz_id=song_muscbrainz_id,
            track_number=int(track_number) if track_number else None,
            year=int(year) if year else None,
        )
    else:
        return None

def get_subsonic_songs_for_artist(query: str) -> List[Song]:
    result = subsonic.search2(query=query, artistCount=10, albumCount=0, songCount=0)
    songs = []

    if 'artist' in result['searchResult2']:
        artist = result['searchResult2']['artist'][0]
        artist_id = artist['id']
        artist_name = artist['name']
        artist_albums = subsonic.getArtist(artist_id)['artist']['album']

        for album in artist_albums:
            album_id = album['id']
            album_name = album['name']
            album_songs = subsonic.getAlbum(album_id)['album']['song']

            for song in album_songs:
                song_id = song['id']
                song_title = song['title']
                song_album = song['album']
                song_artist = song['artist']
                song_duration = song['duration']
                song_cover_url = subsonic.getCoverArt(song_id, size=300)
                song_muscbrainz_id = song['musicBrainzId']
                track_number = song['track']
                year = song['year']
                songs.append(Song(
                    service=Service.SUBSONIC,
                    service_id=song_id,
                    title=song_title,
                    album_name=song_album,
                    primary_artist=song_artist,
                    duration=song_duration,
                    cover_url=song_cover_url,
                    isrc=None,
                    musicbrainz_id=song_muscbrainz_id,
                    track_number=int(track_number) if track_number else None,
                    year=int(year) if year else None,
                ))

    return songs

def clean_str(s: str) -> str:
    if not s:
        return ''
        
    substitutions = {
        'feat.': '', 'feat': '', 'ft.': '', 'ft': '',
        'featuring': '', 'with': '', 'prod.': '', 'prod': '',
        '&': 'and', '+': 'and',
        '[': '', ']': '', '(': '', ')': '', 
        "'": '', '"': '', '!': '', '?': '',
        '/': ' ', '\\': ' ', '_': ' ', '-': ' ',
        '.': '', ',': '', ';': '', ':': ''
    }
    
    s = s.lower()
    for old, new in substitutions.items():
        s = s.replace(old, new)
    
    return ' '.join(s.split())

def calculate_int_similarity(a: int, b: int) -> float:
    if (a == 0 or b == 0) or (a is None or b is None):
        return float(0)
    return round(1 - abs(a - b) / max(a, b), 1)

def calculate_similarity(a: Song, b: Song) -> float:
    title_similarity = SequenceMatcher(None, clean_str(a.title), clean_str(b.title)).ratio()
    artist_similarity = SequenceMatcher(None, clean_str(a.primary_artist), clean_str(b.primary_artist)).ratio()
    album_similarity = SequenceMatcher(None, (clean_str(a.album_name)), clean_str(b.album_name)).ratio()
    
    duration_similarity = 0 if a.duration is None or b.duration is None else 1 if a.duration == b.duration else 0
    track_number_similarity = 0 if a.track_number is None or b.track_number is None else 1 if a.track_number == b.track_number else 0
    year_similarity = 0 if a.year is None or b.year is None else 1 if a.year == b.year else 0

    return round((
        title_similarity +
        artist_similarity +
        album_similarity +
        duration_similarity +
        track_number_similarity +
        year_similarity
    ) / 6, 1)

def is_similar_enough(a: Song, b: Song) -> bool:
    TRESHOLD = 0.6
    return calculate_similarity(a, b) >= TRESHOLD

def calculate_fuzzy_ratio(a: str, b: str) -> float:
    return fuzz.ratio(clean_str(a), clean_str(b)) / 100

def match_spotify_song_to_subsonic(song: Song) -> Optional[Song]:
    # Strategy 1: ISRC + MusicBrainz
    musicbrainz_id = get_musicbrainz_id_from_isrc(song.isrc)
    if musicbrainz_id:
        result = search_subsonic_for_match(musicbrainz_id)
        if result:
            return result

    # Strategy 2: Direct artist + title search
    result = search_subsonic_for_match(f'{clean_str(song.primary_artist)} {clean_str(song.title)}')
    if result and is_similar_enough(song, result):
        return result
    
    # Strategy 3: Search by title only and verify artist separately
    result = search_subsonic_for_match(clean_str(song.title))
    if result and calculate_fuzzy_ratio(song.primary_artist, result.primary_artist) >= 0.6:
        return result

    # Strategy 4: Search by artist only and verify title separately
    result = search_subsonic_for_match(clean_str(song.primary_artist))
    if result and calculate_fuzzy_ratio(song.title, result.title) >= 0.6:
        return result
        
    # Strategy 5: Search for all songs by the artist and verify title separately
    artists = song.additional_artists + [song.primary_artist]
    for artist in artists:
        songs = get_subsonic_songs_for_artist(artist)
        for subsonic_song in songs:
            if calculate_fuzzy_ratio(song.title, subsonic_song.title) >= 0.6:
                match_spotify_song_to_subsonic(subsonic_song)

    return None

def mirror_spotify_playlist(spotify_playlist: Playlist, preview_only: bool = False) -> None:
    new_playlist = Playlist(
        service=Service.SUBSONIC,
        service_id=None,
        title=spotify_playlist.title,
        cover_url=spotify_playlist.cover_url,
        songs=[],
        description=spotify_playlist.description
    )
    
    if not preview_only:
        new_playlist_id = subsonic.createPlaylist(name=new_playlist.title)['playlist']['id']
        subsonic.updatePlaylist(
            lid=new_playlist_id,
            comment=new_playlist.description,
        )

    for song in tqdm(spotify_playlist.songs, desc=f'Mirroring playlist "{spotify_playlist.title}" to Subsonic', colour='blue'):
        subsonic_song = None
        if song.isrc:
            musicbrainz_id = get_musicbrainz_id_from_isrc(song.isrc)
            
            if musicbrainz_id:
                subsonic_song = search_subsonic_for_match(musicbrainz_id)

        if not subsonic_song:
            subsonic_song = match_spotify_song_to_subsonic(song)

        if not subsonic_song:
            tqdm.write(f'{YELLOW}Failed to match [SUBSONIC] {song.primary_artist} - {song.title} (Song isn\'t present in your Subsonic library){RESET}')
            continue

        new_playlist.songs.append(subsonic_song)
        tqdm.write(f'{GREEN}Successfully matched [SPOTIFY] {song.primary_artist} - {song.title} -->> [YOUR SUBSONIC LIBRARY] {subsonic_song.primary_artist} - {subsonic_song.title}{RESET}')

    if not preview_only:
        subsonic.updatePlaylist(
            lid=new_playlist_id,
            songIdsToAdd=[song.service_id for song in new_playlist.songs]
        )

print('Navify - Spotify to Subsonic Playlist Sync Tool')
print('-----------------------------------------------\n')

# 1. Fetching your Spotify playlists
print('Fetching your Spotify playlists...')
whitelist_ids = []
spotify_playlists = get_spotify_playlists(50, whitelist_ids)

print('Found the following playlists:')
for i, playlist in enumerate(spotify_playlists):
    print(f'\t{i + 1}. {playlist}')

print('\n')

# 2. Mirroring Spotify playlists to Subsonic
print('Mirroring Spotify playlists to Subsonic...')
print('If you have a large library, this may take a while. Please note that 100% accuracy is not guaranteed.\n')
for playlist in spotify_playlists:
    mirror_spotify_playlist(
        spotify_playlist=playlist,
        preview_only=False
    )

print('\nDone! If you faced any issues, or aren\'t satisfied with the results, please open an issue in the GitHub repository.')