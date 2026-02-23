import { Link } from 'react-router-dom';
import { splitArtistNames } from '../../utils/artistHelpers';

const ArtistLink = ({ name, className = '' }) => {
  if (!name) return null;

  const artists = splitArtistNames(name);

  if (artists.length <= 1) {
    return (
      <Link
        to={`/artists/name/${encodeURIComponent(name.trim())}`}
        className={`hover:text-primary-600 transition-colors ${className}`}
      >
        {name}
      </Link>
    );
  }

  // Rebuild the original string with clickable individual names
  let remaining = name;
  const parts = [];

  artists.forEach((artist, i) => {
    const idx = remaining.toLowerCase().indexOf(artist.toLowerCase());
    if (idx > 0) {
      parts.push(<span key={`sep-${i}`}>{remaining.substring(0, idx)}</span>);
    }
    parts.push(
      <Link
        key={`artist-${i}`}
        to={`/artists/name/${encodeURIComponent(artist)}`}
        className={`hover:text-primary-600 transition-colors ${className}`}
      >
        {artist}
      </Link>
    );
    remaining = remaining.substring(idx + artist.length);
  });

  if (remaining) {
    parts.push(<span key="trailing">{remaining}</span>);
  }

  return <>{parts}</>;
};

export default ArtistLink;
