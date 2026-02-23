/**
 * Split a multi-artist string into individual artist names.
 * Handles common delimiters: , / & feat. ft. x vs.
 */
export function splitArtistNames(nameString) {
  if (!nameString) return [];
  return nameString
    .split(/[,/&]|\s+(?:feat\.?|ft\.?|x|vs\.?)\s+/i)
    .map(n => n.trim())
    .filter(Boolean);
}
