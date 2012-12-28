
import re

MB_NAMESPACES = {'mmd':'http://musicbrainz.org/ns/mmd-2.0#', 'ext':'http://musicbrainz.org/ns/ext#-2.0'}

SEARCH_ARTISTS = 'http://www.musicbrainz.org/ws/2/artist/?query=artistaccent:%s&limit=%s&offset=%s'
SEARCH_ARTIST_ALBUMS = 'http://www.musicbrainz.org/ws/2/release-group/?query=arid:%s%%20AND%%20release:%%22%s%%22&limit=%s&offset=%s'
SEARCH_ALBUMS = 'http://www.musicbrainz.org/ws/2/release-group/?query=release:%s&limit=%s&offset=%s'

ARTIST_WITH_MBID = 'http://www.musicbrainz.org/ws/2/artist/%s?inc=aliases+tags'
RELEASE_GROUP_WITH_MBID = 'http://www.musicbrainz.org/ws/2/release-group/%s?inc=releases'
RELEASE_WITH_MBID = 'http://www.musicbrainz.org/ws/2/release/%s?inc=labels+release-rels'

RELEASE_COVER_ART = 'http://coverartarchive.org/release/%s'

RE_STRIP_NONALPHA = re.compile('[^0-9a-zA-Z ]+')
RE_STRIP_PARENS = re.compile('\([^)]*\)')
  
#######################################################################
def SearchArtists(artist, offset=0, limit=5):
  artists = []

  artist = RE_STRIP_PARENS.sub('',artist)
  artist = RE_STRIP_NONALPHA.sub(' ',artist)

  Log('<<< Doing Artist search for ' + artist + ' >>>')

  try:
    content = XML.ElementFromURL(SEARCH_ARTISTS % (String.URLEncode(artist), limit, offset))
  except:
    return None
  for a in content.xpath('//mmd:artist', namespaces=MB_NAMESPACES):
    id = a.get('id')
    name = a.xpath('.//mmd:name', namespaces=MB_NAMESPACES)[0].text
    score = int(a.xpath('@ext:score',namespaces=MB_NAMESPACES)[0])
    artists.append((id, name, score))

  Log('Returning Artist metadata for ' + artist + ': ' + str(artists))
  return artists

#######################################################################
def SearchAlbums(album, artist_mbid=None, offset=0, limit=5):
  
  albums = []
  album = RE_STRIP_PARENS.sub('',album)
  album = RE_STRIP_NONALPHA.sub(' ', album)

  Log('<<< Doing Album search for ' + album + ' with artist id ' + str(artist_mbid) + ' >>>')

  if artist_mbid is not None:
    query_url = SEARCH_ARTIST_ALBUMS % (artist_mbid, String.URLEncode(album), str(limit), str(offset))
  else:
    query_url = SEARCH_ALBUMS % (String.URLEncode(album), str(limit), str(offset))

  for a in XML.ElementFromURL(query_url).xpath('//mmd:release-group', namespaces=MB_NAMESPACES):
    #Log('Found release: ' + a.xpath('./mmd:title', namespaces=MB_NAMESPACES)[0].text)
    id = a.get('id')
    title = a.xpath('./mmd:title', namespaces=MB_NAMESPACES)[0].text
    score = int(a.xpath('@ext:score',namespaces=MB_NAMESPACES)[0])
    albums.append((id, title, score))
  
  Log('Returning Album metadata for ' + album + ': ' + str(albums))
  return albums

#######################################################################
def ArtistMetadata(mbid):
  try:
    content = XML.ElementFromURL(ARTIST_WITH_MBID % mbid)
  except: 
    Log('Couldn\'t retrieve artist metadata from MusicBrainz for id ' + mbid)
    return
  artist = {}
  artist['title'] = content.xpath('//mmd:name', namespaces=MB_NAMESPACES)[0].text
  artist['title_sort'] = content.xpath('//mmd:sort-name', namespaces=MB_NAMESPACES)[0].text
  
  # aliases (original_title(s)?) are not available at the moment for artists...
  # aliases = []
  # if mbid != '89ad4ac3-39f7-470e-963a-56509c546377':
  #   for alias in content.xpath('//mmd:alias', namespaces=MB_NAMESPACES):
  #     aliases.append(alias.text)
  # artist['original_title'] = [', '.join(aliases)]
  
  Log('Returning Artist metadata for id ' + mbid + ' -> ' + str(artist))
  return artist

#######################################################################
def AlbumMetadata(mbid):
  try:
    # Need to find a specific release from within the release group, just grabbing the first one for now
    release_group = XML.ElementFromURL(RELEASE_GROUP_WITH_MBID % mbid)
    release_id = release_group.xpath('//mmd:release', namespaces=MB_NAMESPACES)[0].get('id')
    content = XML.ElementFromURL(RELEASE_WITH_MBID % release_id)
  except: 
    Log('Couldn\'t retrieve album metadata from MusicBrainz for id ' + mbid)
    return
  
  album = {}
  album['title'] = content.xpath('//mmd:title', namespaces=MB_NAMESPACES)[0].text  
  try: album['originally_available_at'] = Datetime.ParseDate(release_group.xpath('//mmd:first-release-date', namespaces=MB_NAMESPACES)[0].text).date()
  except: album['originally_available_at'] = None
  try: album['studio'] = content.xpath('//mmd:label/mmd:name', namespaces=MB_NAMESPACES)[0].text
  except: album['studio'] = None

  # Log('about to request ' + RELEASE_COVER_ART % mbid)
  # try: available_art = JSON.ObjectFromURL(RELEASE_COVER_ART % mbid)
  # except: available_art = None
  # if available_art is not None:
  #   Log(JSON.StringFromObject(available_art))

  Log('Returning Album metadata for id ' + mbid + ' -> ' + str(album))
  return album