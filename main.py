""" Inspired by https://towardsdatascience.com/creating-interactive-maps-for-instagram-with-python-and-folium-68bc4691d075 """

import folium
import logging
from pathlib import Path
from typing import Any, Dict, Tuple
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def resize_pictures(dir_in: Path, dir_out: Path, height: int, width: int):
    for path_img_in in list(dir_in.rglob("*.jpg")):
        path_img_out = Path(dir_out / (path_img_in.name))
        logging.info(f'Converting {path_img_in} to {path_img_out} - Size {height} x {width}')
        with Image.open(path_img_in) as img:
            img.thumbnail((height, width), Image.ANTIALIAS)
            img.save(path_img_out, exif=img.getexif())


def convert_angle(angle: Tuple[float, float, float], ref: str) -> float:
    deg, min, sec = angle
    coord = round(deg + min/60.0 + sec/3600.0, 5)
    if ref in ('S', 'W'):
        coord = -coord
    return coord


def get_exif_readable(path_img_in: Path) -> Dict[str, Any]:
    image = Image.open(path_img_in)
    exif = image._getexif()
    exif_readable = {TAGS[k]: v for k,v in exif.items() if k in TAGS}
    if 'GPSInfo' in exif_readable:
        gps_info = {GPSTAGS[k]: v for k,v in exif_readable['GPSInfo'].items()}
        exif_readable['GPSInfo'] = gps_info
    return exif_readable


def get_lat_lon(exif_readable: Dict[str, Any]) -> Tuple[float, float]:
    gps_info = exif_readable['GPSInfo']
    latitude = convert_angle(gps_info['GPSLatitude'], gps_info['GPSLatitudeRef'])
    longitude = convert_angle(gps_info['GPSLongitude'], gps_info['GPSLongitudeRef'])
    return (latitude, longitude)


def plot_map(dir_photos: Path):
    # Center map on Cambridge
    my_map = folium.Map(
        location=[52.2053, 0.1218],
        zoom_start=14
    )
    # Add Marker for each photo
    for path_img_in in list(dir_photos.glob("*.jpg")):
        exif = get_exif_readable(path_img_in)
        try:
            # Re-orient picture
            orient = exif['Orientation']
            if orient in (0, 1, 3):
                width, height = 640, 480
            elif orient in (6, 8):
                width, height = 480, 640
            else:
                raise ValueError(f'Orientation value in exif data is not handled - {path_img_in} - {exif}')
            # Add GPS location marker
            folium.Marker(
                location=list(get_lat_lon(exif)),
                popup=f'<img src="{path_img_in.as_posix()}" width="{width}" height="{height}">',
                icon=folium.Icon(icon="paw", prefix='fa', color='red')
            ).add_to(my_map)

        except KeyError as err:
            logging.warning(f'Key {err} missing - Picture {path_img_in}')

    # Save to HTML
    my_map.save("index.html")


def main():
    logging.basicConfig(level=logging.ERROR)
    dir_original = Path('photos/original')
    dir_thumbnail = Path('photos/thumbnail')
    resize_pictures(dir_original, dir_thumbnail, 640, 480)
    plot_map(dir_thumbnail)


if __name__ == '__main__':
    main()
