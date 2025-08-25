export function encode_entity_id(provider: string, provider_id: string): string {
  return btoa(`${provider_id}@${provider}`);
}

export function decode_entity_id(encoded: string): { provider: string; provider_id: string } {
  const decoded = atob(encoded);
  const [provider_id, provider] = decoded.split('@');
  return { provider, provider_id };
}
