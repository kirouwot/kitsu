from app.player import PlaybackRequest, resolve_playback


def test_resolver_returns_mock_metadata() -> None:
    request = PlaybackRequest(
        anime_id="series-1",
        episode_id="ep-5",
        preferred_audio="ja",
        preferred_subtitle="en",
    )

    metadata = resolve_playback(request)

    assert metadata.sources and metadata.sources[0].url.endswith("series-1/ep-5")
    assert metadata.audio_tracks and metadata.audio_tracks[0].language == "ja"
    assert metadata.subtitle_tracks and metadata.subtitle_tracks[0].language == "en"
    assert metadata.intro == {"start": 0, "end": 0}
    assert metadata.outro == {"start": 0, "end": 0}
