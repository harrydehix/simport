# API Documentation

Welcome to the beta API documentation and specification of the LRCLIB's API! Although we intend to maintain backward compatibility, please be aware that there may be breaking changes in future updates. Since this document is still in its early stages, it may lack information or contain inaccuracies in certain sections.

This API has no rate limiting in place and is openly accessible to all users and applications. There is no need for an API key or any kind of registering!

While this is not mandatory, if you are developing an application to interact with LRCLIB, we encourage you to include the User-Agent header in your requests, specifying your application's name, version, and a link to its homepage or project page. For example: LRCGET v0.2.0 (https://github.com/tranxuanthang/lrcget).

## `GET/api/get` - Get lyrics with a track's signature

Attempt to find the best match of lyrics for the track. You must provide the exact signature of the track, including the track title, artist name, album name, and the track's duration in seconds.

Each time you request a new track's signature, this API will attempt to access external sources in case the lyrics are not found in the internal database. Therefore, the response time will vary significantly. If you prefer to avoid this behavior, please use the /api/get-cached API instead.

_Note: The provided duration is crucial. LRCLIB will attempt to provide the lyrics only when the duration matches the record in LRCLIB's database, or at least with a difference of ±2 seconds in duration._

### Query parameters

<table>
  <tr>
    <th>Field</th>
    <th>Required</th>
    <th>Type</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>track_name</td>
    <td>true</td>
    <td>string</td>
    <td>Title of the track</td>
  </tr>
  <tr>
    <td>artist_name</td>
    <td>true</td>
    <td>string</td>
    <td>Name of the artist</td>
  </tr>
  <tr>
    <td>album_name</td>
    <td>true</td>
    <td>string</td>
    <td>Name of the album</td>
  </tr>
  <tr>
    <td>duration</td>
    <td>true</td>
    <td>number</td>
    <td>Track's duration in seconds</td>
  </tr>
</table>

### Example request

```
GET /api/get?artist_name=Borislav+Slavov&track_name=I+Want+to+Live&album_name=Baldur%27s+Gate+3+(Original+Game+Soundtrack)&duration=233
```

### Example response

**200 OK:**

```
{
    "id": 3396226,
    "trackName": "I Want to Live",
    "artistName": "Borislav Slavov",
    "albumName": "Baldur's Gate 3 (Original Game Soundtrack)",
    "duration": 233,
    "instrumental": false,
    "plainLyrics": "I feel your breath upon my neck\n...The clock won't stop and this is what we get\n",
    "syncedLyrics": "[00:17.12] I feel your breath upon my neck\n...[03:20.31] The clock won't stop and this is what we get\n[03:25.72]"
}
```

**404 Not Found:**

```
{
"code": 404,
"name": "TrackNotFound",
"message": "Failed to find specified track"
}
```

## `GET /api/get-cached` Get lyrics with a track's signature (cached)

This API is similar to /api/get, except that it will only look for lyrics from internal database, and will NOT attempt to access external sources.

### Query parameters

<table>
    <tr>
        <th>Field</th>
        <th>Required</th>
        <th>Type</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>track_name</td>
        <td>true</td>
        <td>string</td>
        <td>Title of the track</td>
    </tr>
    <tr>
        <td>artist_name</td>
        <td>true</td>
        <td>string</td>
        <td>Name of the artist</td>
    </tr>
    <tr>
        <td>album_name</td>
        <td>true</td>
        <td>string</td>
        <td>Name of the album</td>
    </tr>
    <tr>
        <td>duration</td>
        <td>true</td>
        <td>number</td>
        <td>Track's duration in seconds</td>
    </tr>
</table>

### Example request

```
GET /api/get-cached?artist_name=Jeremy+Soule&track_name=Dragonborn&album_name=The+Elder+Scrolls+V:+Skyrim:+Original+Game+Soundtrack&duration=236
```

### Example response

Please see the /api/get's example response.

## `GET /api/get/{id}` Get lyrics by LRCLIB's ID

Get a lyrics record by an absolute ID. ID of a lyrics record can be retrieved from other APIs, such as /api/search API.

<table>
    <tr>
        <th>Field</th>
        <th>Required</th>
        <th>Type</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>id</td>
        <td>true</td>
        <td>number</td>
        <td>ID of the lyrics record</td>
    </tr>
</table>

### Example request

```
GET /api/get/3396226
```

### Example response

Please see the /api/get's example response.

## `GET /api/search` Search for lyrics records

