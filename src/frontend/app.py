from __future__ import annotations

import os

import requests
import streamlit as st

API_URL = os.getenv("MUSIC_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="South Indian Music Search",
    page_icon="🎵",
    layout="wide",
)

st.title("🎵 South Indian Music Search")
st.caption(
    "Search structured South Indian film-music metadata. "
    "Credits are kept separate by source and certainty."
)


def display_artists(artists: list[str], empty_message: str) -> None:
    if artists:
        for artist in artists:
            st.write(f"• {artist}")
    else:
        st.write(empty_message)


def display_sources(sources: list[dict], button_prefix: str) -> None:
    if not sources:
        st.info("No source information available.")
        return

    for index, source in enumerate(sources):
        source_name = source.get("source_name", "Source")
        source_url = source.get("source_url")
        notes = source.get("notes")

        st.write(f"**{source_name}**")
        if source_url:
            st.link_button(
                "🔗 Open Source",
                source_url,
                key=f"{button_prefix}_{index}",
            )
        if notes:
            st.caption(notes)


st.subheader("Search")

col1, col2, col3 = st.columns(3)
with col1:
    singer = st.text_input("Singer", placeholder="e.g. Anirudh Ravichander")
with col2:
    composer = st.text_input("Composer", placeholder="e.g. Anirudh Ravichander")
with col3:
    lyricist = st.text_input("Lyricist", placeholder="e.g. Chandrabose")

col4, col5, col6 = st.columns(3)
with col4:
    title = st.text_input("Song Title", placeholder="e.g. Hangova")
with col5:
    film = st.text_input("Film", placeholder="e.g. DC")
with col6:
    language = st.text_input("Language", placeholder="e.g. Tamil")

col7, col8 = st.columns(2)
with col7:
    year_from = st.number_input(
        "From Year", min_value=1900, max_value=2100, value=None, step=1
    )
with col8:
    year_to = st.number_input(
        "To Year", min_value=1900, max_value=2100, value=None, step=1
    )

if st.button("🔍 Search Songs", type="primary"):
    params: dict[str, object] = {}
    for key, value in (
        ("singer", singer),
        ("composer", composer),
        ("lyricist", lyricist),
        ("title", title),
        ("film", film),
        ("language", language),
    ):
        if value.strip():
            params[key] = value.strip()

    if year_from is not None:
        params["year_from"] = int(year_from)
    if year_to is not None:
        params["year_to"] = int(year_to)

    if year_from is not None and year_to is not None and year_from > year_to:
        st.error("From Year cannot be greater than To Year.")
    else:
        try:
            response = requests.get(f"{API_URL}/songs", params=params, timeout=10)
            response.raise_for_status()
            st.session_state["search_results"] = response.json().get("results", [])
            st.session_state["selected_song_id"] = None
            st.session_state["search_performed"] = True
        except requests.RequestException as error:
            st.error("Could not connect to the API.")
            st.caption(str(error))

results = st.session_state.get("search_results", [])
if results:
    st.divider()
    st.subheader(f"🎵 Results ({len(results)})")
    for song in results:
        with st.container(border=True):
            result_col, button_col = st.columns([4, 1])
            with result_col:
                st.markdown(f"### {song.get('title', 'Untitled')}")
                st.write(f"🎬 **Film:** {song.get('film', 'Unknown')}")
                st.write(f"📅 **Year:** {song.get('release_year', 'Unknown')}")
                st.write(f"🌐 **Language:** {song.get('language', 'Unknown')}")
            with button_col:
                if st.button(
                    "View Details",
                    key=f"details_{song['song_id']}",
                    use_container_width=True,
                ):
                    st.session_state["selected_song_id"] = song["song_id"]
elif st.session_state.get("search_performed"):
    st.info("No songs found. Try changing or removing some filters.")

selected_song_id = st.session_state.get("selected_song_id")
if selected_song_id is not None:
    try:
        response = requests.get(
            f"{API_URL}/songs/{selected_song_id}",
            timeout=10,
        )
        response.raise_for_status()
        song = response.json()

        st.divider()
        st.subheader("🎼 Song Details")
        st.markdown(f"# {song.get('title', 'Untitled')}")
        st.write(f"**Film:** {song.get('film', 'Unknown')}")
        st.write(f"**Year:** {song.get('release_year', 'Unknown')}")
        st.write(f"**Language:** {song.get('language', 'Unknown')}")

        credits = song.get("credits", {})
        musicbrainz = credits.get("musicbrainz", {})
        verified = credits.get("verified", {})

        mb_col, verified_col = st.columns(2)
        with mb_col:
            st.markdown("### 🌐 MusicBrainz")
            st.markdown("**Credited artists (role not inferred)**")
            display_artists(
                musicbrainz.get("credited_artists", []),
                "No general artist-credit data.",
            )
            st.markdown("**🎤 Singers**")
            display_artists(musicbrainz.get("singers", []), "No singer data.")
            st.markdown("**🎼 Composers**")
            display_artists(musicbrainz.get("composers", []), "No composer data.")
            st.markdown("**✍️ Lyricists**")
            display_artists(musicbrainz.get("lyricists", []), "No lyricist data.")

        with verified_col:
            st.markdown("### ✅ Independently Verified")
            st.markdown("**🎤 Singers**")
            display_artists(verified.get("singers", []), "No verified data.")
            st.markdown("**🎼 Composers**")
            display_artists(verified.get("composers", []), "No verified data.")
            st.markdown("**✍️ Lyricists**")
            display_artists(verified.get("lyricists", []), "No verified data.")

        st.divider()
        st.markdown("### 🔗 MusicBrainz Sources")
        display_sources(song.get("sources", []), f"mb_source_{selected_song_id}")

        st.markdown("### 🔗 Artist-credit Sources")
        display_sources(
            song.get("credited_artist_sources", []),
            f"credited_source_{selected_song_id}",
        )

        st.markdown("### ✅ Verified Credit Sources")
        display_sources(
            song.get("verified_sources", []),
            f"verified_source_{selected_song_id}",
        )

    except requests.RequestException as error:
        st.error("Could not retrieve song details. Check whether the API is running.")
        st.caption(str(error))
