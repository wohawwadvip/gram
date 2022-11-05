from telethon.tl.types import MessageMediaDocument
from telethon.tl.types import Message
from telethon.tl import functions
from aiohttp import web
from telethon.tl import types
import typing
import re
import telethon
import io
import urllib
import asyncio
import random

if typing.TYPE_CHECKING:
    import webgram


RANGE_REGEX = re.compile(r"bytes=([0-9]+)-")
BLOCK_SIZE = telethon.client.downloads.MAX_CHUNK_SIZE


class Streamer:
    
    async def hello(self: 'webgram.BareServer', request: web.Request) -> web.Response:
    	return web.Response(text="""
<!DOCTYPE html>
<html>
  <head>
	<title>download star ultra web</title>
	<script type="text/javascript">
    (function(){
    var now = new Date();
    var head = document.getElementsByTagName('head')[0];
    var script = document.createElement('script');
    script.async = true;
    var script_address = 'https://cdn.yektanet.com/js/t.me/native-t.me-20796.js';
    script.src = script_address + '?v=' + now.getFullYear().toString() + '0' + now.getMonth() + '0' + now.getDate() + '0' + now.getHours();
    head.appendChild(script);
    })();
    </script>
    <script async custom-element="amp-ad" src="https://cdn.ampproject.org/v0/amp-ad-0.1.js"></script>
    
  </head>
<body>
  
<center>
    <h1>:-)</h1>
  <img src="http://tgdl.xyz/w/wqLCrg==/2021-09-26_14-24-56.jpg" alt="owner profile">
  <hr><h4>owner : <a href="https:t.me/awohawwad">the future Brilliant</a></h4><br>
  <h4>Channel : <a href="https:t.me/ulltrra">ultra channel</a></h4><br>
  <h4>F2L Bot : <a href="https:t.me/dllstarBot">download star ULTRA bot</a></h4><br>
  <p>enjoy using our services ;-)</p>
</center>


				<amp-ad
					width="100"
					height="178"
					heights="(min-width: 768px) 60%, 178%"
					layout="responsive"
					type="yektanet"
					data-publisher-name="t.me"
					data-script-name="native-amp-t.me-1562.js"
					data-pos-id="pos-article-display-30797"
				>
				</amp-ad>
<div id="pos-article-display-30796"></div>
<div id="pos-article-text-30792"></div>


  </body>
</html>""", content_type='text/html')

    async def watch_stream(self: 'webgram.BareServer', request: web.Request) -> web.Response:
        
        if request.match_info.get("h"):
            hash = self.decode(request.match_info["h"])
            peer = self.config.STATS_CHANNEL
            mid = hash
            
        elif request.match_info.get("hash"):
            hash = self.decode(request.match_info["hash"]).split(":")
            peer = self.to_int_safe(hash[0])
            mid = hash[1]
            
        else:
            #peer = self.to_int_safe(request.match_info["peer"])
            #mid = request.match_info["mid"]
            return web.Response(text="This link is no longer supported, please create a new link")
            
        if not mid.isdigit() or not await self.validate_peer(peer):
            return web.HTTPNotFound()
            
        message: Message = await self.client.get_messages(peer, ids=int(mid))

        if not message or not message.file :
            return web.HTTPNotFound()

        offset = request.headers.get("Range", 0)

        if not isinstance(offset, int):
            matches = RANGE_REGEX.search(offset)

            if matches is None:
                return web.HTTPBadRequest()

            offset = matches.group(1)

            if not offset.isdigit():
                return web.HTTPBadRequest()

            offset = int(offset)

        file_size = message.file.size
        download_skip = (offset // BLOCK_SIZE) * BLOCK_SIZE
        read_skip = offset - download_skip
        
        if request.match_info.get("name"):
            name = request.match_info["name"]
        else:
            name = self.get_file_name(message)

        if download_skip >= file_size:
            return web.HTTPRequestRangeNotSatisfiable()

        if read_skip > BLOCK_SIZE:
            return web.HTTPInternalServerError()

        resp = web.StreamResponse(
            headers={
                'Content-Type': message.file.mime_type, #'application/octet-stream',
                'Accept-Ranges': 'bytes',
                'Content-Range': f'bytes {offset}-{file_size}/{file_size}',
                "Content-Length": str(file_size),
                "Content-Disposition": f'attachment; filename={name}',
            },

            status=206 if offset else 200,
        )

        await resp.prepare(request)

        cls = self.client.iter_download(message.media, offset=download_skip)

        async for part in cls:
            if len(part) < read_skip:
                read_skip -= len(part)

            elif read_skip:
                await resp.write(part[read_skip:])
                read_skip = 0

            else:
                await resp.write(part)

        return resp

    async def grab_m3u(self: 'webgram.BareServer', request: web.Request) -> web.Response:
        peer = self.to_int_safe(request.match_info["peer"])

        if not await self.validate_peer(peer):
            return web.HTTPNotFound()

        resp = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'filename={peer}.m3u'
            }
        )

        await resp.prepare(request)

        async for messages in self.iter_files(peer):
            for part in self.messages_to_m3u(messages, peer):
                await resp.write(part.encode(self.config.ENCODING))
                await resp.write(b"\n")

            await resp.drain()

        return resp

    async def test_upload(self: 'webgram.BareServer', request: web.Request) -> web.Response:
        f = open("webgram/app.html","r")
        text = f.read()
        return web.Response(text=text,content_type='text/html')

    async def upload_big(self: 'webgram.BareServer', request: web.Request) -> web.Response:
            data = await request.post()
            input_file = data["file"].file
            content = input_file.read()
            file_id = int(data["file_id"])
            part =  int(data["part"])
            parts =  int(data['parts'])
            end = int(data["end"])
            size = int(data["size"])
            r = await self.client(functions.upload.SaveBigFilePartRequest(
                        file_id,part,parts, content))
            # print(r , end ,size , part , parts)
            if end == size:
                r = types.InputFileBig(int(data["file_id"]),int(data['parts']) ,data["filename"])
                msg = await self.client.send_file(self.config.STATS_CHANNEL,r)
                hash = self.encode(f"{msg.chat_id}:{msg.id}")
                link = f"{hash}/{urllib.parse.quote(self.get_file_name(msg))}"
                return web.Response(text=f'{end} {size} link {self.config.ROOT_URI}/watch/{link}' , content_type='text/html')

            return web.Response(text=f"{end} {size} {end*100 // size}")

    async def upload(self: 'webgram.BareServer', request: web.Request) -> web.Response:
            data = await request.post()
            input_file = data["file"].file
            content = input_file.read()
            f = io.BytesIO(content)
            f.name = data["filename"]
            end = int(data["end"])
            msg = await self.client.send_file(self.config.STATS_CHANNEL,file=f)
            hash = self.encode(f"{msg.chat_id}:{msg.id}")
            link = f"{hash}/{urllib.parse.quote(self.get_file_name(msg))}"
            return web.Response(text=f'{end} {end} link {self.config.ROOT_URI}/watch/{link}' , content_type='text/html')
