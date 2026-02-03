export function asArray<T>(value: T[] | null | undefined): T[] {
  if (Array.isArray(value)) {
    return value;
  }
  return [];
}

export function safeIncludes<T>(arr: T[] | null | undefined, value: T): boolean {
  return asArray(arr).includes(value);
}

export function getGroups(obj: { groups?: string[]; group_xmlids?: string[] } | null | undefined): string[] {
  if (!obj) {
    return [];
  }
  return asArray(obj.groups ?? obj.group_xmlids);
}
