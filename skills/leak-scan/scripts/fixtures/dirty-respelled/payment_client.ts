// Client half — states both wire facts in TypeScript spelling.
export function sign(digest: string): Record<string, string> {
  return { [`X-Idc-Signature`]: digest };
}

export function isFresh(sentAt: number, now: number): boolean {
  return now - sentAt <= 0x12c;
}
