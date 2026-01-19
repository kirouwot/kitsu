from datetime import datetime

from app.parser import anime as anime_parser
from app.parser import episodes as episodes_parser
from app.parser import schedule as schedule_parser
from app.parser import search as search_parser


def test_parse_anime_page_returns_expected_fields() -> None:
    html = """
    <div id="syncData">{"anilist_id": 101, "mal_id": 202}</div>
    <span class="film-name dynamic-name">Sample Anime</span>
    <img class="film-poster-img" src="https://img/poster.jpg"/>
    <div class="film-description"><div class="text">Some description here.</div></div>
    """
    parsed = anime_parser.parse_anime_page(html, "anime-slug")

    assert parsed["id"] == "anime-slug"
    assert parsed["title"] == "Sample Anime"
    assert parsed["poster"] == "https://img/poster.jpg"
    assert parsed["description"] == "Some description here."
    assert parsed["anilistID"] == 101
    assert parsed["malID"] == 202


def test_parse_episodes_html_extracts_episode_list() -> None:
    html = """
    <div class="detail-infor-content">
      <div class="ss-list">
        <a href="/watch/show/ep-1" data-number="1" title="Ep 1"></a>
        <a href="/watch/show/ep-2" data-number="2" class="ssl-item-filler" title="Ep 2"></a>
      </div>
    </div>
    """
    parsed = anime_parser.parse_episodes_html(html)

    assert parsed["totalEpisodes"] == 2
    assert parsed["episodes"][0] == {
        "title": "Ep 1",
        "episodeId": "ep-1",
        "number": 1,
        "isFiller": False,
    }
    assert parsed["episodes"][1]["isFiller"] is True


def test_parse_server_html_prefers_matching_server() -> None:
    html = """
    <div class="server-notice"><strong>Episode 5</strong></div>
    <div class="ps_-block servers-sub">
      <div class="ps__-list">
        <div class="server-item" data-server-id="10">Alpha</div>
        <div class="server-item" data-server-id="11">Beta</div>
      </div>
    </div>
    """
    chosen_id, parsed = episodes_parser.parse_server_html(html, "sub", preferred="beta")

    assert parsed["episodeNo"] == "5"
    assert chosen_id == 11
    assert parsed["sub"][0]["serverId"] == 10


def test_build_sources_payload_returns_ids_and_sources() -> None:
    watch_html = """<div id="syncData">{"anilist_id": 7, "mal_id": 8}</div>"""

    payload = episodes_parser.build_sources_payload(
        "https://stream/link", watch_html, referer="https://example.com"
    )

    assert payload["headers"] == {"Referer": "https://example.com"}
    assert payload["sources"] == [{"url": "https://stream/link", "type": "iframe"}]
    assert payload["anilistID"] == 7
    assert payload["malID"] == 8


def test_parse_schedule_html_builds_items() -> None:
    html = """
    <ul>
      <li>
        <a href="/anime/slug">
          <span class="time">12:30</span>
          <span class="film-name dynamic-name" data-jname="JP Name">EN Name</span>
        </a>
        <div class="fd-play"><button>Ep 4</button></div>
      </li>
    </ul>
    """
    now = datetime.fromisoformat("2024-01-02T12:00:00")
    parsed = schedule_parser.parse_schedule_html(
        html, target_date="2024-01-02", current_time=now
    )["scheduledAnimes"][0]

    assert parsed["id"] == "anime/slug"
    assert parsed["name"] == "EN Name"
    assert parsed["jname"] == "JP Name"
    assert parsed["episode"] == 4
    assert parsed["airingTimestamp"] == int(
        datetime.fromisoformat("2024-01-02T12:30:00").timestamp() * 1000
    )
    assert parsed["secondsUntilAiring"] == 1800


def test_parse_search_suggestions_skips_invalid_links() -> None:
    html = """
    <div class="nav-item" href="javascript:void(0)"></div>
    <div class="nav-item" href="/watch/show-1?ref=home">
      <span class="film-name" data-jname="J">Show 1</span>
      <img class="film-poster-img" data-src="poster.jpg"/>
      <div class="film-infor">Subbed<br/>2024</div>
    </div>
    """
    parsed = search_parser.parse_search_suggestions(html)["suggestions"]

    assert len(parsed) == 1
    assert parsed[0]["id"] == "watch/show-1"
    assert parsed[0]["name"] == "Show 1"
    assert parsed[0]["poster"] == "poster.jpg"
