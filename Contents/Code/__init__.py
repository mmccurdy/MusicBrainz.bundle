import musicbrainz, re, time

RE_STRIP_NONALPHA = re.compile('[^0-9a-zA-Z ]+')

def Start():
  HTTP.CacheTime = CACHE_1WEEK
  
# TODO(?): Use Google/JSON API for fallback artist name matching like last.fm?
# TODO: investigate throttling to comply with MB ToS
# TODO: Use meaningful User Agent to comply with MB ToS

def CallWithRetries(fun, *args):
  tries = 1  
  while tries > 0:
    try:
      return fun(*args)
    except:
      tries = tries - 1
      if tries > 0:
        Log('Call failed, retrying')
        time.sleep(2)
      else:
        raise

class MusicBrainzAgent(Agent.Artist):
  name = 'MusicBrainz'
  languages = [ Locale.Language.English ]
  primary_provider = True
  fallback_agent = False
  accepts_from = None
  contributes_to = None

  # TODO: Is the Korean locale needed?
    
  def search(self, results, media, lang):
    Log('<<< Artist search got called for ' + str(media) + ' >>>')
    if media.artist == '[Unknown Artist]': 
      return
    CallWithRetries(self.findArtists, lang, results, media, media.artist.lower())
    
    # Last.fm had a bunch of strategies for improving matches (commented below) but they don't seem to be
    # necessary with MusicBrainz and they will add a few seconds to the matching process, so let's see
    # how it does without them...

    # # If the artist starts with "The", try stripping.
    # if artist.startswith('the '):
    #   try: CallWithRetries(self.findArtists, lang, results, media, artist[4:])
    #   except: pass
      
    # # If the artist has an '&', try with 'and'.
    # if artist.find(' & ') != -1:
    #   try: CallWithRetries(self.findArtists, lang, results, media, artist.replace(' & ', ' and '))
    #   except: pass

    # # If the artist has an 'and', try with '&'.
    # if artist.find(' and ') != -1:
    #   try: CallWithRetries(self.findArtists, lang, results, media, artist.replace(' and ', ' & '))
    #   except: pass

    # De-duping results should only be needed if we call findArtist more than once...
    
    # toWhack = []
    # resultMap = {}
    # for result in results:
    #   if not resultMap.has_key(result.id):
    #     resultMap[result.id] = True
    #   else:
    #     toWhack.append(result)
    # Log('whacking ' + str(len(toWhack)) + ' duplicate search results...')
    # for dupe in toWhack:
    #   results.Remove(dupe)
    results.Sort('score', descending=True)

    try: highest_score = max([x.score for x in results])
    except: highest_score = 0

    if len(results) == 0 or highest_score < 85:
      Log('Skipping Artist: ' + media.artist)
    else:
      Log('Adding Artist: ' + media.artist)
    Log('Number of results: ' + str(len(results)) + ' Highest score: ' + str(highest_score))

  def findArtists(self, lang, results, media, artist):
    artists = musicbrainz.SearchArtists(artist)
    if artists is not None:
      for r in artists:
        results.Append(MetadataSearchResult(id=r[0],lang=lang,name=r[1],score=r[2]))

  # TODO(?): Implement score boost based on artist's album matching results
        
  def update(self, metadata, media, lang):
    Log('<<< Artist updated got called for ' + metadata.id + ' >>>')
    artist = CallWithRetries(musicbrainz.ArtistMetadata, metadata.id)
    metadata.title = artist['title']
    metadata.title_sort = artist['title_sort']
    
    # Model ref from API docs:

    # genres / A set of strings specifying the artist’s genres.
    # tags / A set of strings specifying the artist’s tags.
    # collections / A set of strings specifying the collections the artist belongs to.
    # rating / A float between 0 and 10 specifying the artist’s rating.
    # title / A string specifying the artist’s name.
    # summary / A string specifying the artist’s biography.
    # posters / A container of proxy objects representing the artist’s posters. See below for information about proxy objects.
    # art / A container of proxy objects representing the artist’s background art. See below for information about proxy objects.
    # themes / A container of proxy objects representing the artist’s theme music. See below for information about proxy objects.

class MusicBrainzAlbumAgent(Agent.Album):
  name = 'MusicBrainz'
  name = 'MusicBrainz'
  languages = [ Locale.Language.English ]
  primary_provider = True
  fallback_agent = False
  accepts_from = None
  contributes_to = None
  
  def search(self, results, media, lang):
    Log('<<< Album search got called for ' + media.title.lower() + ' >>>')
    if media.parent_metadata is None: return
    if media.parent_metadata.id == '[Unknown Album]': return #eventually, we might be able to look at tracks to match the album
    if media.parent_metadata.id != '89ad4ac3-39f7-470e-963a-56509c546377' and media.parent_metadata.title is not None:  # mbid for "Various Artists"
      # If it makes sense, include the name of the artist in the album match query
      albums = CallWithRetries(musicbrainz.SearchAlbums, media.title.lower(), media.parent_metadata.id)
    else:
      albums = CallWithRetries(musicbrainz.SearchAlbums, media.title.lower())
    for album in albums:
      (id, name, score) = album
      Log('Scanner Album: ' + media.title + ' MusicBrainz Album: ' + name + ' score=' + str(score))
      results.Append(MetadataSearchResult(id=id, name=name, lang=lang, score=score))
    results.Sort('score', descending=True)
 
  def update(self, metadata, media, lang):
    Log('<<< Album update got called for ' + media.title.lower() + ' with id ' + metadata.id + ' >>>')
    album = CallWithRetries(musicbrainz.AlbumMetadata, metadata.id)
    metadata.title = album['title']
    metadata.originally_available_at = album['originally_available_at']
    metadata.studio = album['studio']
    
    # Model ref from API docs:

    # genres / A list of strings specifying the album’s genres.
    # tags / A list of strings specifying the album’s tags.
    # collections / ..todo:: Describe
    # rating / A float between 0 and 10 specifying the album’s rating.
    # original_title / A string specifying the album’s original title.
    # title / A string specifying the album’s title.
    # summary / A string specifying the album’s summary.
    # studio / A string specifying the album’s studio.
    # originally_available_at / A date object specifying the album’s original release date.
    # producers / A list of strings specifying the album’s producers.
    # countries / A list of strings specifying the countries involved in the production of the album.
    # posters / A container of proxy objects representing the album’s covers. See below for information about proxy objects.
    # tracks / A map of Track objects representing the album’s tracks.
