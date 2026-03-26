import re
import httpx
from lxml import etree

# For some tracks, their shortname from the irsdk api does not match
# the shortname from members-assets.iracing.com/, so a rewrite is required.
OVERRIDES = {
    191: {'shortname_override': 'daytona_2011'},
    192: {'shortname_override': 'daytona_2011'},
    193: {'shortname_override': 'daytona_2011'},
    194: {'shortname_override': 'daytona_2011'},
    249: {'shortname_override': 'nurburgring_nordschleife'},
    253: {'shortname_override': 'nurburgring_nordschleife'},
    250: {'shortname_override': 'nurburgring_gp'},
    255: {'shortname_override': 'nurburgring_gp'},
    257: {'shortname_override': 'nurburgring_gp'},
    259: {'shortname_override': 'nurburgring_gp'},
    260: {'shortname_override': 'nurburgring_gp'},
    261: {'shortname_override': 'nurburgring_gp'},
    252: {'shortname_override': 'nurburgring_combined'},
    262: {'shortname_override': 'nurburgring_combined'},
    263: {'shortname_override': 'nurburgring_combined'},
    264: {'shortname_override': 'nurburgring_combined'},
    276: {'shortname_override': 'michigan_2018'},
    277: {'shortname_override': 'pocono_2016'},
    341: {'shortname_override': 'silverstone_2019'},
    342: {'shortname_override': 'silverstone_2019'},
    343: {'shortname_override': 'silverstone_2019'},
    352: {'shortname_override': 'limerock_2019'},
    353: {'shortname_override': 'limerock_2019'},
    354: {'shortname_override': 'limerock_2019'},
    355: {'shortname_override': 'limerock_2019'},
    357: {'shortname_override': 'texas_2020'},
    364: {'shortname_override': 'texas_2020'},
    371: {'shortname_override': 'kentucky_2020'},
    381: {'shortname_override': 'daytona_2011'},
    418: {'shortname_override': 'phoenix_2021'},
    419: {'shortname_override': 'phoenix_2021'},
    508: {'shortname_override': 'limerock_2019'},
    297: {'shortname_override': 'snetterton'},
    298: {'shortname_override': 'snetterton'},
    299: {'shortname_override': 'snetterton'},
    15: {'shortname_override': 'concordhalf'},
}

# On some tracks, it is necessary to rewrite the direction to avoid problems
# with the mirror movement of the car on the track in front.
DIRECTION_OVERRIDES = {
    # Kansas Speedway
    214: -1,
    215: -1,
    216: 1,
    # [Legacy] Kentucky Speedway
    188: 1,
    189: 1,
    # Kentucky Speedway
    371: 1,
    # Detroit Grand Prix
    319: -1,
    # Brands Hatch
    145: 1,
    146: 1,
    290: -1,
}

def make_track_svg_url(
    track_id: int, track_name: str, shortname: str, svg_type: str = "active",
) -> str:
    """
    Build the URL for fetching track-related SVG assets.

    Supports different SVG types such as:
    - "active" (contains external and internal main svg)
    - "start-finish" (contains the finish line and track direction)

    Applies shortname overrides for specific track IDs to ensure
    correct asset paths.

    :param track_id: iRacing track ID
    :param track_name: Human-readable track name
    :param shortname: Default track shortname
    :param svg_type: SVG type ("active" or "start-finish")
    :return: URL string pointing to the requested SVG
    """
    track_name_formatted = str(track_name).lower().replace(" ", "-")
    shortname = OVERRIDES.get(track_id, {}).get(
        "shortname_override",
        shortname,
    )
    shortname = str(shortname).lower()

    return (
        "https://members-assets.iracing.com/public/track-maps/"
        f"tracks_{shortname}/{track_id}-{track_name_formatted}/{svg_type}.svg"
    )


def extract_first_subpath(svg_text: str) -> str | None:
    """
    Extract only the first subpath (M...Z) from the SVG path.

    iRacing track SVGs often contain multiple subpaths inside a single
    <path> element (e.g., inner/outer). For accurate position
    calculations using `getPointAtLength`, we keep only the first subpath,
    which represents the main racing line.

    :param svg_text: Raw SVG string
    :return: Modified SVG string with only the first subpath,
             or original SVG if extraction fails.
    """
    try:
        root = etree.fromstring(svg_text.encode())

        # Try finding paths with namespace
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        paths = root.findall('.//svg:path', ns)

        # Fallbacks if namespace not present
        if not paths:
            paths = root.findall('.//{http://www.w3.org/2000/svg}path')
        if not paths:
            paths = root.findall('.//path')
        
        if not paths:
            return svg_text

        path_el = paths[0]
        d = path_el.get('d', '')

        # Extract first subpath from M to Z
        match = re.search(r'(M[\s\S]*?Z)', d, re.IGNORECASE)
        if match:
            path_el.set('d', match.group(1))

        return etree.tostring(root, encoding='unicode')
    except Exception as e:
        print(f"extract_first_subpath error: {e}")
        return svg_text


def fetch_svg(url: str, extract_first: bool = False) -> str | None:
    """
    Fetch an SVG file from a remote URL.

    Optionally processes the SVG to extract only the first subpath
    for better compatibility with frontend path measurements.

    :param url: SVG file URL
    :param extract_first: Whether to extract only the first subpath
    :return: SVG content as string, or None if request fails
    """
    try:
        resp = httpx.get(url, timeout=5.0)
        if resp.status_code == 200:
            text = resp.text
            if extract_first:
                text = extract_first_subpath(text)
            return text
        else:
            print(f"Load error SVG: {resp.status_code}")
            return None
    except Exception as e:
        print(f"Exception with load SVG: {e}")
        return None
