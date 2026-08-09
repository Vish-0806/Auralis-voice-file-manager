export class SemVerValidator {
  private static readonly SEMVER_REGEX =
    /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;

  public static isValid(version: string): boolean {
    if (!version || typeof version !== 'string') {
      return false;
    }
    return this.SEMVER_REGEX.test(version.trim());
  }

  public static isValidRange(range: string): boolean {
    if (!range || typeof range !== 'string') {
      return false;
    }
    
    const trimmed = range.trim();
    if (trimmed === '*') {
      return true;
    }

    // Split by common range delimiters like whitespace or double-pipe OR
    const parts = trimmed.split(/\s+(?:or|\|\|)\s+|\s+/);
    for (const part of parts) {
      if (!part) {
        continue;
      }
      const cleanPart = part.trim();
      if (cleanPart === '*') {
        continue;
      }
      
      // Match optional operators followed by a version string
      const match = cleanPart.match(/^(\^|~|>=|<=|>|<)?(.*)$/);
      if (!match) {
        return false;
      }
      
      let versionStr = match[2];
      
      // Replace wildcards with 0 and pad to 3 parts (MAJOR.MINOR.PATCH)
      versionStr = versionStr.replace(/[xX\*]/g, '0');
      const verParts = versionStr.split('.');
      while (verParts.length < 3) {
        verParts.push('0');
      }
      const paddedVer = verParts.join('.');
      
      if (!this.isValid(paddedVer)) {
        return false;
      }
    }
    
    return true;
  }
}
