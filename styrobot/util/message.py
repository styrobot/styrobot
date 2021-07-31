import asyncio
import aiohttp
import discord
import re
import io
import traceback
from discord.errors import NotFound
from wand.image import Image
import imageio

url_re = re.compile(r'https?://[^ \n]+(?: |\n|$)')


async def get_image_from_url(session, url, return_imageio_reader=False):
    try:
        buf = b''
        async with session.get(url) as response:
            while not response.content.at_eof():
                buf = buf + await response.content.read(8_000_000)
                if len(buf) > 8_000_000:
                    # too big
                    response.close()
                    return None
        with io.BytesIO(buf) as b:
            if not return_imageio_reader:
                return Image(blob=b)
            else:
                b.seek(0)
                return imageio.imread(b)
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
            get_image_from_url(session, url, return_imageio_reader=True) for url in urls
        ])

    return [result for result in results if result is not None]


async def image_walk(message: discord.Message, attempts=5):
    # first, check if this image has a message
    x = await get_images(message, attempts=1)
    if len(x) > 0:
        return x[0]
    # second, check replies
    if message.reference:
        try:
            msg = await message.channel.fetch_message(message.reference.id)
        except (AttributeError, KeyError, NotFound):
            pass
        else:
            x = await get_images(msg.reference, attempts=1)
            if len(x) > 0:
                return x[0]
    # next, perform the actual walk
    async for msg in message.channel.history(before=message, limit=attempts):
        x = await get_images(msg, attempts=1)
        if len(x) > 0:
            return x[0]
    return None
