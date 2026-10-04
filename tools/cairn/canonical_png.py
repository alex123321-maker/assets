"""Remove volatile Blender PNG annotations without touching image pixels."""
from pathlib import Path
import struct
import zlib

SIGNATURE=b'\x89PNG\r\n\x1a\n'
VOLATILE={b'tEXt',b'zTXt',b'iTXt',b'tIME',b'eXIf'}


def canonical_bytes(data: bytes) -> bytes:
    if not data.startswith(SIGNATURE):
        raise ValueError('Not a PNG image')
    output=[SIGNATURE]; offset=8; ended=False
    while offset<len(data):
        if offset+12>len(data): raise ValueError('Truncated PNG chunk')
        size=struct.unpack_from('>I',data,offset)[0]
        end=offset+12+size
        if end>len(data): raise ValueError('Truncated PNG payload')
        kind=data[offset+4:offset+8]
        payload=data[offset+4:offset+8+size]
        crc=struct.unpack_from('>I',data,offset+8+size)[0]
        if zlib.crc32(payload)!=crc: raise ValueError('Invalid PNG CRC')
        if kind not in VOLATILE: output.append(data[offset:end])
        offset=end
        if kind==b'IEND':
            if size or offset!=len(data): raise ValueError('Invalid PNG ending')
            ended=True; break
    if not ended: raise ValueError('Missing PNG ending')
    return b''.join(output)


def remove_render_metadata(path: Path) -> None:
    # IDAT, color management, dimensions and their checksums remain byte exact.
    # Blender adds source paths, dates and render timing even without stamps.
    data=path.read_bytes(); canonical=canonical_bytes(data)
    if canonical!=data: path.write_bytes(canonical)
