import PAsearchSites
import PAgenres
import PAactors


def search(results,encodedTitle,title,searchTitle,siteNum,lang,searchDate):
    searchResults = HTML.ElementFromURL(PAsearchSites.getSearchSearchURL(siteNum) + encodedTitle)
    for searchResult in searchResults.xpath('//div[@class="grid-item"]'):
        titleNoFormatting = searchResult.xpath('.//a[@class="grid-item-title"]/text()')[0]
        curID = String.Encode(searchResult.xpath('.//a[@class="grid-item-title"]/@href')[0])

        score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())
        results.Append(MetadataSearchResult(id='%s|%d' % (curID, siteNum), name=titleNoFormatting, score=score, lang=lang))

    return results


def update(metadata,siteID,movieGenres,movieActors):
    Log('******UPDATE CALLED*******')

    metadata_id = str(metadata.id).split('|')
    sceneURL = String.Decode(metadata_id[0])
    if not sceneURL.startswith('http'):
        sceneURL = PAsearchSites.getSearchBaseURL(siteID) + sceneURL

    detailsPageElements = HTML.ElementFromURL(sceneURL)

    # Title
    metadata.title = detailsPageElements.xpath('//h1[@class="description"]/text()')[0].strip()

    # Tagline and Collection(s)
    metadata.collections.add("JAY's POV")

    # Studio
    metadata.studio = detailsPageElements.xpath('//div[@class="studio"]//span/text()')[1].strip()

    # Director
    director = metadata.directors.new()
    directorName = detailsPageElements.xpath('//div[@class="director"]/text()')[0].strip()
    director.name = directorName

    # Release Date
    date = detailsPageElements.xpath('//div[@class="release-date"]/text()')[0].strip()
    date_object = parse(date)
    metadata.originally_available_at = date_object
    metadata.year = metadata.originally_available_at.year

    # Actors
    movieActors.clearActors()
    for actorLink in detailsPageElements.xpath('//div[@class="video-performer"]//img'):
        actorName = actorLink.get('title')
        actorPhotoURL = actorLink.get('data-bgsrc')

        movieActors.addActor(actorName, actorPhotoURL)

    # Genres
    movieGenres.clearGenres()
    for genreName in detailsPageElements.xpath('//div[@class="tags"]//a/text()'):
        movieGenres.addGenre(genreName)

    # Posters
    art = []

    for poster in detailsPageElements.xpath('//div[@id="dv_frames"]//img/@src'):
        img = poster.replace('320', '1280')
        art.append(img)

    Log('Artwork found: %d' % len(art))
    for idx, posterUrl in enumerate(art, 1):
        if not PAsearchSites.posterAlreadyExists(posterUrl, metadata):
            # Download image file for analysis
            try:
                img_file = urllib.urlopen(posterUrl)
                im = StringIO(img_file.read())
                resized_image = Image.open(im)
                width, height = resized_image.size
                # Add the image proxy items to the collection
                if width > 10:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order=idx)
                if width > 100:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order=idx)
            except:
                pass

    return metadata
