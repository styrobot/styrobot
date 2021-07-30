import asyncio
import aiohttp
import discord
import re
import io
import traceback
from wand.image import Image

url_re = re.compile(r'https?://[^ \n]+(?: |\n|$)')

async def get_image_from_url(session, url):
    try:
        buf = b''
        async with session.get(url) as response:
            while not response.content.at_eof():
                buf = buf + await response.content.read(8_000_000)
                if len(buf) > 8_000_000:
                    # too big
                    response.close()
                    return None
        b = io.BytesIO(buf)
        return Image(blob=b)
    except Exception:
        traceback.print_exc()
    return None

async def get_images(message: discord.Message, attempts=1):
    urls = []

    urls.extend([a.url for a in message.attachments if
        (a.size < 8_000_000) and (a.content_type in 'image/png;image/jpeg;image/webp'.split(';'))
    ])
    urls.extend([
        e.image.url for e in message.embeds if
        e.image and e.image.url
    ])
    urls.extend([
        x.strip() for x in url_re.findall(message.content) if x
    ])

    urls = urls[:attempts]

    if len(urls) == 0:
        return []

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[
            get_image_from_url(session, url) for url in urls
        ])
    
    return [result for result in results if result is not None]