Search for lyrics records using keywords. This API returns an array of lyrics records that match the specified search condition(s).

At least ONE of the two parameters, q OR track_name, must be present.

_Note: This API currently returns a maximum of 20 results and does not support pagination. These limitations are subject to change in the future._

### Query parameters

<table>
    <tr>
        <th>Field</th>
        <th>Required</th>
        <th>Type</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>q</td>
        <td>conditional</td>
        <td>string</td>
        <td>Search for keyword present in ANY fields (track's title, artist name or album name)</td>
    </tr>
    <tr>
        <td>track_name</td>
        <td>conditional</td>
        <td>string</td>
        <td>Search for keyword in track's title</td>
    </tr>
    <tr>
        <td>artist_name</td>
        <td>false</td>
        <td>string</td>
        <td>Search for keyword in track's artist name</td>
    </tr>
    <tr>
        <td>album_name</td>
        <td>false</td>
        <td>string</td>
        <td>Search for keyword in track's album name</td>
    </tr>
</table>

### Example request

Search for lyrics by using only q parameter:

```
GET /api/search?q=still+alive+portal
```

Search for lyrics by using multiple fields:

```
GET /api/search?track_name=22&artist_name=taylor+swift
```

### Example Response

JSON array of the lyrics records with the following parameters: `id`, `trackName`, `artistName`, `albumName`, `duration`, `instrumental`, `plainLyrics` and `syncedLyrics`.

## `POST /api/publish` Publish a new lyrics

_Note: This API is experimental and subject to potential changes in the future._

Publish a new lyrics to LRCLIB database. This API can be called anonymously, and no registration is required.

If BOTH plain lyrics and synchronized lyrics are left empty, the track will be marked as instrumental.

All previous revisions of the lyrics will still be kept when publishing lyrics for a track that already has existing lyrics.
Obtaining the Publish Token

Every `POST /api/publish` request must include a fresh, valid Publish Token in the X-Publish-Token header. Each Publish Token can only be used once.

The Publish Token consists of two parts: a prefix and a nonce concatenated with a colon ({prefix}:{nonce}).

To obtain a prefix, you need to make a request to the `POST /api/request-challenge` API. This will provide you with a fresh prefix string and a target string.

To find a valid nonce, you must solve a proof-of-work cryptographic challenge using the provided prefix and target. For implementation examples, please refer to the source code of LRCGET.

### Request header

<table>
    <tr>
        <th>Header name</th>
        <th>Required</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>X-Publish-Token</td>
        <td>true</td>
        <td>A Publish Token that can be retrieved via solving a cryptographic challenge</td>
    </tr>
</table>

### Request JSON body parameters

<table>
    <tr>
        <th>Field</th>
        <th>Required</th>
        <th>Type</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>trackName</td>
        <td>true</td>
        <td>string</td>
        <td>Title of the track</td>
    </tr>
    <tr>
        <td>artistName</td>
        <td>true</td>
        <td>string</td>
        <td>Track's artist name</td>
    </tr>
    <tr>
        <td>albumName</td>
        <td>true</td>
        <td>string</td>
        <td>Track's album name</td>
    </tr>
    <tr>
        <td>duration</td>
        <td>true</td>
        <td>number</td>
        <td>Track's duration in seconds</td>
    </tr>
    <tr>
        <td>plainLyrics</td>
        <td>true</td>
        <td>string</td>
        <td>Plain lyrics for the track. Can be empty if the track is instrumental.</td>
    </tr>
    <tr>
        <td>syncedLyrics</td>
        <td>true</td>
        <td>string</td>
        <td>Synchronized lyrics for the track. Can be empty if the track is instrumental.</td>
    </tr>
</table>

### Response

Success response: 201 Created

Failed response (incorrect Publish Token):

```
{
    "code": 400,
    "name": "IncorrectPublishTokenError",
    "message": "The provided publish token is incorrect"
}
```

# `POST /api/request-challenge` Request a challenge

_Note: This API is experimental and subject to potential changes in the future._

Generate a pair of prefix and target strings for the cryptographic challenge. Each challenge has an expiration time of 5 minutes.

The challenge's solution is a nonce, which can be used to create a Publish Token for submitting lyrics to LRCLIB.

### Example response

```
{
    "prefix": "VXMwW2qPfW2gkCNSl1i708NJkDghtAyU",
    "target": "000000FF00000000000000000000000000000000000000000000000000000000"
}
```
