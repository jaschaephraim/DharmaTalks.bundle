API_URL = 'http://dharma-api.com'
API_KEY = '038499f42fdc6513877e301b8277d954'
PER_PAGE = 20
PREFIX = '/music/dharmatalks'
TITLE = 'Dharma Talks'
ICON = R('icon-default.png')
ART = R('art-default.jpg')
SEARCH = L('Search')

def Start():
  ObjectContainer.art = ART
  DirectoryObject.thumb = ICON
  DirectoryObject.art = ART
  InputDirectoryObject.art = ART
  InputDirectoryObject.title = SEARCH
  InputDirectoryObject.prompt = SEARCH

@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
  return ObjectContainer(
    title1 = TITLE,
    objects = [
      DirectoryObject(
        title = 'Talks',
        key = Callback(Talks)
      ),
      DirectoryObject(
        title = 'Speakers',
        key = Callback(Speakers)
      )
    ]
  )

@route(PREFIX+'/talks', page=int)
def Talks(page=1):
  response = JSON.ObjectFromURL(QueryURL(
    slug = 'talks',
    page = page
  ))
  num_talks = response.get('metta').get('total')

  oc = ObjectContainer(title1='Talks')
  
  if page == 1:
    oc.add(InputDirectoryObject(
      key = Callback(Search, slug='talks')
    ))
  
  AddTalks(oc, response.get('results'))

  if page * PER_PAGE < num_talks:
    oc.add(NextPageObject(
      key = Callback(Talks, page=page+1)
    ))

  return oc

@route(PREFIX+'/speakers', page=int)
def Speakers(page=1):
  response = JSON.ObjectFromURL(QueryURL(
    slug = 'speakers',
    page = page
  ))
  num_talks = response.get('metta').get('total')

  oc = ObjectContainer(title1='Speakers')
  
  if page == 1:
    oc.add(InputDirectoryObject(
      key = Callback(Search, slug='speakers')
    ))
  
  AddSpeakers(oc, response.get('results'))
  
  if page * PER_PAGE < num_talks:
    oc.add(NextPageObject(
      key = Callback(Speakers, page=page+1)
    ))

  return oc

@route(PREFIX+'/speaker', speaker_id=int, page=int)
def Speaker(speaker_id, page=1):
  response = JSON.ObjectFromURL(QueryURL(
    slug = 'speaker/%d' % (speaker_id),
    page = page
  ))
  result = response.get('results')[0]
  talks = result.get('talks')
  num_talks = len(talks)

  oc = ObjectContainer(title1=result.get('name'))
  
  start_i = (page - 1) * PER_PAGE
  end_i = page * PER_PAGE
  no_more = False
  for i in range(start_i, end_i):
    if no_more:
      break
    if i == num_talks - 1:
      no_more = True
    talk = talks[i]
    oc.add(Talk(
      url = talk.get('permalink'),
      title = talk.get('title'),
      speaker = result.get('name'),
      venue = talk.get('venue'),
      date = talk.get('date'),
      image = result.get('picture'),
      duration = talk.get('duration'),
      source = talk.get('source')
    ))
  
  if not no_more:
    oc.add(NextPageObject(
      key = Callback(Speaker, speaker_id=speaker_id, page=page+1)
    ))

  return oc

@route(PREFIX+'/search', page=int)
def Search(slug, query, page=1):
  response = JSON.ObjectFromURL(QueryURL(
    slug=slug,
    page = page,
    search = query
  ))
  results = response.get('results')
  num_talks = response.get('metta').get('total')
  
  oc = ObjectContainer(title1='Search: '+query)
  
  if slug == 'talks':
    AddTalks(oc, results)
  else:
    AddSpeakers(oc, results)
  
  if page * PER_PAGE < num_talks:
    oc.add(NextPageObject(
      key = Callback(Search, slug=slug, page=page+1, query=query)
    ))
  
  return oc

@route(PREFIX+'/talk')
def Talk(url, title, speaker, venue, date, image, duration, source, include_container=False):
  track = TrackObject(
    key = Callback(
      Talk,
      url = url,
      title = title,
      speaker = speaker,
      venue = venue,
      date = date,
      image = image,
      duration = duration,
      source = source,
      include_container = True
    ),
    rating_key = url,
    title = title,
    artist = speaker,
    album = '%s %s' % (date, venue) if venue else date,
    duration = int(duration) * 1000 if duration else None,
    source_title = source,
    thumb = GetImage(image),
    art = ART,
    tags = [speaker, venue],
    items = [MediaObject(
      parts = [PartObject(key=url)],
      container = 'mp3',
      audio_codec = AudioCodec.MP3,
      audio_channels = 2
    )]
  )

  if include_container:
    return ObjectContainer(objects=[track])
  return track

def AddTalks(oc, talks):
  for talk in talks:
    speaker = talk.get('speaker')
    oc.add(Talk(
      url = talk.get('permalink'),
      title = talk.get('title'),
      speaker = speaker.get('name'),
      venue = talk.get('venue'),
      date = talk.get('date'),
      image = speaker.get('picture'),
      duration = talk.get('duration'),
      source = talk.get('source')
    ))

def AddSpeakers(oc, speakers):
  for speaker in speakers:
    oc.add(DirectoryObject(
      title = speaker.get('name'),
      summary = speaker.get('bio'),
      thumb = GetImage(speaker.get('picture')),
      key = Callback(Speaker, speaker_id=speaker.get('id'))
    ))

def GetImage(url):
  if not url or url == '/static/images/feed-icon-14x14.png':
    return ICON
  return Resource.ContentsOfURLWithFallback(url)

def QueryURL(slug, page, search=None):
  url = '%s/%s?api_key=%s&rpp=%d&page=%d' % (API_URL, slug, API_KEY, PER_PAGE, page)
  return '%s&search=%s' % (url, search) if search else url
