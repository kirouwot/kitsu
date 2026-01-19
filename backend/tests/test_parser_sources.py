import httpx
import pytest
from app.parser.config import ParserSettings
from app.parser.services.sync_service import ParserSyncService
from app.parser.sources.kodik_episode import KodikEpisodeSource
from app.parser.sources.shikimori_catalog import ShikimoriCatalogSource
from app.parser.sources.shikimori_schedule import ShikimoriScheduleSource


def make_response(url: str, data: object, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("GET", url)
    return httpx.Response(status_code, json=data, request=request)


def make_async_client(
    responses: dict[str, httpx.Response | Exception],
    calls: list[tuple[str, object | None]] | None = None,
) -> type:
    class DummyAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def get(self, url: str, params: object | None = None):
            if calls is not None:
                calls.append((url, params))
            response = responses[url]
            if isinstance(response, Exception):
                raise response
            return response

    return DummyAsyncClient


def test_shikimori_catalog_maps_titles_and_relations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = {
        "https://shiki.test/animes": make_response(
            "https://shiki.test/animes",
            [
                {
                    "id": 42,
                    "russian": "Тест",
                    "english": ["Test"],
                    "japanese": ["テスト"],
                    "description": "Описание",
                    "image": {"original": "/system/animes/original/42.jpg"},
                    "season": "spring_2024",
                    "status": "ongoing",
                    "genres": [{"russian": "Экшен"}],
                    "relations": [{"relation": "sequel", "anime": {"id": 43}}],
                }
            ],
        )
    }
    calls: list[tuple[str, object | None]] = []

    monkeypatch.setattr("httpx.AsyncClient", make_async_client(responses, calls))
    settings = ParserSettings()
    source = ShikimoriCatalogSource(
        settings, base_url="https://shiki.test", rate_limit_seconds=0
    )

    catalog = source.fetch_catalog()

    assert len(catalog) == 1
    anime = catalog[0]
    assert anime.title == "Тест"
    assert anime.title_ru == "Тест"
    assert anime.title_en == "Test"
    assert anime.title_original == "テスト"
    assert anime.year == 2024
    assert anime.season == "spring"
    assert anime.status == "ongoing"
    assert anime.genres == ["Экшен"]
    assert anime.poster_url == "https://shikimori.one/system/animes/original/42.jpg"
    assert anime.relations[0].relation_type == "sequel"
    assert anime.relations[0].related_source_id == "43"
    assert calls[0][0].endswith("/animes")


def test_shikimori_schedule_maps_air_datetime(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        "https://shiki.test/calendar": make_response(
            "https://shiki.test/calendar",
            [
                {
                    "anime": {"id": 7, "url": "/animes/7-test"},
                    "episode": 3,
                    "next_episode_at": "2024-02-01T12:30:00+00:00",
                }
            ],
        )
    }
    monkeypatch.setattr("httpx.AsyncClient", make_async_client(responses))
    source = ShikimoriScheduleSource(
        ParserSettings(), base_url="https://shiki.test", rate_limit_seconds=0
    )

    schedule = source.fetch_schedule()

    assert schedule[0].anime_source_id == "7"
    assert schedule[0].episode_number == 3
    assert schedule[0].air_datetime is not None
    assert schedule[0].source_url == "https://shikimori.one/animes/7-test"


def test_kodik_episode_filters_translations_and_qualities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = {
        "https://kodik.test/search": make_response(
            "https://kodik.test/search",
            {
                "results": [
                    {
                        "id": "555",
                        "translation": {
                            "id": "1",
                            "title": "AniLibria",
                            "type": "voice",
                        },
                        "translations": [
                            {"id": "1", "title": "AniLibria", "type": "voice"},
                            {"id": "2", "title": "Subs", "type": "sub"},
                        ],
                        "qualities": ["720p", "1080p"],
                        "episodes": {
                            "1": "https://kodik.test/ep1",
                            "2": "https://kodik.test/ep2",
                        },
                    }
                ]
            },
        )
    }
    monkeypatch.setattr("httpx.AsyncClient", make_async_client(responses))
    settings = ParserSettings(
        allowed_translations=["AniLibria"],
        allowed_translation_types=["voice"],
        allowed_qualities=["1080p"],
    )
    source = KodikEpisodeSource(
        settings, base_url="https://kodik.test", rate_limit_seconds=0
    )

    episodes = source.fetch_episodes()

    assert len(episodes) == 2
    assert episodes[0].anime_source_id == "555"
    assert episodes[0].translation == "AniLibria"
    assert episodes[0].quality == "1080p"
    assert [t.name for t in episodes[0].translations] == ["AniLibria"]
    assert episodes[0].qualities == ["1080p"]


def test_no_retry_on_http_status_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = make_response(
        "https://shiki.test/animes", {"detail": "fail"}, status_code=500
    )
    calls: list[tuple[str, object | None]] = []
    monkeypatch.setattr(
        "httpx.AsyncClient", make_async_client({"https://shiki.test/animes": response}, calls)
    )
    source = ShikimoriCatalogSource(
        ParserSettings(), base_url="https://shiki.test", rate_limit_seconds=0
    )

    with pytest.raises(httpx.HTTPStatusError):
        source.fetch_catalog()

    assert calls == [
        ("https://shiki.test/animes", {"page": "1", "limit": "50"})
    ]


def test_sync_service_does_not_touch_database(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_get_session():
        raise AssertionError("Database access should not occur in parser sources")

    monkeypatch.setattr("app.database.get_session", fail_get_session)
    responses = {
        "https://shiki.test/animes": make_response(
            "https://shiki.test/animes", []
        ),
        "https://shiki.test/calendar": make_response(
            "https://shiki.test/calendar", []
        ),
        "https://kodik.test/search": make_response(
            "https://kodik.test/search", {"results": []}
        ),
    }
    monkeypatch.setattr("httpx.AsyncClient", make_async_client(responses))
    catalog = ShikimoriCatalogSource(
        ParserSettings(), base_url="https://shiki.test", rate_limit_seconds=0
    )
    schedule = ShikimoriScheduleSource(
        ParserSettings(), base_url="https://shiki.test", rate_limit_seconds=0
    )
    episodes = KodikEpisodeSource(
        ParserSettings(), base_url="https://kodik.test", rate_limit_seconds=0
    )

    service = ParserSyncService(catalog, episodes, schedule)

    assert service.sync_all() == []
