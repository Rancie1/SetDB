/**
 * Spotify embed player component.
 * 
 * Renders a Spotify iframe embed for a given track.
 * Supports compact (52px) and full-size (152px) variants.
 */

const SpotifyEmbed = ({ spotifyTrackId, spotifyUrl, compact = true }) => {
  let trackId = spotifyTrackId;
  if (!trackId && spotifyUrl) {
    if (spotifyUrl.includes('spotify.com/track/')) {
      trackId = spotifyUrl.split('spotify.com/track/')[1]?.split('?')[0]?.split('/')[0];
    } else if (spotifyUrl.startsWith('spotify:track:')) {
      trackId = spotifyUrl.replace('spotify:track:', '');
    }
  }

  if (!trackId) return null;

  const height = compact ? 80 : 152;

  return (
    <iframe
      src={`https://open.spotify.com/embed/track/${trackId}?utm_source=generator&theme=0`}
      width="100%"
      height={height}
      frameBorder="0"
      allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
      loading="lazy"
      style={{ borderRadius: '8px', maxWidth: compact ? '320px' : '100%' }}
      title="Spotify Player"
    />
  );
};

export default SpotifyEmbed;
