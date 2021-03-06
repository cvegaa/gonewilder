#!/usr/bin/python

from Httpy    import Httpy
from os       import path, getcwd, sep, mkdir
from PIL      import Image # Python Image Library
from commands import getstatusoutput
from sys      import stderr
from time     import strftime, gmtime

class ImageUtils(object):
	logger = stderr

	# Static class variables
	MAXIMUM_THUMBNAIL_SIZE = 5 * 1024 * 1024 # In bytes
	MAXIMUM_THUMBNAIL_DIM  = 5000 # In pixels
	httpy = Httpy()

	@staticmethod
	def debug(text):
		tstamp = strftime('[%Y-%m-%dT%H:%M:%SZ]', gmtime())
		text = '%s ImageUtils: %s' % (tstamp, text)
		ImageUtils.logger.write('%s\n' % text)
		if ImageUtils.logger != stderr:
			stderr.write('%s\n' % text)

	'''
		Given a URL, return a tuple containig:
		[0] media type ('video', 'image')
		[1] filesystem-safe album name, or None if not an album
		[2] List of all direct links to relevant media. E.g.:
					imgur.com/asdf1 -> [i.imgur.com/asdf1.jpg]
					i.imgur.com/smallh.jpg -> [i.imgur.com/large.jpg]
					imgur.com/a/album -> [i.imgur.com/image1.jpg, i.imgur.com/image2.jpg]
					xhamster.com/video -> xhamster.com/cdn/video.mp4
					etc
		Throws exception if domain is not supported.
	'''
	@staticmethod
	def get_urls(url):
		if 'imgur.com' in url.lower():
			return ImageUtils.get_urls_imgur(url)
		elif '.' in url and url.lower()[url.rfind('.')+1:] in ['jpg', 'jpeg', 'png', 'gif']:
			# Direct link to image
			return ('image', None, [url])
		elif '.' in url and url.lower()[url.rfind('.')+1:] in ['mp4', 'flv', 'wmv']:
			# Direct link to video
			return ('video', None, [url])
		elif 'xhamster.com' in url:
			# xhamster
			return ImageUtils.get_urls_xhamster(url)
		elif 'videobam.com' in url:
			# videobam
			return ImageUtils.get_urls_videobam(url)
		elif 'sexykarma.com' in url:
			# sexykarma
			return ImageUtils.get_urls_sexykarma(url)
		elif 'tumblr.com' in url:
			# tumblr
			return ImageUtils.get_urls_tumblr(url)
		elif 'vine.co/' in url:
			# vine
			return ImageUtils.get_urls_vine(url)
		elif 'vidble.com/' in url:
			# vidble
			return ImageUtils.get_urls_vidble(url)
		elif 'soundcloud.com/' in url or 'snd.sc/' in url:
			# soundcloud
			return ImageUtils.get_urls_soundcloud(url)
		elif 'soundgasm.net/' in url:
			# soundgasm
			return ImageUtils.get_urls_soundgasm(url)
		elif 'chirb.it/' in url or 'chirbit.com' in url:
			# chirbit
			return ImageUtils.get_urls_chirbit(url)
		elif 'vocaroo.com/' in url:
			# vocaroo
			return ImageUtils.get_urls_vocaroo(url)
		elif 'imgdoge.com/' in url:
			# imgdoge
			return ImageUtils.get_urls_imgdoge(url)
		elif 'gifboom.com/' in url:
			# imgdoge
			return ImageUtils.get_urls_gifboom(url)
		elif 'mediacru.sh/' in url:
			# imgdoge
			return ImageUtils.get_urls_mediacrush(url)
		else:
			raise Exception('domain not supported; %s' % url)
	
	''' Removes excess fields from URL '''
	@staticmethod
	def strip_url(url):
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		if '&' in url: url = url[:url.find('&')]
		return url

	################
	# XHAMSTER
	@staticmethod
	def get_urls_xhamster(url):
		ImageUtils.debug('xhamster: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		if not "<div class='mp4'>" in r:
			raise Exception('no mp4 found at %s' % url)
		chunk = ImageUtils.httpy.between(r, "<div class='mp4'>", "</div>")[0]
		return ('video', None, [ImageUtils.httpy.between(chunk, 'href="', '"')[0]])

	################
	# VIDEOBAM
	@staticmethod
	def get_urls_videobam(url):
		ImageUtils.debug('videobam: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		if not ',"url":"' in r:
			raise Exception('no url found at %s' % url)
		for link in ImageUtils.httpy.between(r, '"url":"', '"'):
			if not '.mp4' in link: continue
			return ('video', None, [link.replace('\\', '')])
		raise Exception('no mp4 found at %s' % url)

	################
	# SEXYKARMA
	@staticmethod
	def get_urls_sexykarma(url):
		ImageUtils.debug('sexykarma: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		if not "url: escape('" in r:
			raise Exception('no url found at %s' % url)
		for link in ImageUtils.httpy.between(r, "url: escape('", "'"):
			return ('video', None, [link])
		raise Exception('no video found at %s' % url)

	################
	# TUMBLR
	@staticmethod
	def get_urls_tumblr(url):
		ImageUtils.debug('tumblr: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		if not 'source src=\\x22' in r:
			raise Exception('no src= found at %s' % url)
		for link in ImageUtils.httpy.between(r, 'source src=\\x22', '\\x22'):
			link = ImageUtils.httpy.unshorten(link)
			return ('video', None, [link])
		raise Exception('no video found at %s' % url)

	################
	# VINE
	@staticmethod
	def get_urls_vine(url):
		ImageUtils.debug('vine: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		if not 'property="twitter:image" content="' in r:
			raise Exception('no twitter:image found at %s' % url)
		for link in ImageUtils.httpy.between(r, 'property="twitter:image" content="', '"'):
			return ('video', None, [link])
		raise Exception('no video found at %s' % url)

	################
	# VIDBLE
	@staticmethod
	def get_urls_vidble(url):
		ImageUtils.debug('vidble: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		urls = []
		for index, link in enumerate(ImageUtils.httpy.between(r, "<img src='", "'")):
			if '"' in link: continue
			if not link.startswith('/'): link = '/%s' % link
			urls.append('http://www.vidble.com%s' % link.replace('_med.', '.'))
		return ('image', None, urls)

	################
	# SOUNDCLOUD
	@staticmethod
	def get_urls_soundcloud(url):
		ImageUtils.debug('soundcloud: getting %s' % url)
		from DB   import DB
		from json import loads
		db = DB()
		(client_id, secret_id) = db.get_credentials('soundcloud')
		url = 'http://api.soundcloud.com/resolve.json?url=%s&client_id=%s' % (url, client_id)
		r = ImageUtils.httpy.get(url)
		json = None
		try:
			json = loads(r)
			if 'download_url' in json:
				download = '%s&client_id=%s' % (json['download_url'], client_id)
				return ('audio', None, [download])
		except Exception, e:
			raise Exception('unable to parse json')
		return []

	################
	# SOUNDGASM
	@staticmethod
	def get_urls_soundgasm(url):
		ImageUtils.debug('soundgasm: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		urls = []
		for link in ImageUtils.httpy.between(r, 'm4a: "', '"'):
			urls.append(link)
		return ('audio', None, urls)

	################
	# VOCAROO
	@staticmethod
	def get_urls_vocaroo(url):
		ImageUtils.debug('vocaroo: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		urls = []
		for link in ImageUtils.httpy.between(r, '<source src="', '"'):
			urls.append('http://vocaroo.com%s' % link)
			break # Only get the first one
		return ('audio', None, urls)

	################
	# IMGDOGE
	@staticmethod
	def get_urls_imgdoge(url):
		ImageUtils.debug('imgdoge: getting %s' % url)
		pdata = { 'imgContinue' : 'Continue to image - click here' }
		r = ImageUtils.httpy.oldpost(url, postdict=pdata)
		urls = []
		for link in ImageUtils.httpy.between(r, "<a href='http://imgdoge.com/upload/big/", "'"):
			urls.append('http://imgdoge.com/upload/big/%s' % link)
			break # Only get the first one
		return ('image', None, urls)

	################
	# GIFBOOM
	@staticmethod
	def get_urls_gifboom(url):
		ImageUtils.debug('gifboom: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		urls = []
		for link in ImageUtils.httpy.between(r, 'twitter:player:stream" content="', '"'):
			urls.append(link)
			break # Only get the first one
		return ('image', None, urls)

	################
	# MEDIACRUSH
	@staticmethod
	def get_urls_mediacrush(url):
		ImageUtils.debug('mediacrush: getting %s' % url)
		while url.endswith('/'): url = url[:-1]
		r = ImageUtils.httpy.get('%s.json' % url)
		from json import loads
		json = loads(r)
		mediatype = album = None
		urls = []
		for fil in json.get('files', []):
			if 'url' in fil:
				mediatype = fil['type']
				mediatype = mediatype[:mediatype.find('/')]
				u = fil['url']
				if u.startswith('/'):
					u = 'http://mediacru.sh%s' % u
				urls.append(u)
				break
			elif 'files' in fil:
				mediatype = 'album'
				album = url[url.find('cru.sh/')+len('cru.sh/'):]
				if '/' in album: album = album[:album.find('/')]
				if '?' in album: album = album[:album.find('?')]
				if '#' in album: album = album[:album.find('#')]
				for subfil in fil['files']:
					u = subfil['url']
					if u.startswith('/'):
						u = 'http://mediacru.sh%s' % u
					urls.append(u)
					break
		return (mediatype, album, urls)

	################
	# CHIRBIT
	@staticmethod
	def get_urls_chirbit(url):
		ImageUtils.debug('chirbit: getting %s' % url)
		r = ImageUtils.httpy.get(url)
		urls = []
		for link in ImageUtils.httpy.between(r, 'setFile", "', '"'):
			urls.append(link)
		return ('audio', None, urls)

	################
	# IMGUR
	@staticmethod
	def get_urls_imgur(url):
		if url.startswith('//'): url = 'http:%s' % url
		url = ImageUtils.strip_url(url)
		if '/m.imgur.com/' in url: url = url.replace('/m.imgur.com/', '/imgur.com/')
		if '.com/a/' in url:
			# Album
			albumid = url[url.find('/a/')+3:]
			if '/' in albumid: albumid = albumid[:albumid.find('/')]
			if '#' in albumid: albumid = albumid[:albumid.find('#')]
			if '?' in albumid: albumid = albumid[:albumid.find('?')]
			return ('album', albumid, ImageUtils.get_imgur_album(url))
		else:
			# Image
			return ('image', None, [ImageUtils.get_imgur_highest_res(url)])
		raise Exception('unable to get urls from %s' % url)

	@staticmethod
	def get_imgur_album(url):
		# Sanitize album URL
		url = url.replace('http://', '').replace('https://', '')
		fields = url.split('/')
		while fields[-2] != 'a': fields.pop(-1)
		url = 'http://%s' % '/'.join(fields)
		# Get album
		result = []
		#ImageUtils.debug('imgur_album: loading %s' % url)
		r = ImageUtils.httpy.get('%s/noscript' % url)
		for image in ImageUtils.httpy.between(r, '<img src="//i.', '"'):
			image = 'http://i.%s' % image
			image = ImageUtils.get_imgur_highest_res(image)
			result.append(image)
		ImageUtils.debug('get_imgur_album: found %d images in album' % len(result))
		return result
	
	@staticmethod
	def get_imgur_highest_res(url):
		if not '/' in url:
			raise Exception('invalid url: %s' % url)
		fname = url.split('/')[-1]
		if '.' in fname and fname[fname.rfind('.')-1] == 'h':
			# Might not be highest res, revert to image-page
			noh = url[:url.rfind('h.')] + url[url.rfind('h.')+1:]
			meta = ImageUtils.httpy.get_meta(noh)
			if 'Content-Length' in meta and meta['Content-Length'] == '503' \
			   or meta['content-type'] == 'unknown' \
			   or meta['content-type'].startswith('text/html'):
				ImageUtils.debug('imgur_highest_res: %s -> %s' % (url, url))
				return url
			else:
				ImageUtils.debug('imgur_highest_res: %s -> %s' % (url, noh))
				return noh
		elif not '.' in fname:
			# Need to get full-size and extension
			r = ImageUtils.httpy.get(url)
			if not '<link rel="image_src" href="' in r:
				raise Exception('image not found')
			image = ImageUtils.httpy.between(r, '<link rel="image_src" href="', '"')[0]
			if image.startswith('//'): image = 'http:%s' % image
			ImageUtils.debug('imgur_highest_res: %s -> %s' % (url, image))
			return image
		return url


	'''
		Return just filename (no path) for a URL
			http://i.imgur.com/asdf1.jpg -> "asdf1.jpg"
			amazonaws.com/crazystuff/theimage.jpg?morecrazy=stuff&asdf=123 -> "theimage.jpg"
			http://2.videobam.com/storage/encoded.mp4/2d1/5113?ss=177 -> "encoded.mp4"
		Also appends 'mp3' file extension for audio files that end with 'php' (vocaroo)
	'''
	@staticmethod
	def get_filename_from_url(url, media_type='image'):
		fname = ImageUtils.strip_url(url)
		fields = fname.split('/')
		while not '.' in fields[-1]: fields.pop(-1)
		filename = fields[-1]
		if media_type == 'audio':
			if filename.endswith('.php'):
				filename = filename[:filename.rfind('.')+1] + 'mp3'
		return filename


	########################
	# ACTUAL IMAGE FUNCTIONS

	'''
		Create thumbnail from existing image file.
		Raises exception if unable to save thumbnail
	'''
	@staticmethod
	def create_thumbnail(image, saveas):
		if image.lower().endswith('.mp4') or \
		   image.lower().endswith('.flv') or \
			 image.lower().endswith('.wmv'):
			return ImageUtils.create_video_thumbnail(image, saveas)
		if path.getsize(image) > ImageUtils.MAXIMUM_THUMBNAIL_SIZE:
			raise Exception('Image too large: %db %db' % 
					(path.getsize(image), ImageUtils.MAXIMUM_THUMBNAIL_SIZE))
		try:
			im = Image.open(image)
		except Exception, e:
			raise Exception('failed to create thumbnail: %s' % str(e))
		(width, height) = im.size
		if width  > ImageUtils.MAXIMUM_THUMBNAIL_DIM or \
		   height > ImageUtils.MAXIMUM_THUMBNAIL_DIM:
			raise Exception(
					'Image too large: %dx%d > %dpx' % 
					(width, height, ImageUtils.MAXIMUM_THUMBNAIL_DIM))
			
		if im.mode != 'RGB': im = im.convert('RGB')
		im.thumbnail( (200,200), Image.ANTIALIAS)
		im.save(saveas, 'JPEG')
		return saveas

	''' 
		Create thumbnail for video file using ffmpeg.
		Raises exception if unable to save video thumbnail
	'''
	@staticmethod
	def create_video_thumbnail(video, saveas):
		if saveas.lower().endswith('.mp4') or \
			 saveas.lower().endswith('.flv') or \
			 saveas.lower().endswith('.wmv'):
			saveas = '%s.png' % saveas[:saveas.rfind('.')]
		overlay = path.join(ImageUtils.get_root(), 'images', 'play_overlay.png')
		ffmpeg = '/usr/bin/ffmpeg'
		if not path.exists(ffmpeg):
			ffmpeg = '/opt/local/bin/ffmpeg'
			if not path.exists(ffmpeg):
				raise Exception('ffmpeg not found; unable to create video thumbnail')
		cmd = ffmpeg
		cmd += ' -i "'
		cmd += video
		cmd += '" -vf \'movie='
		cmd += overlay
		cmd += ' [watermark]; '
		cmd += '[in]scale=200:200 [scale]; '
		cmd += '[scale][watermark] overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2 [out]\' '
		cmd += saveas
		output = ''
		try:
			(status, output) = getstatusoutput(cmd)
		except:
			raise Exception('failed to generate thumbnail using ffmpeg: %s' % output)
		return saveas

	'''
		Get width/height of image or video
	'''
	@staticmethod
	def get_dimensions(image):
		if image.lower().endswith('.mp4') or \
		   image.lower().endswith('.flv'):
			ffmpeg = '/usr/bin/ffmpeg'
			if not path.exists(ffmpeg):
				ffmpeg = '/opt/local/bin/ffmpeg'
				if not path.exists(ffmpeg):
					raise Exception('ffmpeg not found; unable to get video dimensions')
			(status, output) = getstatusoutput('%s -i "%s"' % (ffmpeg, image))
			for line in output.split('\n'):
				if 'Stream' in line and 'Video:' in line:
					line = line[line.find('Video:')+6:]
					fields = line.split(', ')
					dims = fields[2]
					if not 'x' in dims: raise Exception('invalid video dimensions')
					(width, height) = dims.split('x')
					if ' ' in height: height = height[:height.find(' ')]
					try:
						width  = int(width)
						height = int(height)
					except:
						raise Exception('invalid video dimensions: %sx%s' % (width, height))
					return (width, height)
			raise Exception('unable to get video dimensions')
		else:
			im = Image.open(image)
			return im.size


	###############
	# MISCELLANEOUS

	@staticmethod
	def create_subdirectories(directory):
		current = ''
		for subdir in directory.split(sep):
			if subdir == '': continue
			current = path.join(current, subdir)
			if not path.exists(current):
				mkdir(current)

	''' Get root working dir '''
	@staticmethod
	def get_root():
		cwd = getcwd()
		if cwd.endswith('py'):
			return '..'
		return '.'

if __name__ == '__main__':
	#url = 'http://www.sexykarma.com/gonewild/video/cum-compilation-YIdo9ntfsWo.html'
	#url = 'http://xhamster.com/movies/1435778/squirting_hard.html'
	#url = 'http://videobam.com/jcLzr'
	#url = 'http://alwaysgroundedx.tumblr.com/private/22807448211/tumblr_m3tyhmw3mQ1ruoc8i'
	#url = 'https://vine.co/v/h6Htgnj7Z5q'
	#url = 'http://www.vidble.com/album/CwlMIYqm'
	#url = 'http://www.vidble.com/ieIvnqJY4v'
	#url = 'http://vidble.com/album/pXpkBBpD'
	#url = 'http://vidble.com/album/schhngs4'
	#url = 'http://snd.sc/1d2RCEv'
	#url = 'http://soundgasm.net/u/sexuallyspecific/F4M-A-week-of-retribution-TD-Challenge-Part-7-The-Finale'
	#url = 'http://chirb.it/5vyK6D'
	#url = 'http://vocaroo.com/i/s0umizubFmH6'
	#url = 'http://imgdoge.com/img-52ed7dd198460.html'
	#url = 'http://gifboom.com/x/5c009736'
	url = 'https://mediacru.sh/5dc4cee7fb94' # album
	#url = 'https://mediacru.sh/d7CsmyozGgB7'
	(a, b, urls) = ImageUtils.get_urls(url)
	print a, b, urls
	for i,u in enumerate(urls):
		print i,u
	fil = urls[0]
	ImageUtils.httpy.download(fil, 'test.%s' % fil[fil.rfind('.')+1:])
	#ImageUtils.create_thumbnail('test.jpg', 'test_thumb.jpg')
	#ImageUtils.create_thumbnail('../test.mp4', '../test_thumb.jpg')
	# Testing imgur highest-res
	#print ImageUtils.get_imgur_highest_res('http://i.imgur.com/30GO67h.jpg')
	#print ImageUtils.get_imgur_highest_res('http://i.imgur.com/30GO67hh.jpg')
	pass
